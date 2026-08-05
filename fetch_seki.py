"""fetch_seki.py — download and extract a SEKI edition from Bank Indonesia.

SEKI (Statistik Ekonomi dan Keuangan Indonesia) is published monthly as a single
zip of ~108 .xls tables. The parsers (parse_bop / parse_exports / parse_imports /
parse_domain1) read the loose .xls files, so this downloads and extracts them.

    python fetch_seki.py                  # newest edition available
    python fetch_seki.py --edition JUNI-2026
    python fetch_seki.py --list           # probe which editions exist, download nothing
    python fetch_seki.py --keep-zip       # don't delete the zip after extracting

GDP no longer needs this — it comes from the BPS API via fetch_gdp_bps.py. SEKI
is still required for the BoP page (tables 5.1, 5.10, 5.19) and for CPI/IHPB and
the deflator series via parse_domain1.py.

Editions are discovered by probing the URL pattern backwards from the current
month; BI publishes an edition roughly 5-6 weeks after the reference month, so
the newest one is typically 2 months back.
"""
import argparse
import datetime as dt
import os
import sys
import zipfile

import requests

SEKI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rawdata", "seki")
DOC_URL = "https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/Documents/SEKI_{ed}.zip"
PAGE_URL = "https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/Pages/SEKI-{m}-{y}.aspx"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

BULAN = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
         "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]

# Tables the parsers actually read. Everything else in the zip is extracted too
# (it is small and other scripts may want it), but these are what we verify.
REQUIRED = ["TABEL5_1.xls", "TABEL5_10.xls", "TABEL5_19.xls",
            "TABEL7_1.xls", "TABEL7_2.xls", "TABEL7_3.xls",
            "TABEL7_4.xls", "TABEL7_5.xls", "TABEL7_6.xls",
            "TABEL8_1.xls", "TABEL8_2.xls"]


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def recent_editions(n=8, today=None):
    """Most recent first: ('JUNI-2026', ...) walking backwards from this month."""
    d = today or dt.date.today()
    out = []
    y, m = d.year, d.month
    for _ in range(n):
        out.append(f"{BULAN[m - 1]}-{y}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return out


def exists(s, edition):
    """Size in bytes if the zip is real, else 0.

    BI answers HTTP 200 with an HTML soft-404 page for editions that do not
    exist, so status code alone is useless — a probe on a future month returns
    200 just like a real one. The only reliable test is the payload itself:
    a real zip starts with the PK\\x03\\x04 local-file-header magic.
    """
    url = DOC_URL.format(ed=edition.replace("-", "_"))
    month, year = edition.split("-")
    try:
        r = s.get(url, timeout=45, stream=True,
                  headers={"Range": "bytes=0-3",
                           "Referer": PAGE_URL.format(m=month, y=year)})
        try:
            if r.status_code not in (200, 206):
                return 0
            if r.raw.read(4) != b"PK\x03\x04":
                return 0                      # HTML soft-404
            # "bytes 0-3/8422521" -> total size, when the server sends it
            cr = r.headers.get("Content-Range", "")
            return int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else 1
        finally:
            r.close()
    except requests.RequestException:
        return 0


def find_latest(s, probe=8):
    for ed in recent_editions(probe):
        print(f"  probing {ed} ...", end=" ")
        got = exists(s, ed)
        if got:
            print(f"{got/1e6:.1f} MB" if got > 1 else "available")
            return ed
        print("not published")
    return None


def download(s, edition, dest_dir):
    month, year = edition.split("-")
    url = DOC_URL.format(ed=edition.replace("-", "_"))
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f"SEKI_{edition.replace('-', '_')}.zip")
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        print(f"  already downloaded: {os.path.basename(path)} "
              f"({os.path.getsize(path)/1e6:.1f} MB)")
        return path
    print(f"  downloading {url}")
    tmp = path + ".part"
    with s.get(url, timeout=300, stream=True,
               headers={"Referer": PAGE_URL.format(m=month, y=year)}) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    if pct % 20 == 0:
                        print(f"    {pct}%", end="\r")
    if not zipfile.is_zipfile(tmp):
        os.remove(tmp)
        raise SystemExit(f"downloaded file is not a zip — BI may have changed the URL:\n  {url}")
    os.replace(tmp, path)
    print(f"  saved {os.path.basename(path)} ({os.path.getsize(path)/1e6:.1f} MB)")
    return path


def extract(path, dest_dir):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        z.extractall(dest_dir)
    print(f"  extracted {len(names)} files into {dest_dir}")
    missing = [t for t in REQUIRED if not os.path.exists(os.path.join(dest_dir, t))]
    if missing:
        raise SystemExit("zip is missing tables the parsers need: " + ", ".join(missing))
    print(f"  all {len(REQUIRED)} required tables present")


def main():
    ap = argparse.ArgumentParser(description="Download and extract a SEKI edition")
    ap.add_argument("--edition", help="e.g. JUNI-2026 (default: newest available)")
    ap.add_argument("--list", action="store_true", help="probe recent editions, download nothing")
    ap.add_argument("--keep-zip", action="store_true", help="keep the zip after extracting")
    ap.add_argument("--dir", default=SEKI_DIR, help=f"target dir (default: {SEKI_DIR})")
    a = ap.parse_args()
    s = session()

    if a.list:
        print("Probing recent editions:")
        for ed in recent_editions(8):
            got = exists(s, ed)
            print(f"  {ed:<16} {f'{got/1e6:.1f} MB' if got > 1 else ('available' if got else '-')}")
        return 0

    edition = a.edition
    if edition:
        edition = edition.upper().replace("_", "-")
        if not exists(s, edition):
            raise SystemExit(f"SEKI {edition} is not downloadable — try --list")
    else:
        print("Finding newest published edition:")
        edition = find_latest(s)
        if not edition:
            raise SystemExit("no SEKI edition found in the last 8 months — check the URL pattern")
    print(f"\nSEKI {edition}")
    path = download(s, edition, a.dir)
    extract(path, a.dir)
    if not a.keep_zip:
        pass  # zips are small and useful as a fallback; keep by default
    print("\nNext: python parse_domain1.py && python parse_bop.py "
          "&& python parse_exports.py && python parse_imports.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
