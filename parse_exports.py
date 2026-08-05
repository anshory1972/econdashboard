"""parse_exports.py — extract exports by commodity from TABEL5_10.xls → clean CSV.

Sources:
  Sheet '2005-2012' : 2005-2009 data  (monthly, aggregate to quarterly)
  Sheet '2010-2024' : 2010-2026 data  (monthly, aggregate to quarterly)

Column structure (both sheets):
  Old sheet (2005-2012): row6 holds Excel date serials; row1 = label col;
    annual total cols have row6 = empty.
  New sheet (2010-2024): row4 = year (filled only in Jan col); row5 = 'Jan'..'Dec';
    blank-month cols are separators or annual totals.

Units in source: Thousands USD → output: USD million (divide by 1000).

Output: rawdata/seki/clean/exports_by_commodity.csv
  Wide format: one row per quarter (YYYY-QN), one column per commodity.
"""
import xlrd
import csv
import os

XLS = r"C:\work\economist\rawdata\seki\TABEL5_10.xls"
OUT = r"C:\work\economist\rawdata\seki\clean\exports_by_commodity.csv"

MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

QUARTER_MAP = {1: 'Q1', 2: 'Q1', 3: 'Q1',
               4: 'Q2', 5: 'Q2', 6: 'Q2',
               7: 'Q3', 8: 'Q3', 9: 'Q3',
               10: 'Q4', 11: 'Q4', 12: 'Q4'}


def safe_float(v):
    """Return float or None for empty/non-numeric cells."""
    if v == '' or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def quarter_key(year, month):
    return f'{year}-{QUARTER_MAP[month]}'


# ---------------------------------------------------------------------------
# Commodity definitions: (csv_column_name, old_row, new_row)
#   old_row: row index in sheet '2005-2012' (label in col1)
#   new_row: row index in sheet '2010-2024' (label in col2)
# ---------------------------------------------------------------------------
COMMODITIES = [
    # Grand total (fob)
    #   old sheet row 40: "Jumlah, fob"
    #   new sheet row 40: "III. Jumlah, fob (I + II)"
    ('total_fob',                           40, 40),
    # ── Agriculture ──────────────────────────────────────────────────────────
    #   old sheet row 8:  "Hasil pertanian"
    #   new sheet row 7:  "A. Hasil pertanian"
    ('agri_total',                           8,  7),
    ('agri_coffee',                          9,  8),   # Biji Kopi / Biji kopi
    ('agri_tea',                            10,  9),   # Teh
    ('agri_spices',                         11, 10),   # Rempah-rempah
    ('agri_tobacco',                        12, 11),   # Tembakau
    ('agri_cocoa',                          13, 12),   # Biji Coklat / Biji coklat
    ('agri_shrimp',                         14, 13),   # Udang
    ('agri_other',                          15, 14),   # Hasil pertanian lainnya
    # ── Manufacturing ────────────────────────────────────────────────────────
    #   old sheet row 16: "Hasil manufaktur"
    #   new sheet row 15: "B. Hasil manufaktur"
    ('manuf_total',                         16, 15),
    ('manuf_textiles',                      17, 16),   # Tekstil dan produk tekstil
    ('manuf_wood',                          18, 17),   # Produk kayu olahan
    ('manuf_palm_oil',                      19, 18),   # Minyak sawit
    ('manuf_chemicals',                     20, 19),   # Bahan kimia
    ('manuf_base_metals',                   21, 20),   # Produk logam dasar
    ('manuf_elec_equip',                    22, 21),   # Peralatan listrik
    ('manuf_cement',                        23, 22),   # Semen
    ('manuf_paper',                         24, 23),   # Kertas
    ('manuf_rubber',                        25, 24),   # Karet olahan
    ('manuf_oil_products',                  26, 25),   # Produk minyak (refined)
    ('manuf_lpg',                           27, 26),   # Gas elpiji
    ('manuf_other',                         28, 27),   # Produk manufaktur lainnya
    # ── Mining ───────────────────────────────────────────────────────────────
    #   old sheet row 29: "Hasil pertambangan dan hasil sektor lainnya"
    #   new sheet row 28: "C. Hasil pertambangan"
    ('mining_total',                        29, 28),
    ('mining_copper_ore',                   30, 29),   # Biji tembaga
    ('mining_nickel_ore',                   31, 30),   # Biji nikel
    ('mining_coal',                         32, 31),   # Batubara
    ('mining_bauxite',                      33, 32),   # Bauksit
    ('mining_crude_oil',                    34, 33),   # Minyak mentah
    ('mining_natural_gas',                  35, 34),   # Gas alam
    ('mining_lng',                          36, 35),   # Gas alam cair
    ('mining_other',                        37, 36),   # Hasil pertambangan lainnya
]


def parse_old_sheet(wb):
    """Parse '2005-2012' sheet. Returns {quarter_key: {col_name: value_usd_mn}}."""
    sh = wb.sheet_by_name('2005-2012')
    datemode = wb.datemode

    # Build column map: col_index → (year, month) using row6 date serials
    col_dates = {}
    current_year = None
    for c in range(3, sh.ncols - 4):
        yr_cell = str(sh.cell_value(5, c)).strip()  # row5 has year labels
        if yr_cell and yr_cell not in ('COMMODITIES', ''):
            try:
                current_year = int(float(yr_cell))
            except ValueError:
                pass
        date_cell = sh.cell_value(6, c)  # row6 has Excel date serials
        if isinstance(date_cell, float) and date_cell > 1000:
            try:
                dt = xlrd.xldate_as_datetime(date_cell, datemode)
                col_dates[c] = (dt.year, dt.month)
            except Exception:
                pass
        # Also handle string month headers (e.g. 'May', 'Jun' in some cols)
        elif isinstance(date_cell, str) and date_cell.strip() in MONTH_MAP:
            if current_year:
                col_dates[c] = (current_year, MONTH_MAP[date_cell.strip()])

    # Aggregate monthly → quarterly
    # {quarter_key: {col_name: [monthly_values]}}
    q_data = {}
    for c, (yr, mo) in col_dates.items():
        if yr > 2009:  # overlap: skip 2010+ here
            continue
        qk = quarter_key(yr, mo)
        if qk not in q_data:
            q_data[qk] = {name: [] for name, _, _ in COMMODITIES}
        for name, old_row, _ in COMMODITIES:
            v = sh.cell_value(old_row, c)
            fv = safe_float(v)
            if fv is not None:
                q_data[qk][name].append(fv)

    # Sum months → quarter, convert kUSD → USD mn
    result = {}
    for qk, series in q_data.items():
        result[qk] = {}
        for name in [n for n, _, _ in COMMODITIES]:
            vals = series[name]
            result[qk][name] = round(sum(vals) / 1000.0, 3) if vals else None
    return result


def parse_new_sheet(wb):
    """Parse '2010-2024' sheet. Returns {quarter_key: {col_name: value_usd_mn}}."""
    sh = wb.sheet_by_name('2010-2024')

    # Build column map: col_index → (year, month) using rows 4+5
    col_dates = {}
    current_year = None
    for c in range(3, sh.ncols - 4):
        yr_cell = str(sh.cell_value(4, c)).strip()
        if yr_cell and yr_cell not in ('', 'COMMODITIES'):
            try:
                current_year = int(float(yr_cell))
            except ValueError:
                pass
        mo_cell = str(sh.cell_value(5, c)).strip().rstrip('*').rstrip('*')
        # Strip trailing asterisks (provisional markers like 'Jan*', 'Apr**')
        mo_clean = mo_cell.rstrip('*').strip()
        if mo_clean in MONTH_MAP and current_year:
            col_dates[c] = (current_year, MONTH_MAP[mo_clean])

    # Aggregate monthly → quarterly
    q_data = {}
    for c, (yr, mo) in col_dates.items():
        qk = quarter_key(yr, mo)
        if qk not in q_data:
            q_data[qk] = {name: [] for name, _, _ in COMMODITIES}
        for name, _, new_row in COMMODITIES:
            if new_row < sh.nrows:
                v = sh.cell_value(new_row, c)
                fv = safe_float(v)
                if fv is not None:
                    q_data[qk][name].append(fv)

    # Sum months → quarter, convert kUSD → USD mn
    result = {}
    for qk, series in q_data.items():
        result[qk] = {}
        for name in [n for n, _, _ in COMMODITIES]:
            vals = series[name]
            result[qk][name] = round(sum(vals) / 1000.0, 3) if vals else None
    return result


def sort_periods(periods):
    """Sort quarterly period strings YYYY-QN."""
    def key(p):
        yr, q = p.split('-')
        return (int(yr), int(q[1]))
    return sorted(periods, key=key)


def main():
    wb = xlrd.open_workbook(XLS)

    old_data = parse_old_sheet(wb)  # 2005-2009
    new_data = parse_new_sheet(wb)  # 2010-2026

    # Merge: new_data takes precedence on overlap
    combined = {**old_data, **new_data}

    all_periods = sort_periods(combined.keys())
    col_names = [name for name, _, _ in COMMODITIES]
    headers = ['period'] + col_names

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for p in all_periods:
            row = {'period': p}
            row.update(combined[p])
            writer.writerow(row)

    print(f"Written: {OUT}")
    print(f"  Periods: {all_periods[0]} to {all_periods[-1]}  ({len(all_periods)} quarters)")
    print(f"  Commodities: {len(col_names)}")

    # Spot-check: last 4 periods, key columns
    key_cols = ['total_fob', 'mining_coal', 'manuf_palm_oil',
                'mining_crude_oil', 'mining_natural_gas']
    print(f"\nSpot-check — last 4 periods:")
    header_line = f"{'Period':<12}" + ''.join(f"{c:>18}" for c in key_cols)
    print(header_line)
    print('-' * len(header_line))
    for p in all_periods[-4:]:
        row = combined[p]
        vals = [str(row.get(c) or '') for c in key_cols]
        print(f"{p:<12}" + ''.join(f"{v:>18}" for v in vals))


if __name__ == '__main__':
    main()
