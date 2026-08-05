import xlrd

wb = xlrd.open_workbook(r"C:\work\economist\rawdata\seki\TABEL5_1.xls")
sh = wb.sheet_by_name("5.1")

print(f"Total rows: {sh.nrows}, cols: {sh.ncols}")

# Print ALL rows with their labels (col 0 = row num, col 2 = label)
print("\n--- All data rows (label + row num) ---")
for r in range(sh.nrows):
    rn  = sh.cell_value(r, 0)
    lbl = sh.cell_value(r, 2)
    if lbl or rn:
        print(f"  XLS row {r:2d} | item# {str(rn)[:4]} | {str(lbl)[:60]}")

# Find annual columns by looking at which cols between Q4 and next Q1 have values
# Year structure from row 4 + row 5
print("\n--- Year/Quarter column map ---")
year_row, qtr_row = 4, 5
ycols, qcols = {}, {}
for c in range(sh.ncols):
    v4 = sh.cell_value(year_row, c)
    v5 = sh.cell_value(qtr_row, c)
    if isinstance(v4, float) and 2000 <= v4 <= 2030:
        ycols[c] = int(v4)
    if isinstance(v5, str) and v5.strip().startswith('Q'):
        qcols[c] = v5.strip()

print("Year label columns:", ycols)
print("Quarter columns:", qcols)

# For each year, determine Q1-Q4 columns and annual column
# Strategy: Q1 of each year starts after the previous year's annual
years = sorted(set(ycols.values()))
q1_cols = sorted(c for c, q in qcols.items() if q.startswith('Q1'))
print("\nQ1 cols:", q1_cols)

# Group quarters by year by Q1 boundaries
for i, q1 in enumerate(q1_cols):
    next_q1 = q1_cols[i+1] if i+1 < len(q1_cols) else sh.ncols
    yr_qs = {c: qcols[c] for c in qcols if q1 <= c < next_q1}
    # Annual col: the column between this Q4 and next Q1 that has data in row 6
    q4_col = max(yr_qs.keys()) if yr_qs else None
    annual_col = None
    if q4_col:
        for c in range(q4_col + 1, next_q1):
            v = sh.cell_value(6, c)
            if isinstance(v, (int, float)) and v != 0.0:
                annual_col = c
                break
    # Infer year
    yr = next((ycols[c] for c in ycols if q1 <= c <= (q4_col or q1)), None)
    # also check if year label is slightly outside
    if yr is None:
        yr = next((ycols[c] for c in ycols if abs(c - q1) <= 3), None)
    print(f"  Q1@{q1}: year={yr} | Q cols={sorted(yr_qs.keys())} | annual_col={annual_col}")
