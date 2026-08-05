"""fetch_gdp_bps.py — pull quarterly GDP from the BPS WebAPI → clean CSVs.

Replaces the SEKI 7.2 / 7.4 parsing path AND the manual CEIC export for GDP.
BPS publishes on release day; SEKI carries the same quarter ~2 months later.

    python fetch_gdp_bps.py          # both tables
    python fetch_gdp_bps.py --sector
    python fetch_gdp_bps.py --exp

Outputs (schema unchanged, plus a `vervar` column that build_gdp.py ignores):
    rawdata/seki/clean/gdp_sector_constant.csv       <- var 65,   turvar 237
    rawdata/seki/clean/gdp_expenditure_constant.csv  <- var 1956, turvar 0

Series are written under the LEGACY SEKI names, mapped by numeric vervar id.
build_gdp.py matches series by exact string and *filters* unmatched ones
(sec_avail/mfg_avail), so a renamed series silently vanishes from the charts
rather than raising. Ids are stable across BPS vintages; labels are not — they
carry <b> tags, enumerator prefixes, and get re-worded. Hence id-keyed mapping
and the write-time assertions at the bottom.

API gotchas, every one of which fails SILENTLY:
  * `th` is an internal year id: 2026 -> 126 (year - 1900). Passing 2026 gives
    status:OK with an empty datacontent.
  * Max 3 years per request.
  * var 65 MUST pin turvar=237 (constant 2010). 238 is current prices and looks
    perfectly plausible while being ~83% too high.
  * The API 403s urllib's default User-Agent.
"""
import argparse
import os
import sys
import time

import pandas as pd
import requests

# ── Config ────────────────────────────────────────────────────────────────────
CLEAN = r"C:\work\economist\rawdata\seki\clean"
BASE = "https://webapi.bps.go.id/v1/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

Y0, Y1 = 2010, 2026          # Seri 2010 starts 2010-Q1
TH_OFFSET = 1900             # th id = year - 1900
QMAP = {"31": "Q1", "32": "Q2", "33": "Q3", "34": "Q4"}   # 35 = annual, excluded
QEND = {"Q1": "03-31", "Q2": "06-30", "Q3": "09-30", "Q4": "12-31"}
UNIT = "Miliar Rp (Constant 2010)"


_KEY_CACHE = None

# Where to look for the key, in order. Never hardcode it here: this repo is
# public, so a literal key would be published on the next commit.
_ENV_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    r"C:\WORK\inclgrowth\.env",   # the original location, kept as a fallback
]


def _read_env_file(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BPS_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


def api_key():
    """BPS_API_KEY from the environment, else a .env file. Resolved lazily."""
    global _KEY_CACHE
    if _KEY_CACHE:
        return _KEY_CACHE
    key = os.getenv("BPS_API_KEY")
    if not key:
        for path in _ENV_CANDIDATES:
            key = _read_env_file(path)
            if key:
                break
    if not key:
        raise SystemExit(
            "BPS_API_KEY not found.\n"
            "  Set the environment variable, or create a .env file next to this\n"
            "  script containing a single line:\n\n"
            "      BPS_API_KEY=<your key>\n\n"
            "  Get a free key by registering at https://webapi.bps.go.id/\n"
            "  Looked in: " + ", ".join(_ENV_CANDIDATES)
        )
    _KEY_CACHE = key
    return key

# ── Sector table (var 65, turvar 237) ─────────────────────────────────────────
# vervar id -> legacy SEKI series name. Quirks below are deliberate: they are
# join keys build_gdp.py matches byte-for-byte, and are never rendered.
SECTOR_17 = {
    11000: "PERTANIAN, KEHUTANAN & PERIKANAN",
    12000: "PERTAMBANGAN & PENGGALIAN",
    13000: "INDUSTRI PENGOLAHAN",
    14000: "PENGADAAN LISTRIK DAN GAS",
    15000: "PENGADAAN AIR, PENGELOLAAN SAMPAH, LIMBAH DAN DAUR ULANG",
    16000: "KONSTRUKSI",
    17000: "PERDAGANGAN BESAR DAN ECERAN, REPARASI MOBIL DAN MOTOR",
    18000: "TRANSPORTASI DAN PERGUDANGAN",
    19000: "PENYEDIAAN AKOMODASI DAN MAKAN MINUIM",      # sic: SEKI typo
    20000: "INFORMASI DAN KOMUNIKASI",
    21000: "JASA KEUANGAN DAN ASURANSI",
    22000: "REAL ESTATE",
    23000: "JASA PERUSAHAAN",
    24000: "ADMINISTRASI PEMERINTAHAN, PERTAHANAN DAN JAMINAN SOSIAL WAJIB",
    25000: "JASA PENDIDIKAN",
    26000: "JASA KESEHATAN DAN KEGIATAN LAINNYA",
    27000: "JASA LAINNYA",
}

SECTOR_AGG = {
    99001: "NILAI TAMBAH BRUTO ATAS HARGA DASAR",
    99002: "PAJAK DIKURANG SUBSIDI ATAS PRODUK",
    99003: "PRODUK DOMESTIK BRUTO",
}

# 13019 ("Industri Pengolahan Non Migas") is an INTERMEDIATE AGGREGATE.
# Including it yields 17 subsectors and double-counts against INDUSTRI PENGOLAHAN.
MFG_16 = {
    13010: "Industri Batubara dan Pengilangan Migas",
    13020: "Industri Makanan dan Minuman",
    13030: "Pengolahan Tembakau",
    13040: "Industri Tekstil dan Pakaian Jadi",
    13050: "Industri Kulit, Barang dari Kulit dan Alas Kaki",
    13060: ("Industri Kayu, Barang dari Kayu, Gabus dan Barang Anyaman dari "
            "Bambu, Rotan dan sejenisnya"),
    13070: ("Industri Kertas dan Barang dari kertas, Percetakan dan "
            "Reproduksi Media Rekaman"),
    13080: "industri Kimia, Farmasi dan Obat Tradisional",   # sic: lowercase i
    13090: "Industri Karet, Barang dari Karet dan Plastik",
    13100: "Industri Barang Galian bukan logam",
    13110: "Industri Logam Dasar",
    13120: ("Industri Barang dari Logam, Komputer, Barang Elektronik, Optik "
            "dan Peralatan Listrik"),
    13130: "Industri Mesin dan Perlengkapan",
    13140: "Industri Alat Angkutan",
    13150: "Industri Furnitur",
    13160: ("Industri Pengolahan Lainnya, Jasa Reparasi dan Pemasangan Mesin "
            "dan Peralatan"),
}

SECTOR_SUB = {
    11010: "Pertanian, Peternakan, Perburuan dan Jasa Pertanian",
    11011: "Tanaman pangan",                              # sic: lowercase p
    11012: "Tanaman Hortikultura",
    11013: "Tanaman Perkebunan",
    11014: "Peternakan",
    11015: "Jasa Pertanian dan Perburuan",
    11020: "Kehutanan dan Penebangan kayu",               # sic: lowercase k
    11030: "Perikanan",
    12010: "Pertambangan Minyak dan Gas Bumi",
    12020: "Pertambangan Batubara dan Lignit",
    12030: "Pertambangan Biji Logam,",                    # sic: trailing comma
    12040: "Pertambangan dan Penggalian Lainnya",
    14010: "Ketenagalistrikan",
    14020: "Pengadaan Gas dan Produksi Es",
    17010: "Perdagangan Mobil, Sepeda Motor dan Reparasinya",
    17020: "Pedagangan Besar dan Eceran, bukan Mobil dan Sepeda",   # sic: typo
    18010: "Angkutan Rel",
    18020: "Angkutan Darat",
    18030: "Angkutan Laut",
    18040: "Angkutan Sungai, Danau & Penyeberangan",
    18050: "Angkutan Udara",
    18060: "Pergudangan dan Jasa Penunjang Angkutan, Pos dan Kurir",
    19010: "Penyediaan Akomodasi",
    19020: "Penyediaan Makan Minum",
    21010: "Jasa Perantara Keuangan",
    21020: "Asuransi dan Dana Pensiun",
    21030: "Jasa Keuangan lainnya",                       # sic: lowercase l
    21040: "Jasa Penunjang Keuangan",
}

SECTOR_IDS = {**SECTOR_17, **SECTOR_AGG, **MFG_16, **SECTOR_SUB}

# ── Expenditure table (var 1956, turvar 0) ────────────────────────────────────
EXP_IDS = {
    100: "Rumah Tangga",
    200: "Konsumsi LNPRT",
    300: "Pemerintah",
    400: "Pembentukan Modal Tetap Domestik Bruto",
    500: "Perubahan Inventori",
    610: "Ekspor Barang",
    620: "Ekspor Jasa",
    710: "Impor Barang (-/-)",     # stored positive, same as the SEKI convention
    720: "Impor Jasa (-/-)",
    790: "Diskrepansi Statistik 1)",
    800: "Produk Domestik Bruto",
}

# The 13 series that used to require the manual CEIC export. Namespaced: bare
# 'Lainnya' / 'Mesin dan Perlengkapan' would collide, which is the same class of
# ambiguity that made GFCF the contribution denominator (build_gdp.py:35).
EXP_SUB = {
    110: "RT: Makanan dan Minuman, Selain Restoran",
    120: "RT: Pakaian, Alas Kaki dan Jasa Perawatannya",
    130: "RT: Perumahan dan Perlengkapan Rumahtangga",
    140: "RT: Kesehatan dan Pendidikan",
    150: "RT: Transportasi dan Komunikasi",
    160: "RT: Restoran dan Hotel",
    170: "RT: Lainnya",
    410: "PMTB: Bangunan",
    420: "PMTB: Mesin dan Perlengkapan",
    430: "PMTB: Kendaraan",
    440: "PMTB: Peralatan Lainnya",
    450: "PMTB: CBR",
    460: "PMTB: Produk Kekayaan Intelektual",
}

EXP_ALL = {**EXP_IDS, **EXP_SUB}


# ── Fetch ─────────────────────────────────────────────────────────────────────
def fetch_var(var_id, turvar, y0=Y0, y1=Y1):
    """Return {(vervar_id, 'YYYY-QN'): value}. 3-year request cap -> chunked."""
    out = {}
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})
    for start in range(y0, y1 + 1, 3):
        end = min(start + 2, y1)
        th = f"{start - TH_OFFSET}:{end - TH_OFFSET}" if end > start else f"{start - TH_OFFSET}"
        url = f"{BASE}/list/model/data/domain/0000/var/{var_id}/th/{th}/key/{api_key()}"
        for attempt in range(3):
            try:
                j = sess.get(url, timeout=90).json()
                break
            except Exception as e:                                   # noqa: BLE001
                if attempt == 2:
                    raise
                print(f"    retry {attempt+1} ({e})")
                time.sleep(2)
        if j.get("status") != "OK":
            raise RuntimeError(f"var {var_id} th {th}: {j.get('status')} {j.get('message')}")
        dc = j.get("datacontent") or {}
        assert dc, f"var {var_id} th {th}: empty datacontent (wrong th id?)"
        years = {x["val"]: x["label"] for x in j.get("tahun", [])}
        ids = SECTOR_IDS if var_id == 65 else EXP_ALL
        for yv, ylab in years.items():
            for qid, qlab in QMAP.items():
                for vv in ids:
                    # BUILD the key; parsing is ambiguous (turvar is variable-length
                    # and the var id can recur inside the vervar digits).
                    k = f"{vv}{var_id}{turvar}{yv}{qid}"
                    if k in dc:
                        out[(vv, f"{ylab}-{qlab}")] = float(dc[k])
        print(f"    {start}-{end}: {len(dc)} cells")
    return out


def to_long(raw, ids, table_tag):
    """Wide {(vervar, period): value} -> the long schema build_gdp.py reads."""
    rows = []
    for (vv, period), value in raw.items():
        q = period[-2:]
        rows.append({
            "table": table_tag,
            "period": period,
            "series": ids[vv],
            "value": round(value, 2),
            "unit": UNIT,
            "freq": "Q",
            "date": f"{period[:4]}-{QEND[q]}",
            "vervar": vv,
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["series", "period"]).reset_index(drop=True)


def pivot(df):
    return df.pivot_table(index="period", columns="series", values="value")


def write_atomic(df, path):
    """Never leave a truncated CSV — build_gdp.py would silently drop sectors."""
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)
    print(f"  Written: {path}  ({df['series'].nunique()} series x "
          f"{df['period'].nunique()} quarters)")


# ── Builders ──────────────────────────────────────────────────────────────────
def build_sector():
    print("[Sector] var 65, turvar 237 (Harga Konstan 2010)")
    raw = fetch_var(65, 237)
    df = to_long(raw, SECTOR_IDS, "7.2")
    p = pivot(df)

    assert len(SECTOR_17) == 17, f"expected 17 sectors, have {len(SECTOR_17)}"
    assert len(MFG_16) == 16, f"expected 16 subsectors, have {len(MFG_16)}"
    assert 13019 not in MFG_16, "13019 is an intermediate aggregate — must be excluded"

    sum17 = p[list(SECTOR_17.values())].sum(axis=1)
    ntb = p["NILAI TAMBAH BRUTO ATAS HARGA DASAR"]
    tax = p["PAJAK DIKURANG SUBSIDI ATAS PRODUK"]
    pdb = p["PRODUK DOMESTIK BRUTO"]
    assert (sum17 - ntb).abs().max() < 1.0, \
        f"17 sectors don't reconcile to NTB: max {(sum17-ntb).abs().max():.3f}"
    assert (ntb + tax - pdb).abs().max() < 1.0, \
        f"NTB + tax != PDB: max {(ntb+tax-pdb).abs().max():.3f}"

    sum16 = p[list(MFG_16.values())].sum(axis=1)
    assert (sum16 - p["INDUSTRI PENGOLAHAN"]).abs().max() < 1.0, \
        f"16 subsectors don't reconcile: max {(sum16-p['INDUSTRI PENGOLAHAN']).abs().max():.3f}"

    n_q = df["period"].nunique()
    assert n_q >= 66, f"expected >= 66 quarters, got {n_q}"
    print(f"  reconciled: 17 sectors -> NTB, +tax -> PDB, 16 subsectors -> manufacturing")
    write_atomic(df, os.path.join(CLEAN, "gdp_sector_constant.csv"))
    return df


def build_expenditure():
    print("[Expenditure] var 1956, turvar 0")
    raw = fetch_var(1956, 0)
    df = to_long(raw, EXP_ALL, "7.4")
    p = pivot(df)

    # 'Pengeluaran Konsumsi' is a SEKI aggregate with no BPS vervar; derive it so
    # the file stays a superset of what the old parser produced.
    cons = p["Rumah Tangga"] + p["Konsumsi LNPRT"] + p["Pemerintah"]
    extra = pd.DataFrame({
        "table": "7.4", "period": cons.index, "series": "Pengeluaran Konsumsi",
        "value": cons.round(2).values, "unit": UNIT, "freq": "Q",
        "date": [f"{q[:4]}-{QEND[q[-2:]]}" for q in cons.index], "vervar": -1,
    })
    df = (pd.concat([df, extra], ignore_index=True)
            .sort_values(["series", "period"]).reset_index(drop=True))
    p = pivot(df)

    resid = (p["Rumah Tangga"] + p["Konsumsi LNPRT"] + p["Pemerintah"]
             + p["Pembentukan Modal Tetap Domestik Bruto"] + p["Perubahan Inventori"]
             + p["Ekspor Barang"] + p["Ekspor Jasa"]
             - p["Impor Barang (-/-)"] - p["Impor Jasa (-/-)"]
             + p["Diskrepansi Statistik 1)"] - p["Produk Domestik Bruto"])
    assert resid.abs().max() < 2.0, \
        f"expenditure identity fails: max residual {resid.abs().max():.3f}"

    n_q = df["period"].nunique()
    assert n_q >= 66, f"expected >= 66 quarters, got {n_q}"
    print(f"  reconciled: components -> PDB (max residual {resid.abs().max():.3f})")
    write_atomic(df, os.path.join(CLEAN, "gdp_expenditure_constant.csv"))
    return df


def check_contract(sec_df, exp_df):
    """Encode build_gdp.py's expectations here, where a miss is loud."""
    have_sec = set(sec_df["series"])
    have_exp = set(exp_df["series"])
    need_sec = set(SECTOR_17.values()) | set(MFG_16.values()) | {
        "PRODUK DOMESTIK BRUTO", "INDUSTRI PENGOLAHAN"}
    need_exp = {"Rumah Tangga", "Pemerintah", "Pembentukan Modal Tetap Domestik Bruto",
                "Ekspor Barang", "Impor Barang (-/-)", "Produk Domestik Bruto"} \
        | set(EXP_SUB.values())
    assert need_sec <= have_sec, f"sector CSV missing: {sorted(need_sec - have_sec)}"
    assert need_exp <= have_exp, f"expenditure CSV missing: {sorted(need_exp - have_exp)}"
    print("  build_gdp.py contract satisfied "
          f"({len(need_sec)} sector + {len(need_exp)} expenditure series)")


def main():
    ap = argparse.ArgumentParser(description="Fetch quarterly GDP from the BPS WebAPI")
    ap.add_argument("--sector", action="store_true")
    ap.add_argument("--exp", action="store_true")
    a = ap.parse_args()
    run_all = not (a.sector or a.exp)

    sec_df = build_sector() if (run_all or a.sector) else None
    exp_df = build_expenditure() if (run_all or a.exp) else None
    if sec_df is not None and exp_df is not None:
        check_contract(sec_df, exp_df)
        latest = sorted(set(sec_df["period"]))[-1]
        pdb = pivot(sec_df)["PRODUK DOMESTIK BRUTO"]
        yoy = (pdb.iloc[-1] / pdb.iloc[-5] - 1) * 100
        qoq = (pdb.iloc[-1] / pdb.iloc[-2] - 1) * 100
        print(f"\n  {latest}: PDB {pdb.iloc[-1]:,.1f} bn  |  YoY {yoy:+.2f}%  QoQ {qoq:+.2f}%")
    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
