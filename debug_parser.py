import xlrd, re

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

wb = xlrd.open_workbook(r"C:\work\economist\rawdata\seki\TABEL7_2.xls")
sh = wb.sheet_by_name("7.2")

year_row, qtr_row = 4, 5

# Print FULL year row and quarter row — all 89 columns
print("Full year row (row 4):")
for c in range(sh.ncols):
    v = sh.cell_value(year_row, c)
    yr = as_year(v)
    if v not in ('', 0.0) or yr:
        print(f"  col {c:2d}: type={sh.cell_type(year_row,c)} raw={repr(v):<25} -> year={yr}")

print("\nFull quarter row (row 5):")
for c in range(sh.ncols):
    v = sh.cell_value(qtr_row, c)
    q = as_quarter(str(v).strip())
    if v not in ('', 0.0) or q:
        print(f"  col {c:2d}: type={sh.cell_type(qtr_row,c)} raw={repr(v):<25} -> qtr={q}")
