"""
SEKI Domain 1 Parser — Real Sector (Bab VII & VIII)
Consistent 2010 base year — only parses from 2010 onwards.
Outputs tidy long-format CSVs to rawdata/seki/clean/
"""

import xlrd
import pandas as pd
import numpy as np
import os
import re

RAW_DIR   = r"C:\work\economist\rawdata\seki"
CLEAN_DIR = r"C:\work\economist\rawdata\seki\clean"
os.makedirs(CLEAN_DIR, exist_ok=True)

MONTH_MAP = {
    'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'mei':5,
    'jun':6,'jul':7,'aug':8,'ags':8,'sep':9,'okt':10,
    'oct':10,'nov':11,'dec':12,'des':12
}

MIN_YEAR = 2010   # drop everything before this

# ── helpers ───────────────────────────────────────────────────────────────────

def clean_str(v):
    if v is None or v == '':
        return ''
    return re.sub(r'\s+', ' ', str(v)).strip()

def as_year(v):
    if isinstance(v, float) and 2000 <= v <= 2030:
        return int(v)
    if isinstance(v, str):
        m = re.match(r'^(20[012]\d)\s*$', v.strip())
        if m:
            return int(m.group(1))
    return None

def as_quarter(v):
    if isinstance(v, str):
        m = re.match(r'[Qq](\d)', v.strip())
        if m:
            return int(m.group(1))
    return None

def as_month(v):
    if isinstance(v, str):
        return MONTH_MAP.get(v.strip().lower()[:3])
    return None

def is_text_label(v):
    s = clean_str(v)
    if not s or len(s) < 2:
        return False
    if re.match(r'^[\d\.\,\-\+\s]+$', s):
        return False
    return True

def get_label(sheet, r, max_col=4):
    best = ''
    for c in range(max_col):
        v = clean_str(sheet.cell_value(r, c))
        if is_text_label(v) and len(v) > len(best):
            best = v
    return best

# ── GDP quarterly parser ───────────────────────────────────────────────────────

def parse_gdp_sheet(sheet, table_id, unit):
    nrows, ncols = sheet.nrows, sheet.ncols

    year_row = qtr_row = None
    for r in range(min(12, nrows)):
        n_years = sum(1 for c in range(ncols) if as_year(sheet.cell_value(r, c)))
        n_qtrs  = sum(1 for c in range(ncols) if as_quarter(clean_str(sheet.cell_value(r, c))))
        if n_years >= 2 and year_row is None:
            year_row = r
        if n_qtrs  >= 3 and qtr_row  is None:
            qtr_row  = r
        if year_row is not None and qtr_row is not None:
            break

    if year_row is None or qtr_row is None:
        return None

    # Build year and quarter position maps separately.
    # Then group by Q1 boundaries: each Q1 marks the start of a new year group.
    # The year label may sit at any position (Q1–Q4) within its group.
    year_cols = {}
    qtr_cols  = {}
    for c in range(ncols):
        yr = as_year(sheet.cell_value(year_row, c))
        if yr:
            year_cols[c] = yr
        q = as_quarter(clean_str(sheet.cell_value(qtr_row, c)))
        if q:
            qtr_cols[c] = q

    if not year_cols or not qtr_cols:
        return None

    # Q1 columns define group boundaries
    q1_cols = sorted(c for c, q in qtr_cols.items() if q == 1)
    col_periods = {}
    for i, q1_col in enumerate(q1_cols):
        next_q1 = q1_cols[i + 1] if i + 1 < len(q1_cols) else q1_col + 10
        # Find the year label anywhere inside this group [q1_col, next_q1)
        group_yr = next(
            (year_cols[c] for c in sorted(year_cols) if q1_col <= c < next_q1),
            None
        )
        if group_yr is None:
            continue
        for q_col, q in qtr_cols.items():
            if q1_col <= q_col < next_q1:
                col_periods[q_col] = f"{group_yr}-Q{q}"

    if not col_periods:
        return None

    records = []
    for r in range(qtr_row + 1, nrows):
        label = get_label(sheet, r)
        if not label:
            continue
        has_data = any(
            isinstance(sheet.cell_value(r, c), (int, float)) and
            sheet.cell_value(r, c) not in (0.0, '')
            for c in col_periods
        )
        if not has_data:
            continue
        for c, period in col_periods.items():
            v = sheet.cell_value(r, c)
            if isinstance(v, (int, float)) and v not in (0.0, ''):
                records.append({
                    'table': table_id, 'period': period,
                    'series': label,   'value':  float(v),
                    'unit':  unit,     'freq':   'Q'
                })

    if not records:
        return None

    df = pd.DataFrame(records)
    df['date'] = pd.PeriodIndex(df['period'], freq='Q').to_timestamp(how='end').normalize()
    return df

# ── Monthly price parser ───────────────────────────────────────────────────────

def parse_price_sheet(sheet, table_id, unit):
    nrows, ncols = sheet.nrows, sheet.ncols

    year_row = month_row = None
    for r in range(min(12, nrows)):
        n_years  = sum(1 for c in range(ncols) if as_year(sheet.cell_value(r, c)))
        n_months = sum(1 for c in range(ncols) if as_month(clean_str(sheet.cell_value(r, c))))
        if n_years  >= 2 and year_row  is None:
            year_row  = r
        if n_months >= 6 and month_row is None:
            month_row = r
        if year_row is not None and month_row is not None:
            break

    if year_row is None or month_row is None:
        return None

    year_cols  = {}
    month_cols = {}
    for c in range(ncols):
        yr = as_year(sheet.cell_value(year_row, c))
        if yr:
            year_cols[c] = yr
        m = as_month(clean_str(sheet.cell_value(month_row, c)))
        if m:
            month_cols[c] = m

    if not year_cols or not month_cols:
        return None

    # Group by January boundaries
    jan_cols = sorted(c for c, m in month_cols.items() if m == 1)
    col_periods = {}
    for i, jan_col in enumerate(jan_cols):
        next_jan = jan_cols[i + 1] if i + 1 < len(jan_cols) else jan_col + 15
        group_yr = next(
            (year_cols[c] for c in sorted(year_cols) if jan_col <= c < next_jan),
            None
        )
        if group_yr is None:
            continue
        for m_col, m in month_cols.items():
            if jan_col <= m_col < next_jan:
                col_periods[m_col] = f"{group_yr}-{m:02d}"

    if not col_periods:
        return None

    cur_category = ''
    records = []
    for r in range(month_row + 1, nrows):
        label = get_label(sheet, r)
        if not label:
            continue
        has_data = any(
            isinstance(sheet.cell_value(r, c), (int, float)) and
            sheet.cell_value(r, c) not in (0.0, '')
            for c in col_periods
        )
        if not has_data:
            cur_category = label
            continue
        series = f"{cur_category} — {label}" if cur_category and label != cur_category else label
        for c, period in col_periods.items():
            v = sheet.cell_value(r, c)
            if isinstance(v, (int, float)) and v not in (0.0, ''):
                records.append({
                    'table': table_id, 'period': period,
                    'series': series,  'value':  float(v),
                    'unit':  unit,     'freq':   'M'
                })

    if not records:
        return None

    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['period'], format='%Y-%m')
    return df

# ── stitch + filter to MIN_YEAR ────────────────────────────────────────────────

def stitch(frames, freq='Q'):
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=['table','series','period'], keep='last')
    # Filter to MIN_YEAR onwards
    if freq == 'Q':
        df = df[df['period'] >= f"{MIN_YEAR}-Q1"]
    else:
        df = df[df['period'] >= f"{MIN_YEAR}-01"]
    df = df.sort_values(['table','series','date']).reset_index(drop=True)
    return df

# ── file-level parsers ─────────────────────────────────────────────────────────

def parse_gdp_file(filename, table_id, unit, sheets_to_use):
    """Parse only the named sheets from a GDP file."""
    path = os.path.join(RAW_DIR, filename)
    wb   = xlrd.open_workbook(path)
    frames = []
    for sname in wb.sheet_names():
        if sname not in sheets_to_use:
            continue
        sh = wb.sheet_by_name(sname)
        df = parse_gdp_sheet(sh, table_id, unit)
        if df is not None and len(df) > 0:
            frames.append(df)
            print(f"  {sname:25s}: {len(df):5,} rows | "
                  f"{df['period'].nunique():3} periods | "
                  f"{df['series'].nunique():3} series")
    return stitch(frames, freq='Q')

def parse_price_file(filename, table_id, unit, sheets_to_use):
    """Parse only the named sheets from a price file."""
    path = os.path.join(RAW_DIR, filename)
    wb   = xlrd.open_workbook(path)
    frames = []
    for sname in wb.sheet_names():
        if sname not in sheets_to_use:
            continue
        sh = wb.sheet_by_name(sname)
        df = parse_price_sheet(sh, table_id, unit)
        if df is not None and len(df) > 0:
            frames.append(df)
            print(f"  {sname:25s}: {len(df):5,} rows | "
                  f"{df['period'].nunique():3} periods | "
                  f"{df['series'].nunique():3} series")
    return stitch(frames, freq='M')

# ── task definitions ───────────────────────────────────────────────────────────
#
# GDP tables: use ONLY the main sheet (e.g. '7.1') — 2010 constant prices
# Price tables: stitch 'Th 2010-2019' + latest sheet for full 2010-present coverage

TASKS = [
    # (filename,        parse_fn,          table_id, unit,                        sheets_to_use,                       out_csv)
    ('TABEL7_1.xls', parse_gdp_file,   '7.1', 'Miliar Rp (Nominal)',       ['7.1'],                             'gdp_sector_nominal.csv'),
    ('TABEL7_2.xls', parse_gdp_file,   '7.2', 'Miliar Rp (Constant 2010)', ['7.2'],                             'gdp_sector_constant.csv'),
    ('TABEL7_3.xls', parse_gdp_file,   '7.3', 'Miliar Rp (Nominal)',       ['7.3'],                             'gdp_expenditure_nominal.csv'),
    ('TABEL7_4.xls', parse_gdp_file,   '7.4', 'Miliar Rp (Constant 2010)', ['7.4'],                             'gdp_expenditure_constant.csv'),
    ('TABEL7_5.xls', parse_gdp_file,   '7.5', 'Index (2010=100)',          ['7.5'],                             'gdp_deflator_index.csv'),
    ('TABEL7_6.xls', parse_gdp_file,   '7.6', 'Percent YoY',               ['7.6'],                             'gdp_deflator_growth.csv'),
    ('TABEL8_1.xls', parse_price_file, '8.1', 'CPI Index',                 ['Th 2010-2019', '8.1'],             'cpi_monthly.csv'),
    ('TABEL8_2.xls', parse_price_file, '8.2', 'IHPB Index',                ['Th 2010-2019','Th 2020-2024','8.2'],'ihpb_monthly.csv'),
]

# ── run ────────────────────────────────────────────────────────────────────────

all_frames = []
for fname, fn, tid, unit, sheets, out_csv in TASKS:
    print(f"\n-- {fname} ({tid}) --")
    df = fn(fname, tid, unit, sheets)
    if df is None or len(df) == 0:
        print(f"  WARNING: no data extracted")
        continue
    out_path = os.path.join(CLEAN_DIR, out_csv)
    df.to_csv(out_path, index=False)
    print(f"  => {out_csv}: {len(df):,} rows | "
          f"{df['series'].nunique()} series | "
          f"{df['period'].min()} to {df['period'].max()}")
    all_frames.append(df)

# ── master panel ───────────────────────────────────────────────────────────────
if all_frames:
    master = pd.concat(all_frames, ignore_index=True)
    master_path = os.path.join(CLEAN_DIR, 'domain1_panel.csv')
    master.to_csv(master_path, index=False)
    print(f"\n{'='*60}")
    print(f"MASTER PANEL  : {len(master):,} rows")
    print(f"Tables        : {master['table'].unique().tolist()}")
    print(f"Period range  : {master['period'].min()} to {master['period'].max()}")
    print(f"Unique series : {master['series'].nunique()}")
    print(f"Saved         : {master_path}")

    print("\nSample series per table:")
    for tbl, grp in master.groupby('table'):
        samples = list(grp['series'].unique()[:3])
        print(f"  {tbl}: {samples}")

print("\nDone.")
