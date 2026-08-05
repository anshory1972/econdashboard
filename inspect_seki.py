import xlrd, os

seki_dir = r"C:\work\economist\rawdata\seki"
files = [f"TABEL7_{i}.xls" for i in range(1, 7)] + ["TABEL8_1.xls", "TABEL8_2.xls"]

for fname in files:
    path = os.path.join(seki_dir, fname)
    wb = xlrd.open_workbook(path)
    print(f"\n{'='*60}")
    print(f"FILE: {fname}  |  Sheets: {wb.sheet_names()}")
    for sh_name in wb.sheet_names():
        sh = wb.sheet_by_name(sh_name)
        print(f"\n  Sheet: '{sh_name}'  ({sh.nrows} rows x {sh.ncols} cols)")
        # Print first 12 rows to understand structure
        for r in range(min(12, sh.nrows)):
            row_vals = []
            for c in range(min(15, sh.ncols)):
                v = sh.cell_value(r, c)
                row_vals.append(str(v)[:20] if v != '' else '·')
            print(f"    R{r:02d}: {' | '.join(row_vals)}")
