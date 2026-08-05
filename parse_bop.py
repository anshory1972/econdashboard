"""parse_bop.py — extract BOP series from TABEL5_1.xls → clean CSV.
Run this once per SEKI release, before build_bop.py.
Output: rawdata/seki/clean/bop_quarterly.csv  (wide format, one row per quarter)
"""
import xlrd, csv, os

XLS   = r"C:\work\economist\rawdata\seki\TABEL5_1.xls"
OUT   = r"C:\work\economist\rawdata\seki\clean\bop_quarterly.csv"
SHEET = "5.1"

# Quarter → XLS column mapping (same as build_bop.py)
BOP_Q = [
    ('2010-Q1',3),('2010-Q2',4),('2010-Q3',5),('2010-Q4',6),
    ('2011-Q1',8),('2011-Q2',9),('2011-Q3',10),('2011-Q4',11),
    ('2012-Q1',14),('2012-Q2',15),('2012-Q3',16),('2012-Q4',17),
    ('2013-Q1',19),('2013-Q2',20),('2013-Q3',21),('2013-Q4',22),
    ('2014-Q1',24),('2014-Q2',25),('2014-Q3',26),('2014-Q4',27),
    ('2015-Q1',29),('2015-Q2',30),('2015-Q3',31),('2015-Q4',32),
    ('2016-Q1',34),('2016-Q2',35),('2016-Q3',36),('2016-Q4',37),
    ('2017-Q1',39),('2017-Q2',40),('2017-Q3',41),('2017-Q4',42),
    ('2018-Q1',44),('2018-Q2',45),('2018-Q3',46),('2018-Q4',47),
    ('2019-Q1',49),('2019-Q2',50),('2019-Q3',51),('2019-Q4',52),
    ('2020-Q1',54),('2020-Q2',55),('2020-Q3',56),('2020-Q4',57),
    ('2021-Q1',59),('2021-Q2',60),('2021-Q3',61),('2021-Q4',62),
    ('2022-Q1',64),('2022-Q2',65),('2022-Q3',66),('2022-Q4',67),
    ('2023-Q1',69),('2023-Q2',70),('2023-Q3',71),('2023-Q4',72),
    ('2024-Q1',74),('2024-Q2',75),('2024-Q3',76),('2024-Q4',77),
    ('2025-Q1',79),('2025-Q2',80),('2025-Q3',81),('2025-Q4',82),
    ('2026-Q1',84),
]

# XLS row → CSV column name
# Row numbers verified against TABEL5_1.xls sheet "5.1"
SERIES = [
    (6,  'current_account'),
    (7,  'ca_goods'),
    (22, 'ca_services'),
    (25, 'ca_primary_income'),
    (28, 'ca_secondary_income'),
    (31, 'capital_account'),
    (34, 'financial_account'),
    (37, 'fa_direct_investment'),
    (40, 'fa_portfolio'),
    (45, 'fa_derivatives'),
    (46, 'fa_other_investment'),
    (52, 'net_errors_omissions'),
    (53, 'overall_balance'),
    (54, 'reserve_assets_raw'),      # positive = drawdown (standard BOP sign)
    (59, 'reserve_position'),        # end-period level, USD mn
    (60, 'import_coverage_months'),  # BI memorandum item
]

def read_cell(sh, row, col):
    if sh.cell_type(row, col) == xlrd.XL_CELL_EMPTY:
        return None
    v = sh.cell_value(row, col)
    return round(float(v), 2) if isinstance(v, (int, float)) else None

def main():
    wb = xlrd.open_workbook(XLS)
    sh = wb.sheet_by_name(SHEET)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    headers = ['period'] + [name for _, name in SERIES]
    rows = []
    for period, col in BOP_Q:
        row_data = {'period': period}
        for xls_row, col_name in SERIES:
            row_data[col_name] = read_cell(sh, xls_row, col)
        rows.append(row_data)

    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written: {OUT}  ({len(rows)} quarters × {len(SERIES)} series)")

    # Spot-check: print last 4 quarters
    print("\nLast 4 quarters (CA, Goods, FA, Overall Balance):")
    print(f"{'Period':<12} {'CA':>10} {'Goods':>10} {'FA':>10} {'Balance':>10}")
    print("-" * 46)
    for r in rows[-4:]:
        print(f"{r['period']:<12} "
              f"{str(r['current_account'] or ''):>10} "
              f"{str(r['ca_goods'] or ''):>10} "
              f"{str(r['financial_account'] or ''):>10} "
              f"{str(r['overall_balance'] or ''):>10}")

if __name__ == "__main__":
    main()
