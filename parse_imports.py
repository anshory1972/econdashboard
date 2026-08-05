"""parse_imports.py — extract imports by economic category from TABEL5_19.xls → clean CSV.

Sources:
  Sheet '2005-2012' : 2005-2009 data  (monthly, aggregate to quarterly)
  Sheet '5.19'      : 2010-2026 data  (monthly, aggregate to quarterly)

Column structure:
  Old sheet (2005-2012): row6 holds Excel date serials; label col = col2;
    annual total cols have row6 = empty.
  New sheet (5.19): row4 = year (filled only in Jan col); row5 = 'Jan'..'Dec';
    blank-month cols are separators or annual totals.

Units in source: Thousands USD → output: USD million (divide by 1000).

Output: rawdata/seki/clean/imports_by_category.csv
  Wide format: one row per quarter (YYYY-QN), one column per category.
"""
import xlrd
import csv
import os

XLS = r"C:\work\economist\rawdata\seki\TABEL5_19.xls"
OUT = r"C:\work\economist\rawdata\seki\clean\imports_by_category.csv"

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
    if v == '' or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def quarter_key(year, month):
    return f'{year}-{QUARTER_MAP[month]}'


# ---------------------------------------------------------------------------
# Category definitions: (csv_column_name, old_row, new_row)
#   old_row: row index in sheet '2005-2012'
#   new_row: row index in sheet '5.19'
#
# Row labels (old → new):
#   row 8  → 7  : Barang konsumsi           → A. Barang konsumsi
#   row 9  → 8  : Makanan&minuman baku RT   → same
#   row 10 → 9  : Makanan&minuman olahan RT → same
#   row 11 → 10 : Mobil penumpang            → same
#   row 12 → 11 : Alat angkutan bukan industri → same
#   row 13 → 12 : Barang konsumsi tahan lama → same
#   row 14 → 13 : Barang konsumsi semi-tahan → same
#   row 15 → 14 : Barang konsumsi tidak tahan lama → same
#   row 16 → 15 : BBM olahan produk minyak (konsumsi) → same
#   row 17 → 16 : Barang tidak dirinci      → same
#   row 18 → 17 : Bahan baku & penolong     → B. Bahan baku dan bahan penolong
#   row 19 → 18 : Mak&min baku industri     → same
#   row 20 → 19 : Mak&min olahan industri   → same
#   row 21 → 20 : Bahan pasokan, baku industri → same
#   row 22 → 21 : Bahan pasokan, olahan industri → same
#   row 23 → 22 : Suku cadang barang modal  → same
#   row 24 → 23 : Suku cadang alat angkutan → same
#   row 25 → 24 : BBM baku                  → same
#   row 26 → 25 : a.l. minyak mentah        → same
#   row 27 → 26 : BBM olahan                → same
#   row 28 → 27 : a.l. produk minyak        → same
#   row 29 → 28 : a.l. gas elpiji           → same
#   row 30 → 29 : Barang modal              → C. Barang modal
#   row 31 → 30 : Barang modal (kecuali alat angkutan) → same
#   row 32 → 31 : Mobil penumpang (modal)   → same
#   row 33 → 32 : Alat angkutan lainnya industri → same
#   row 35 → 35 : Jumlah, cif               → III. Jumlah, cif (I + II)
#   row 37 → 37 : Jumlah, fob               → V. Jumlah, fob (III - IV)
# ---------------------------------------------------------------------------
CATEGORIES = [
    # Grand totals
    ('total_cif',                    35, 35),  # Jumlah, cif
    ('total_fob',                    37, 37),  # Jumlah, fob
    # ── Consumer goods ───────────────────────────────────────────────────────
    ('cons_total',                    8,  7),  # Barang konsumsi total
    ('cons_food_bev_raw',             9,  8),  # Makanan&minuman baku (RT)
    ('cons_food_bev_processed',      10,  9),  # Makanan&minuman olahan (RT)
    ('cons_passenger_cars',          11, 10),  # Mobil penumpang
    ('cons_transport_nec',           12, 11),  # Alat angkutan bukan industri
    ('cons_durable',                 13, 12),  # Barang konsumsi tahan lama
    ('cons_semidurable',             14, 13),  # Barang konsumsi semi-tahan lama
    ('cons_nondurable',              15, 14),  # Barang konsumsi tidak tahan lama
    ('cons_fuel_oil_products',       16, 15),  # BBM olahan produk minyak
    ('cons_unclassified',            17, 16),  # Barang tidak dirinci
    # ── Raw materials & intermediates ────────────────────────────────────────
    ('rawmat_total',                 18, 17),  # Bahan baku & bahan penolong
    ('rawmat_food_bev_raw',          19, 18),  # Mak&min baku industri
    ('rawmat_food_bev_processed',    20, 19),  # Mak&min olahan industri
    ('rawmat_supply_raw',            21, 20),  # Bahan pasokan, baku industri
    ('rawmat_supply_processed',      22, 21),  # Bahan pasokan, olahan industri
    ('rawmat_spares_capgoods',       23, 22),  # Suku cadang barang modal
    ('rawmat_spares_transport',      24, 23),  # Suku cadang alat angkutan
    ('rawmat_fuel_raw',              25, 24),  # BBM baku
    ('rawmat_crude_oil',             26, 25),  # a.l. minyak mentah
    ('rawmat_fuel_processed',        27, 26),  # BBM olahan
    ('rawmat_oil_products',          28, 27),  # a.l. produk minyak
    ('rawmat_lpg',                   29, 28),  # a.l. gas elpiji
    # ── Capital goods ────────────────────────────────────────────────────────
    ('capgoods_total',               30, 29),  # Barang modal
    ('capgoods_excl_transport',      31, 30),  # Barang modal (kecuali alat angkutan)
    ('capgoods_passenger_cars',      32, 31),  # Mobil penumpang (capital)
    ('capgoods_transport_other',     33, 32),  # Alat angkutan lainnya, industri
]


def parse_old_sheet(wb):
    """Parse '2005-2012' sheet; returns {quarter_key: {col_name: value_usd_mn}}."""
    sh = wb.sheet_by_name('2005-2012')
    datemode = wb.datemode

    col_dates = {}
    current_year = None
    for c in range(3, sh.ncols - 4):
        yr_cell = str(sh.cell_value(5, c)).strip()
        if yr_cell and yr_cell not in ('', 'GROUP ITEM'):
            try:
                current_year = int(float(yr_cell))
            except ValueError:
                pass
        date_cell = sh.cell_value(6, c)
        if isinstance(date_cell, float) and date_cell > 1000:
            try:
                dt = xlrd.xldate_as_datetime(date_cell, datemode)
                col_dates[c] = (dt.year, dt.month)
            except Exception:
                pass
        elif isinstance(date_cell, str) and date_cell.strip() in MONTH_MAP:
            if current_year:
                col_dates[c] = (current_year, MONTH_MAP[date_cell.strip()])

    q_data = {}
    for c, (yr, mo) in col_dates.items():
        if yr > 2009:
            continue
        qk = quarter_key(yr, mo)
        if qk not in q_data:
            q_data[qk] = {name: [] for name, _, _ in CATEGORIES}
        for name, old_row, _ in CATEGORIES:
            if old_row < sh.nrows:
                v = sh.cell_value(old_row, c)
                fv = safe_float(v)
                if fv is not None:
                    q_data[qk][name].append(fv)

    result = {}
    for qk, series in q_data.items():
        result[qk] = {}
        for name in [n for n, _, _ in CATEGORIES]:
            vals = series[name]
            result[qk][name] = round(sum(vals) / 1000.0, 3) if vals else None
    return result


def parse_new_sheet(wb):
    """Parse '5.19' sheet; returns {quarter_key: {col_name: value_usd_mn}}."""
    sh = wb.sheet_by_name('5.19')

    col_dates = {}
    current_year = None
    for c in range(3, sh.ncols - 4):
        yr_cell = str(sh.cell_value(4, c)).strip()
        if yr_cell and yr_cell not in ('', 'GROUP ITEM'):
            try:
                current_year = int(float(yr_cell))
            except ValueError:
                pass
        mo_cell = str(sh.cell_value(5, c)).strip().rstrip('*')
        if mo_cell in MONTH_MAP and current_year:
            col_dates[c] = (current_year, MONTH_MAP[mo_cell])

    q_data = {}
    for c, (yr, mo) in col_dates.items():
        qk = quarter_key(yr, mo)
        if qk not in q_data:
            q_data[qk] = {name: [] for name, _, _ in CATEGORIES}
        for name, _, new_row in CATEGORIES:
            if new_row < sh.nrows:
                v = sh.cell_value(new_row, c)
                fv = safe_float(v)
                if fv is not None:
                    q_data[qk][name].append(fv)

    result = {}
    for qk, series in q_data.items():
        result[qk] = {}
        for name in [n for n, _, _ in CATEGORIES]:
            vals = series[name]
            result[qk][name] = round(sum(vals) / 1000.0, 3) if vals else None
    return result


def sort_periods(periods):
    def key(p):
        yr, q = p.split('-')
        return (int(yr), int(q[1]))
    return sorted(periods, key=key)


def main():
    wb = xlrd.open_workbook(XLS)

    old_data = parse_old_sheet(wb)   # 2005-2009
    new_data = parse_new_sheet(wb)   # 2010-2026

    # Merge — new_data takes precedence on any overlap
    combined = {**old_data, **new_data}

    all_periods = sort_periods(combined.keys())
    col_names = [name for name, _, _ in CATEGORIES]
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
    print(f"  Categories: {len(col_names)}")

    # Spot-check: last 4 periods, key columns
    key_cols = ['total_cif', 'cons_total', 'rawmat_total',
                'capgoods_total', 'rawmat_crude_oil']
    print(f"\nSpot-check — last 4 periods:")
    hdr = f"{'Period':<12}" + ''.join(f"{c:>18}" for c in key_cols)
    print(hdr)
    print('-' * len(hdr))
    for p in all_periods[-4:]:
        row = combined[p]
        vals = [str(row.get(c) or '') for c in key_cols]
        print(f"{p:<12}" + ''.join(f"{v:>18}" for v in vals))


if __name__ == '__main__':
    main()
