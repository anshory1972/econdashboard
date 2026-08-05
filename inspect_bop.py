import xlrd

wb = xlrd.open_workbook(r"C:\work\economist\rawdata\seki\TABEL5_1.xls")
print("Sheets:", wb.sheet_names())
sh = wb.sheet_by_name("5.1")
print(f"\nSheet '5.1': {sh.nrows} rows x {sh.ncols} cols")
print("\n--- First 30 rows (cols 0-20) ---")
for r in range(min(30, sh.nrows)):
    row_vals = []
    for c in range(min(21, sh.ncols)):
        v = sh.cell_value(r, c)
        row_vals.append(str(v)[:18] if v != '' else '.')
    print(f"R{r:02d}: {' | '.join(row_vals)}")

print("\n--- Full column count check (row 5-8) ---")
for r in range(4, 10):
    print(f"\nR{r:02d} all cols ({sh.ncols} total):")
    for c in range(sh.ncols):
        v = sh.cell_value(r, c)
        if v != '' and v != 0.0:
            print(f"  col{c:3d}: {repr(v)[:40]}")
