"""
Build econdashboard.html — GDP YoY quarterly growth
All 17 sectors · Analytical window toggle (2Y / 4Y / All)
Commentary: last quarter only, 8Q as benchmark
"""
import pandas as pd
import numpy as np
import json, os

CLEAN = r"C:\work\economist\rawdata\seki\clean"
HTML  = r"C:\work\economist\html"
os.makedirs(HTML, exist_ok=True)

# ── 1. Load ────────────────────────────────────────────────────────────────────

sec = pd.read_csv(os.path.join(CLEAN, "gdp_sector_constant.csv"))
exp = pd.read_csv(os.path.join(CLEAN, "gdp_expenditure_constant.csv"))

# ── 2. Headline GDP YoY ────────────────────────────────────────────────────────

gdp = (sec[sec['series'] == 'PRODUK DOMESTIK BRUTO']
       .sort_values('period').reset_index(drop=True))
gdp['yoy'] = gdp['value'].pct_change(4) * 100
gdp = gdp.dropna(subset=['yoy'])
gdp = gdp[gdp['period'] >= '2015-Q1'].reset_index(drop=True)

periods       = gdp['period'].tolist()
yoy_vals      = [round(v, 2) for v in gdp['yoy'].tolist()]
precovid      = gdp[(gdp['period'] >= '2015-Q1') & (gdp['period'] <= '2019-Q4')]
precovid_mean = round(precovid['yoy'].mean(), 2)
latest_period = gdp['period'].iloc[-1]
latest_yoy    = round(gdp['yoy'].iloc[-1], 2)
prev_yoy      = round(gdp['yoy'].iloc[-2], 2)
delta         = round(latest_yoy - prev_yoy, 2)

# ── 3. Demand: growth & contributions ─────────────────────────────────────────

EXP_MAP = {
    'Rumah Tangga':                           'Household Consumption',
    'Pemerintah':                             'Government',
    'Pembentukan Modal Tetap Domestik Bruto': 'Investment (PMTB)',
    'Ekspor Barang':                          'Exports (Goods)',
    'Impor Barang (-/-)':                     'Imports (Goods)',
}
exp_components = {k: v for k, v in EXP_MAP.items() if k in exp['series'].unique()}
gdp_total_name_exp = next(s for s in exp['series'].unique() if 'domestik bruto' in s.lower())
gdp_total_exp = exp[exp['series'] == gdp_total_name_exp].sort_values('period').set_index('period')['value']

exp_growth_records, exp_contrib_records = [], []
# Add GDP total as reference (pinned at top in snapshot; also visible in time series)
for p, v in zip(periods, yoy_vals):
    exp_growth_records.append({'period': p, 'component': 'GDP', 'yoy': round(v, 2)})
for raw, label in exp_components.items():
    comp     = exp[exp['series'] == raw].sort_values('period').set_index('period')['value']
    yoy_comp = (comp.pct_change(4) * 100).dropna()
    for p, v in yoy_comp.items():
        if p >= '2015-Q1':
            exp_growth_records.append({'period': p, 'component': label, 'yoy': round(v, 2)})
    sign = -1 if label == 'Imports (Goods)' else 1
    contrib = ((comp - comp.shift(4)) / gdp_total_exp.shift(4) * 100).dropna()
    for p, v in contrib.items():
        if p >= '2015-Q1':
            exp_contrib_records.append({'period': p, 'component': label, 'contribution': round(v * sign, 3)})

exp_growth = pd.DataFrame(exp_growth_records)
exp_contrib = pd.DataFrame(exp_contrib_records)

# ── 4. Sectors: growth & contributions (all 17) ───────────────────────────────

SEC_MAP = {
    'PERTANIAN, KEHUTANAN & PERIKANAN':                              'Agriculture',
    'PERTAMBANGAN & PENGGALIAN':                                     'Mining & Quarrying',
    'INDUSTRI PENGOLAHAN':                                           'Manufacturing',
    'PENGADAAN LISTRIK DAN GAS':                                     'Electricity & Gas',
    'PENGADAAN AIR, PENGELOLAAN SAMPAH, LIMBAH DAN DAUR ULANG':     'Water & Waste',
    'KONSTRUKSI':                                                    'Construction',
    'PERDAGANGAN BESAR DAN ECERAN, REPARASI MOBIL DAN MOTOR':       'Trade',
    'TRANSPORTASI DAN PERGUDANGAN':                                  'Transport & Storage',
    'PENYEDIAAN AKOMODASI DAN MAKAN MINUIM':                        'Accommodation & Food',
    'INFORMASI DAN KOMUNIKASI':                                      'Info & Comms',
    'JASA KEUANGAN DAN ASURANSI':                                    'Finance & Insurance',
    'REAL ESTATE':                                                   'Real Estate',
    'JASA PERUSAHAAN':                                               'Business Services',
    'ADMINISTRASI PEMERINTAHAN, PERTAHANAN DAN JAMINAN SOSIAL WAJIB': 'Government Admin',
    'JASA PENDIDIKAN':                                               'Education',
    'JASA KESEHATAN DAN KEGIATAN LAINNYA':                          'Health & Social',
    'JASA LAINNYA':                                                  'Other Services',
}
sec_avail = {k: v for k, v in SEC_MAP.items() if k in sec['series'].unique()}
gdp_total_sec = sec[sec['series'] == 'PRODUK DOMESTIK BRUTO'].sort_values('period').set_index('period')['value']

sec_growth_records, sec_contrib_records = [], []
for raw, label in sec_avail.items():
    comp     = sec[sec['series'] == raw].sort_values('period').set_index('period')['value']
    yoy_comp = (comp.pct_change(4) * 100).dropna()
    for p, v in yoy_comp.items():
        if p >= '2015-Q1':
            sec_growth_records.append({'period': p, 'sector': label, 'yoy': round(v, 2)})
    contrib = ((comp - comp.shift(4)) / gdp_total_sec.shift(4) * 100).dropna()
    for p, v in contrib.items():
        if p >= '2015-Q1':
            sec_contrib_records.append({'period': p, 'sector': label, 'contribution': round(v, 3)})

sec_growth = pd.DataFrame(sec_growth_records)
sec_contrib = pd.DataFrame(sec_contrib_records)

# ── 4b. Manufacturing subsectors ──────────────────────────────────────────────

MFG_MAP = {
    'Industri Makanan dan Minuman':                                                        'Food & Beverages',
    'Pengolahan Tembakau':                                                                 'Tobacco',
    'Industri Tekstil dan Pakaian Jadi':                                                   'Textiles & Apparel',
    'Industri Kulit, Barang dari Kulit dan Alas Kaki':                                     'Leather & Footwear',
    'Industri Kayu, Barang dari Kayu, Gabus dan Barang Anyaman dari Bambu, Rotan dan sejenisnya': 'Wood Products',
    'Industri Kertas dan Barang dari kertas, Percetakan dan Reproduksi Media Rekaman':     'Paper & Printing',
    'Industri Batubara dan Pengilangan Migas':                                             'Coal & Oil Refining',
    'industri Kimia, Farmasi dan Obat Tradisional':                                        'Chemicals & Pharma',
    'Industri Karet, Barang dari Karet dan Plastik':                                       'Rubber & Plastics',
    'Industri Barang Galian bukan logam':                                                  'Non-metallic Minerals',
    'Industri Logam Dasar':                                                                'Basic Metals',
    'Industri Barang dari Logam, Komputer, Barang Elektronik, Optik dan Peralatan Listrik': 'Metal Products & Electronics',
    'Industri Mesin dan Perlengkapan':                                                     'Machinery',
    'Industri Alat Angkutan':                                                              'Transport Equipment',
    'Industri Furnitur':                                                                   'Furniture',
    'Industri Pengolahan Lainnya, Jasa Reparasi dan Pemasangan Mesin dan Peralatan':       'Other Manufacturing',
}
mfg_avail = {k: v for k, v in MFG_MAP.items() if k in sec['series'].unique()}

# Use manufacturing aggregate as the denominator for contributions
mfg_total = sec[sec['series'] == 'INDUSTRI PENGOLAHAN'].sort_values('period').set_index('period')['value']

mfg_growth_records, mfg_contrib_records = [], []
for raw, label in mfg_avail.items():
    comp     = sec[sec['series'] == raw].sort_values('period').set_index('period')['value']
    yoy_comp = (comp.pct_change(4) * 100).dropna()
    for p, v in yoy_comp.items():
        if p >= '2015-Q1':
            mfg_growth_records.append({'period': p, 'subsector': label, 'yoy': round(v, 2)})
    contrib = ((comp - comp.shift(4)) / mfg_total.shift(4) * 100).dropna()
    for p, v in contrib.items():
        if p >= '2015-Q1':
            mfg_contrib_records.append({'period': p, 'subsector': label, 'contribution': round(v, 3)})

mfg_growth = pd.DataFrame(mfg_growth_records)
mfg_contrib = pd.DataFrame(mfg_contrib_records)

# Manufacturing aggregate YoY (for commentary reference)
# ── 4c. CEIC: Household consumption & GFCF sub-components ─────────────────────

ceic_raw = pd.read_csv(r'C:\work\economist\rawdata\ceic\ceic_gdp_exp.csv')

# Keep only data rows (MM/YYYY format)
is_data = ceic_raw.iloc[:, 0].astype(str).str.match(r'^\d{2}/\d{4}$')
ceic = ceic_raw[is_data].copy()

# Parse MM/YYYY → YYYY-Qq
_qmap = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
ceic['period'] = ceic.iloc[:, 0].apply(lambda d: f"{d[3:]}-{_qmap[d[:2]]}")
ceic = ceic[ceic['period'] >= '2015-Q1'].reset_index(drop=True)

# Strip long prefix from column names
_pfx = 'Gross Domestic Product: SNA 2008: 2010p: '
ceic = ceic.rename(columns={c: c.replace(_pfx, '') for c in ceic.columns})
ceic = ceic.set_index('period')

# Convert all value columns to numeric
for col in ceic.columns:
    if col != 'Unnamed: 0':
        ceic[col] = pd.to_numeric(ceic[col], errors='coerce')

# ── Household consumption sub-components ──
HH_TOTAL = 'Consumption Expenditure: Household'
HH_MAP = {
    'Consumption Expenditure: Household: Food & Beverages, Other than Restaurant': 'Food & Beverages',
    'Consumption Expenditure: Household: Apparel, Footwear & Maintenance Services': 'Apparel & Footwear',
    'Consumption Expenditure: Household: Equipments':                               'Household Equipment',
    'Consumption Expenditure: Household: Health & Education':                       'Health & Education',
    'Consumption Expenditure: Household: Transportation & Communication':            'Transport & Comms',
    'Consumption Expenditure: Household: Restaurant & Hotel':                       'Restaurant & Hotel',
    'Consumption Expenditure: Household: Others':                                   'Other Consumption',
}
hh_total = ceic[HH_TOTAL]

hh_growth_records, hh_contrib_records = [], []
# Include total in growth chart for SEKI consistency check
for p, v in (hh_total.pct_change(4) * 100).dropna().items():
    hh_growth_records.append({'period': p, 'component': 'Household Total', 'yoy': round(v, 2)})
for raw, label in HH_MAP.items():
    comp = ceic[raw]
    for p, v in (comp.pct_change(4) * 100).dropna().items():
        hh_growth_records.append({'period': p, 'component': label, 'yoy': round(v, 2)})
    for p, v in ((comp - comp.shift(4)) / hh_total.shift(4) * 100).dropna().items():
        hh_contrib_records.append({'period': p, 'component': label, 'contribution': round(v, 3)})
hh_growth = pd.DataFrame(hh_growth_records)
hh_contrib = pd.DataFrame(hh_contrib_records)

# ── GFCF sub-components ──
GFCF_TOTAL = 'Gross Fixed Capital Formation'
GFCF_MAP = {
    'GFCF: Buildings & Structures':         'Buildings & Structures',
    'GFCF: Machine & Equipment':            'Machine & Equipment',
    'GFCF: Vehicles':                       'Vehicles',
    'GFCF: Other Equipments':               'Other Equipment',
    'GFCF: Cultivated Biological Resources':'Biological Resources',
    'GFCF: Intellectual Property Products': 'Intellectual Property',
}
gfcf_total = ceic[GFCF_TOTAL]

gfcf_growth_records, gfcf_contrib_records = [], []
for p, v in (gfcf_total.pct_change(4) * 100).dropna().items():
    gfcf_growth_records.append({'period': p, 'component': 'GFCF Total', 'yoy': round(v, 2)})
for raw, label in GFCF_MAP.items():
    comp = ceic[raw]
    for p, v in (comp.pct_change(4) * 100).dropna().items():
        gfcf_growth_records.append({'period': p, 'component': label, 'yoy': round(v, 2)})
    for p, v in ((comp - comp.shift(4)) / gfcf_total.shift(4) * 100).dropna().items():
        gfcf_contrib_records.append({'period': p, 'component': label, 'contribution': round(v, 3)})

hh_yoy_series   = (hh_total.pct_change(4)   * 100).dropna()
gfcf_yoy_series = (gfcf_total.pct_change(4) * 100).dropna()
gfcf_growth = pd.DataFrame(gfcf_growth_records)
gfcf_contrib = pd.DataFrame(gfcf_contrib_records)
mfg_yoy_series = (mfg_total.pct_change(4) * 100).dropna()

# ── 5. Auto-generate commentaries (last quarter; 8Q avg as benchmark) ─────────

def bold(x, suffix='%', decimals=2, sign=False):
    fmt = f'{x:+.{decimals}f}' if sign else f'{x:.{decimals}f}'
    return f'<strong>{fmt}{suffix}</strong>'

def hi(text):
    return f'<em>{text}</em>'

def vs_avg(v, avg, unit='%'):
    diff   = v - avg
    direct = 'above' if diff >= 0 else 'below'
    return f'{direct} its 8Q avg ({bold(avg, unit)}) by <strong>{abs(diff):.2f}{unit}</strong>'

# Shared anchors
g8      = gdp.tail(8)
q       = g8.iloc[-1]['period']       # latest quarter label
g_now   = g8.iloc[-1]['yoy']          # latest GDP YoY
g_prev  = g8.iloc[-2]['yoy']          # prior quarter GDP YoY
g_avg8  = g8['yoy'].mean()            # 8Q average
g_swing = g_now - g_prev

# ── GDP ──
gdp_comment = (
    f"<p>GDP grew {bold(g_now)} YoY in {hi(q)}, "
    f"{'up' if g_swing >= 0 else 'down'} {bold(abs(g_swing), sign=False)} pp "
    f"from {bold(g_prev)} in the prior quarter.</p>"
    f"<p>The latest reading is {vs_avg(g_now, g_avg8)}, "
    f"and {bold(g_now - precovid_mean, '%', sign=True)} relative to "
    f"the 2015–2019 pre-COVID mean of {bold(precovid_mean)}.</p>"
)

# ── Demand: growth ──
eg8      = exp_growth[exp_growth['period'].isin(g8['period'].tolist())]
eg_avg   = eg8.groupby('component')['yoy'].mean()
eg_q     = eg8[eg8['period'] == q].set_index('component')['yoy'].sort_values(ascending=False)
eg_neg   = [c for c in eg_q.index if eg_q[c] < 0]

rows = [
    f"<p>· {hi(c)}: {bold(v)} — {vs_avg(v, float(eg_avg.get(c, 0)))}</p>"
    for c, v in eg_q.items()
]
exp_growth_comment = (
    f"<p>Demand growth in {hi(q)}:</p>"
    + "".join(rows)
    + (f"<p>{hi(', '.join(eg_neg))} contracted this quarter.</p>" if eg_neg else "")
)

# ── Demand: contributions ──
ec8    = exp_contrib[exp_contrib['period'].isin(g8['period'].tolist())]
ec_avg = ec8.groupby('component')['contribution'].mean()
ec_q   = ec8[ec8['period'] == q].set_index('component')['contribution'].sort_values(ascending=False)
ec_neg = [c for c in ec_q.index if ec_q[c] < 0]

rows_c = [
    f"<p>· {hi(c)}: {bold(v, ' pp', sign=True)} — {vs_avg(v, float(ec_avg.get(c, 0)), ' pp')}</p>"
    for c, v in ec_q.items()
]
exp_contrib_comment = (
    f"<p>Contributions to {bold(g_now)} GDP growth in {hi(q)}:</p>"
    + "".join(rows_c)
    + (f"<p>Drag: {hi(', '.join(ec_neg))}.</p>" if ec_neg else "")
)

# ── Sectors: growth ──
sg8      = sec_growth[sec_growth['period'].isin(g8['period'].tolist())]
sg_avg   = sg8.groupby('sector')['yoy'].mean()
sg_q     = sg8[sg8['period'] == q].set_index('sector')['yoy'].sort_values(ascending=False)
sg_neg   = [s for s in sg_q.index if sg_q[s] < 0]
sg_top3  = sg_q.head(3)
sg_bot3  = sg_q.tail(3)

top_rows = [
    f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(sg_avg.get(s, 0)))}</p>"
    for s, v in sg_top3.items()
]
bot_rows = [
    f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(sg_avg.get(s, 0)))}</p>"
    for s, v in sg_bot3.items()
]
sec_growth_comment = (
    f"<p><strong>Top 3 sectors</strong> in {hi(q)}:</p>"
    + "".join(top_rows)
    + f"<p><strong>Bottom 3:</strong></p>"
    + "".join(bot_rows)
    + (f"<p>In contraction: {hi(', '.join(sg_neg))}.</p>" if sg_neg else "")
)

# ── Sectors: contributions ──
sc8      = sec_contrib[sec_contrib['period'].isin(g8['period'].tolist())]
sc_avg   = sc8.groupby('sector')['contribution'].mean()
sc_q     = sc8[sc8['period'] == q].set_index('sector')['contribution'].sort_values(ascending=False)
sc_neg   = [s for s in sc_q.index if sc_q[s] < 0]
sc_top3  = sc_q.head(3)

top_c_rows = [
    f"<p>· {hi(s)}: {bold(v, ' pp', sign=True)} — {vs_avg(v, float(sc_avg.get(s, 0)), ' pp')}</p>"
    for s, v in sc_top3.items()
]
sec_contrib_comment = (
    f"<p><strong>Top 3 contributors</strong> in {hi(q)}:</p>"
    + "".join(top_c_rows)
    + (f"<p>Drag: {hi(', '.join(sc_neg))}.</p>" if sc_neg else "")
)

# ── Manufacturing subsector commentary ──
mg8      = mfg_growth[mfg_growth['period'].isin(g8['period'].tolist())]
mg_avg   = mg8.groupby('subsector')['yoy'].mean()
mg_q     = mg8[mg8['period'] == q].set_index('subsector')['yoy'].sort_values(ascending=False)
mg_neg   = [s for s in mg_q.index if mg_q[s] < 0]
mg_top3  = mg_q.head(3)
mg_bot3  = mg_q.tail(3)

mc8      = mfg_contrib[mfg_contrib['period'].isin(g8['period'].tolist())]
mc_avg   = mc8.groupby('subsector')['contribution'].mean()
mc_q     = mc8[mc8['period'] == q].set_index('subsector')['contribution'].sort_values(ascending=False)
mc_neg   = [s for s in mc_q.index if mc_q[s] < 0]
mc_top3  = mc_q.head(3)

mfg_now  = round(float(mfg_yoy_series.get(q, 0)), 2)
mfg_prev = round(float(mfg_yoy_series.get(g8.iloc[-2]['period'], 0)), 2)

top_mg_rows = [
    f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(mg_avg.get(s, 0)))}</p>"
    for s, v in mg_top3.items()
]
bot_mg_rows = [
    f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(mg_avg.get(s, 0)))}</p>"
    for s, v in mg_bot3.items()
]
top_mc_rows = [
    f"<p>· {hi(s)}: {bold(v, ' pp', sign=True)} — {vs_avg(v, float(mc_avg.get(s, 0)), ' pp')}</p>"
    for s, v in mc_top3.items()
]

mfg_growth_comment = (
    f"<p>Manufacturing grew {bold(mfg_now)} in {hi(q)} "
    f"({'up' if mfg_now >= mfg_prev else 'down'} from {bold(mfg_prev)} prior quarter).</p>"
    f"<p><strong>Top 3 subsectors:</strong></p>"
    + "".join(top_mg_rows)
    + f"<p><strong>Bottom 3:</strong></p>"
    + "".join(bot_mg_rows)
    + (f"<p>Contracting: {hi(', '.join(mg_neg))}.</p>" if mg_neg else "")
)

mfg_contrib_comment = (
    f"<p>Contributions to manufacturing growth in {hi(q)}:</p>"
    + "".join(top_mc_rows)
    + (f"<p>Drag: {hi(', '.join(mc_neg))}.</p>" if mc_neg else "")
)

# ── Household consumption commentary ──
hh8      = hh_growth[hh_growth['period'].isin(g8['period'].tolist()) & (hh_growth['component'] != 'Household Total')]
hh_avg   = hh8.groupby('component')['yoy'].mean()
hh_q     = hh8[hh8['period'] == q].set_index('component')['yoy'].sort_values(ascending=False)
hh_neg   = [c for c in hh_q.index if hh_q[c] < 0]
hh_now   = round(float(hh_yoy_series.get(q, 0)), 2)
hh_prev  = round(float(hh_yoy_series.get(g8.iloc[-2]['period'], 0)), 2)

hc8     = hh_contrib[hh_contrib['period'].isin(g8['period'].tolist())]
hc_avg  = hc8.groupby('component')['contribution'].mean()
hc_q    = hc8[hc8['period'] == q].set_index('component')['contribution'].sort_values(ascending=False)
hc_neg  = [c for c in hc_q.index if hc_q[c] < 0]

hh_growth_comment = (
    f"<p>Household consumption grew {bold(hh_now)} in {hi(q)} "
    f"({'up' if hh_now >= hh_prev else 'down'} from {bold(hh_prev)} prior quarter).</p>"
    f"<p><strong>Top components:</strong></p>"
    + "".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(hh_avg.get(s,0)))}</p>"
              for s, v in hh_q.head(3).items())
    + (f"<p>Contracting: {hi(', '.join(hh_neg))}.</p>" if hh_neg else "")
)

hh_contrib_comment = (
    f"<p>Contributions to household consumption growth in {hi(q)}:</p>"
    + "".join(f"<p>· {hi(s)}: {bold(v, ' pp', sign=True)} — {vs_avg(v, float(hc_avg.get(s,0)), ' pp')}</p>"
              for s, v in hc_q.head(3).items())
    + (f"<p>Drag: {hi(', '.join(hc_neg))}.</p>" if hc_neg else "")
)

# ── GFCF commentary ──
gf8      = gfcf_growth[gfcf_growth['period'].isin(g8['period'].tolist()) & (gfcf_growth['component'] != 'GFCF Total')]
gf_avg   = gf8.groupby('component')['yoy'].mean()
gf_q     = gf8[gf8['period'] == q].set_index('component')['yoy'].sort_values(ascending=False)
gf_neg   = [c for c in gf_q.index if gf_q[c] < 0]
gf_now   = round(float(gfcf_yoy_series.get(q, 0)), 2)
gf_prev  = round(float(gfcf_yoy_series.get(g8.iloc[-2]['period'], 0)), 2)

gc8     = gfcf_contrib[gfcf_contrib['period'].isin(g8['period'].tolist())]
gc_avg  = gc8.groupby('component')['contribution'].mean()
gc_q    = gc8[gc8['period'] == q].set_index('component')['contribution'].sort_values(ascending=False)
gc_neg  = [c for c in gc_q.index if gc_q[c] < 0]

gfcf_growth_comment = (
    f"<p>GFCF grew {bold(gf_now)} in {hi(q)} "
    f"({'up' if gf_now >= gf_prev else 'down'} from {bold(gf_prev)} prior quarter).</p>"
    f"<p><strong>Top components:</strong></p>"
    + "".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v, float(gf_avg.get(s,0)))}</p>"
              for s, v in gf_q.head(3).items())
    + (f"<p>Contracting: {hi(', '.join(gf_neg))}.</p>" if gf_neg else "")
)

gfcf_contrib_comment = (
    f"<p>Contributions to GFCF growth in {hi(q)}:</p>"
    + "".join(f"<p>· {hi(s)}: {bold(v, ' pp', sign=True)} — {vs_avg(v, float(gc_avg.get(s,0)), ' pp')}</p>"
              for s, v in gc_q.head(3).items())
    + (f"<p>Drag: {hi(', '.join(gc_neg))}.</p>" if gc_neg else "")
)

commentaries = {
    'gdp':        gdp_comment,
    'expGrowth':  exp_growth_comment,
    'expContrib': exp_contrib_comment,
    'hhGrowth':   hh_growth_comment,
    'hhContrib':  hh_contrib_comment,
    'gfcfGrowth': gfcf_growth_comment,
    'gfcfContrib':gfcf_contrib_comment,
    'secGrowth':  sec_growth_comment,
    'secContrib': sec_contrib_comment,
    'mfgGrowth':  mfg_growth_comment,
    'mfgContrib': mfg_contrib_comment,
}

# ── 5b. Snapshot commentaries (Tab 2 — latest quarter grouped view) ───────────

def snap_cmt_overview():
    top2 = ec_q.head(2)
    drag = [c for c in ec_q.index if ec_q[c] < 0]
    lines = (
        f"<p>GDP grew {bold(g_now)} YoY in {hi(q)}, "
        f"{'up' if g_swing >= 0 else 'down'} {bold(abs(g_swing), sign=False)} pp "
        f"from the prior quarter and {vs_avg(g_now, g_avg8)}.</p>"
        f"<p><strong>Main demand drivers:</strong> "
        + ", ".join(f"{hi(c)} ({bold(v, ' pp', sign=True)})" for c, v in top2.items()) + ".</p>"
    )
    if drag:
        lines += f"<p><strong>Drag:</strong> " + ", ".join(f"{hi(c)} ({bold(ec_q[c], ' pp', sign=True)})" for c in drag) + ".</p>"
    else:
        lines += "<p>No demand component in negative contribution territory.</p>"
    return lines

def snap_cmt_hh():
    hh8_avg = round(float(hh_yoy_series.reindex(g8['period'].tolist()).mean()), 2)
    return (
        f"<p>Household consumption grew {bold(hh_now)} in {hi(q)}, "
        f"{vs_avg(hh_now, hh8_avg)}.</p>"
        f"<p><strong>Fastest:</strong> {hi(hh_q.index[0])} at {bold(hh_q.iloc[0])} "
        f"(contributes {bold(float(hc_q.get(hh_q.index[0], 0)), ' pp', sign=True)}).</p>"
        f"<p><strong>Slowest:</strong> {hi(hh_q.index[-1])} at {bold(hh_q.iloc[-1])}.</p>"
        + (f"<p><strong>Contracting:</strong> {hi(', '.join(hh_neg))}.</p>" if hh_neg else "")
        + f"<p>Dominant contributor: {hi(hc_q.index[0])} at {bold(hc_q.iloc[0], ' pp', sign=True)}.</p>"
    )

def snap_cmt_gfcf():
    gf8_avg = round(float(gfcf_yoy_series.reindex(g8['period'].tolist()).mean()), 2)
    return (
        f"<p>GFCF grew {bold(gf_now)} in {hi(q)}, "
        f"{vs_avg(gf_now, gf8_avg)}.</p>"
        f"<p><strong>Fastest:</strong> {hi(gf_q.index[0])} at {bold(gf_q.iloc[0])} "
        f"(contributes {bold(float(gc_q.get(gf_q.index[0], 0)), ' pp', sign=True)}).</p>"
        f"<p><strong>Slowest:</strong> {hi(gf_q.index[-1])} at {bold(gf_q.iloc[-1])}.</p>"
        + (f"<p><strong>Contracting:</strong> {hi(', '.join(gf_neg))}.</p>" if gf_neg else "")
        + f"<p>Dominant contributor: {hi(gc_q.index[0])} at {bold(gc_q.iloc[0], ' pp', sign=True)}.</p>"
    )

def snap_cmt_sectors():
    n_pos = sum(1 for v in sg_q.values if v >= 0)
    n_neg = sum(1 for v in sg_q.values if v < 0)
    mfg_v = round(float(sg_q.get('Manufacturing', 0)), 2)
    mfg_rank = list(sg_q.index).index('Manufacturing') + 1 if 'Manufacturing' in sg_q.index else None
    return (
        f"<p>In {hi(q)}, {n_pos} of 17 sectors grew; {n_neg} contracted.</p>"
        f"<p><strong>Top 3:</strong> "
        + ", ".join(f"{hi(sg_q.index[i])} ({bold(sg_q.iloc[i])})" for i in range(3)) + ".</p>"
        + f"<p><strong>Bottom 3:</strong> "
        + ", ".join(f"{hi(sg_q.index[-(i+1)])} ({bold(sg_q.iloc[-(i+1)])})" for i in range(3)) + ".</p>"
        + (f"<p>Manufacturing ranked {mfg_rank}/17 at {bold(mfg_v)}.</p>" if mfg_rank else "")
        + f"<p>Largest GDP contributor: {hi(sc_q.index[0])} ({bold(sc_q.iloc[0], ' pp', sign=True)}).</p>"
    )

def snap_cmt_mfg():
    mfg8_avg = round(float(mfg_yoy_series.reindex(g8['period'].tolist()).mean()), 2)
    n_pos = sum(1 for v in mg_q.values if v >= 0)
    n_neg = sum(1 for v in mg_q.values if v < 0)
    return (
        f"<p>Manufacturing grew {bold(mfg_now)} in {hi(q)}, "
        f"{vs_avg(mfg_now, mfg8_avg)}.</p>"
        f"<p>{n_pos} of 16 sub-sectors grew; {n_neg} contracted.</p>"
        f"<p><strong>Top 3:</strong> "
        + ", ".join(f"{hi(mg_q.index[i])} ({bold(mg_q.iloc[i])})" for i in range(3)) + ".</p>"
        + f"<p><strong>Bottom 3:</strong> "
        + ", ".join(f"{hi(mg_q.index[-(i+1)])} ({bold(mg_q.iloc[-(i+1)])})" for i in range(3)) + ".</p>"
        + f"<p>Top contributor: {hi(mc_q.index[0])} ({bold(mc_q.iloc[0], ' pp', sign=True)}).</p>"
    )

snap_comments = {
    'overview': snap_cmt_overview(),
    'hh':       snap_cmt_hh(),
    'gfcf':     snap_cmt_gfcf(),
    'sectors':  snap_cmt_sectors(),
    'mfg':      snap_cmt_mfg(),
}

# ── 6. Package for JS ──────────────────────────────────────────────────────────

def pivot(df, group_col, value_col):
    ps = sorted(df['period'].unique())
    out = {}
    for name, grp in df.groupby(group_col, sort=False):   # preserve insertion order
        s = grp.set_index('period')[value_col]
        out[name] = [round(float(s.get(p, 0) or 0), 3) for p in ps]
    return ps, out

exp_g_periods,  exp_g_data  = pivot(exp_growth,  'component',  'yoy')
exp_c_periods,  exp_c_data  = pivot(exp_contrib, 'component',  'contribution')
hh_g_periods,   hh_g_data   = pivot(hh_growth,   'component',  'yoy')
hh_c_periods,   hh_c_data   = pivot(hh_contrib,  'component',  'contribution')
gfcf_g_periods, gfcf_g_data = pivot(gfcf_growth, 'component',  'yoy')
gfcf_c_periods, gfcf_c_data = pivot(gfcf_contrib,'component',  'contribution')
sec_g_periods,  sec_g_data  = pivot(sec_growth,  'sector',     'yoy')
sec_c_periods,  sec_c_data  = pivot(sec_contrib, 'sector',     'contribution')
mfg_g_periods,  mfg_g_data  = pivot(mfg_growth,  'subsector',  'yoy')
mfg_c_periods,  mfg_c_data  = pivot(mfg_contrib, 'subsector',  'contribution')

# Snapshot helpers
TOTAL_KEYS = {'Household Total', 'GFCF Total', 'GDP', 'Manufacturing Total'}

def snap_sort(data_dict):
    """Latest value per series, total pinned first, rest sorted highest → lowest."""
    latest = {k: round(float(v[-1] or 0), 2) for k, v in data_dict.items()}
    totals = [(k, v) for k, v in latest.items() if k in TOTAL_KEYS]
    others = sorted([(k, v) for k, v in latest.items() if k not in TOTAL_KEYS],
                    key=lambda x: x[1], reverse=True)
    items = totals + others
    return {
        'labels':      [x[0] for x in items],
        'values':      [x[1] for x in items],
        'total_label': totals[0][0] if totals else None,
    }

def snap_fixed(data_dict, order):
    """Latest value per series in a fixed order; any extras appended at end."""
    latest = {k: round(float(v[-1] or 0), 2) for k, v in data_dict.items()}
    ordered = [(k, latest[k]) for k in order if k in latest]
    extras  = [(k, v) for k, v in latest.items() if k not in order]
    items   = ordered + extras
    total   = next((k for k in order if k in TOTAL_KEYS and k in latest), None)
    return {
        'labels':      [x[0] for x in items],
        'values':      [x[1] for x in items],
        'total_label': total,
    }

EXP_ORDER        = ['GDP', 'Household Consumption', 'Investment (PMTB)',
                    'Government', 'Exports (Goods)', 'Imports (Goods)']
EXP_ORDER_CONTRIB = ['Household Consumption', 'Investment (PMTB)',
                     'Government', 'Exports (Goods)', 'Imports (Goods)']

snap = {
    'period':        latest_period,
    'gdp_yoy':       latest_yoy,
    'gdp_avg8':      round(float(sum(yoy_vals[-8:]) / min(8, len(yoy_vals))), 2),
    'exp_growth':    snap_fixed(exp_g_data,  EXP_ORDER),
    'exp_contrib':   snap_fixed(exp_c_data,  EXP_ORDER_CONTRIB),
    'hh_growth':     snap_sort(hh_g_data),
    'hh_contrib':    snap_sort(hh_c_data),
    'gfcf_growth':   snap_sort(gfcf_g_data),
    'gfcf_contrib':  snap_sort(gfcf_c_data),
    'sec_growth':    snap_sort(sec_g_data),
    'sec_contrib':   snap_sort(sec_c_data),
    'mfg_growth':    snap_sort(mfg_g_data),
    'mfg_contrib':   snap_sort(mfg_c_data),
    'comments':      snap_comments,
}

data_js = {
    'periods':       periods,       'yoy':      yoy_vals,
    'precovid_mean': precovid_mean,
    'exp_g_periods':  exp_g_periods,  'exp_g_data':  exp_g_data,
    'exp_c_periods':  exp_c_periods,  'exp_c_data':  exp_c_data,
    'hh_g_periods':   hh_g_periods,   'hh_g_data':   hh_g_data,
    'hh_c_periods':   hh_c_periods,   'hh_c_data':   hh_c_data,
    'gfcf_g_periods': gfcf_g_periods, 'gfcf_g_data': gfcf_g_data,
    'gfcf_c_periods': gfcf_c_periods, 'gfcf_c_data': gfcf_c_data,
    'sec_g_periods':  sec_g_periods,  'sec_g_data':  sec_g_data,
    'sec_c_periods':  sec_c_periods,  'sec_c_data':  sec_c_data,
    'mfg_g_periods':  mfg_g_periods,  'mfg_g_data':  mfg_g_data,
    'mfg_c_periods':  mfg_c_periods,  'mfg_c_data':  mfg_c_data,
    'latest_period': latest_period, 'latest_yoy': latest_yoy,
    'prev_yoy':      prev_yoy,      'delta':      delta,
    'comments':      commentaries,
    'snap':          snap,
}

# ── 7. Colours ─────────────────────────────────────────────────────────────────

EXP_COLORS = {
    'GDP':                   '#1a1814',
    'Household Consumption': '#2563eb',
    'Government':            '#16a34a',
    'Investment (PMTB)':     '#d97706',
    'Exports (Goods)':       '#7c3aed',
    'Imports (Goods)':       '#dc2626',
}
SEC_COLORS = {
    'Agriculture':          '#15803d',
    'Mining & Quarrying':   '#92400e',
    'Manufacturing':        '#ea580c',
    'Electricity & Gas':    '#ca8a04',
    'Water & Waste':        '#4d7c0f',
    'Construction':         '#0e7490',
    'Trade':                '#2563eb',
    'Transport & Storage':  '#7c3aed',
    'Accommodation & Food': '#be185d',
    'Info & Comms':         '#0891b2',
    'Finance & Insurance':  '#db2777',
    'Real Estate':          '#9333ea',
    'Business Services':    '#0369a1',
    'Government Admin':     '#374151',
    'Education':            '#065f46',
    'Health & Social':      '#991b1b',
    'Other Services':       '#6b7280',
}

MFG_COLORS = {
    'Food & Beverages':           '#15803d',
    'Tobacco':                    '#374151',
    'Textiles & Apparel':         '#be185d',
    'Leather & Footwear':         '#92400e',
    'Wood Products':              '#4d7c0f',
    'Paper & Printing':           '#0369a1',
    'Coal & Oil Refining':        '#1a1814',
    'Chemicals & Pharma':         '#7c3aed',
    'Rubber & Plastics':          '#0e7490',
    'Non-metallic Minerals':      '#b45309',
    'Basic Metals':               '#6b7280',
    'Metal Products & Electronics': '#2563eb',
    'Machinery':                  '#0891b2',
    'Transport Equipment':        '#ea580c',
    'Furniture':                  '#9333ea',
    'Other Manufacturing':        '#db2777',
}

HH_COLORS = {
    'Household Total':    '#1a1814',
    'Food & Beverages':   '#15803d',
    'Apparel & Footwear': '#be185d',
    'Household Equipment':'#d97706',
    'Health & Education': '#7c3aed',
    'Transport & Comms':  '#2563eb',
    'Restaurant & Hotel': '#ea580c',
    'Other Consumption':  '#6b7280',
}
GFCF_COLORS = {
    'GFCF Total':            '#1a1814',
    'Buildings & Structures':'#0e7490',
    'Machine & Equipment':   '#ea580c',
    'Vehicles':              '#ca8a04',
    'Other Equipment':       '#6b7280',
    'Biological Resources':  '#15803d',
    'Intellectual Property': '#7c3aed',
}

# ── 8. HTML ────────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GDP Growth Dashboard — Test</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:#1a1814; --ink-light:#4a4740; --ink-faint:#8a8780;
    --paper:#f5f2ec; --paper-warm:#ede9e0; --paper-card:#faf8f4;
    --rule:#d8d3c8; --accent:#b5460f;
  }}
  *{{ margin:0; padding:0; box-sizing:border-box; }}
  body{{ background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif;
        font-weight:300; font-size:15px; line-height:1.7; }}
  header{{ background:var(--ink); color:var(--paper); padding:2.5rem 3rem 2rem; }}
  .header-label{{ font-family:'DM Mono',monospace; font-size:11px; letter-spacing:.2em;
                  text-transform:uppercase; color:var(--accent); margin-bottom:.75rem; }}
  header h1{{ font-family:'Playfair Display',serif; font-size:2rem; font-weight:400;
              line-height:1.2; margin-bottom:1rem; }}
  header h1 em{{ font-style:italic; color:rgba(245,242,236,.6); }}
  .header-meta{{ display:flex; gap:2rem; flex-wrap:wrap; }}
  .hm{{ font-family:'DM Mono',monospace; font-size:11px; color:rgba(245,242,236,.5); letter-spacing:.08em; }}
  .hm span{{ color:rgba(245,242,236,.9); display:block; font-size:13px; margin-top:2px; }}
  .container{{ max-width:1100px; margin:0 auto; padding:2rem 2rem 5rem; }}
  /* ── Window bar ── */
  .window-bar{{
    position:sticky; top:0; z-index:50;
    background:var(--paper-warm); border-bottom:1px solid var(--rule);
    padding:.6rem 2rem; display:flex; align-items:center; gap:1.5rem;
  }}
  .window-label{{ font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.15em;
                  text-transform:uppercase; color:var(--ink-faint); }}
  .window-btns{{ display:flex; gap:4px; }}
  .wbtn{{
    font-family:'DM Mono',monospace; font-size:11px; letter-spacing:.08em;
    padding:4px 14px; border-radius:2px; cursor:pointer;
    border:1px solid var(--rule); background:var(--paper-card); color:var(--ink-light);
    transition:all .15s;
  }}
  .wbtn:hover{{ background:var(--paper-warm); border-color:var(--ink-faint); color:var(--ink); }}
  .wbtn.active{{ background:var(--ink); border-color:var(--ink); color:var(--paper); font-weight:500; }}
  /* ── KPIs ── */
  .kpi-row{{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px;
             background:var(--rule); border:1px solid var(--rule); border-radius:4px;
             overflow:hidden; margin-bottom:2.5rem; }}
  .kpi{{ background:var(--paper-card); padding:1.25rem 1.5rem; }}
  .kpi-label{{ font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.15em;
               text-transform:uppercase; color:var(--ink-faint); margin-bottom:.4rem; }}
  .kpi-value{{ font-family:'Playfair Display',serif; font-size:2rem; font-weight:400; }}
  .kpi-value.pos{{ color:#2d5a27; }} .kpi-value.neg{{ color:#b5460f; }}
  .kpi-sub{{ font-family:'DM Mono',monospace; font-size:11px; color:var(--ink-faint); margin-top:.3rem; }}
  /* ── Sections ── */
  .block{{ margin-bottom:3rem; }}
  .block-header{{ display:flex; align-items:baseline; gap:1rem; margin-bottom:1.5rem;
                  padding-bottom:.6rem; border-bottom:2px solid var(--ink); }}
  .block-num{{ font-family:'DM Mono',monospace; font-size:11px; color:var(--ink-faint);
               letter-spacing:.1em; min-width:28px; }}
  .block-title{{ font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:400; }}
  .chart-wrap{{ background:var(--paper-card); border:1px solid var(--rule);
                border-radius:4px; padding:1.5rem; }}
  .chart-wrap h3{{ font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.12em;
                   text-transform:uppercase; color:var(--ink-faint); margin-bottom:1rem; }}
  .chart-full{{ background:var(--paper-card); border:1px solid var(--rule);
                border-radius:4px; padding:1.5rem; }}
  .chart-full h3{{ font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.12em;
                   text-transform:uppercase; color:var(--ink-faint); margin-bottom:1rem; }}
  .chart-note{{ font-family:'DM Mono',monospace; font-size:10px; color:var(--ink-faint); margin-top:.75rem; }}
  /* ── Commentary panel ── */
  .chart-with-comment{{ display:flex; gap:1.5rem; align-items:flex-start; }}
  .chart-with-comment .chart-full,
  .chart-with-comment .chart-wrap{{ flex:1; min-width:0; }}
  .comment-box{{
    width:260px; flex-shrink:0;
    background:var(--paper-card);
    border:1px solid var(--rule); border-left:3px solid var(--accent);
    border-radius:0 4px 4px 0; padding:1.25rem;
    display:none;
  }}
  .comment-box .cb-label{{
    font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.15em;
    text-transform:uppercase; color:var(--accent); margin-bottom:.75rem;
  }}
  .comment-box p{{ font-size:12.5px; color:var(--ink-light); line-height:1.6; margin-bottom:.5rem; }}
  .comment-box p:last-child{{ margin-bottom:0; }}
  .comment-box strong{{ color:var(--ink); font-weight:500; }}
  .comment-box em{{ font-style:normal; color:var(--ink); font-weight:500; }}
  body.short-active .comment-box{{ display:block; }}
  /* ── Snapshot layout ── */
  .snap-group{{ margin-bottom:3rem; }}
  .snap-group-header{{
    display:flex; align-items:baseline; gap:1rem; margin-bottom:1.5rem;
    padding-bottom:.6rem; border-bottom:2px solid var(--ink);
  }}
  .snap-group-num{{ font-family:'DM Mono',monospace; font-size:11px; color:var(--ink-faint);
                   letter-spacing:.1em; min-width:28px; }}
  .snap-group-title{{ font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:400; }}
  .snap-body{{ display:flex; gap:1.5rem; align-items:flex-start; }}
  .snap-comment{{
    width:260px; flex-shrink:0;
    background:var(--paper-card); border:1px solid var(--rule);
    border-left:3px solid var(--accent); border-radius:0 4px 4px 0; padding:1.25rem;
  }}
  .snap-comment .cb-label{{
    font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.15em;
    text-transform:uppercase; color:var(--accent); margin-bottom:.75rem;
  }}
  .snap-comment p{{ font-size:12.5px; color:var(--ink-light); line-height:1.6; margin-bottom:.5rem; }}
  .snap-comment p:last-child{{ margin-bottom:0; }}
  .snap-comment strong{{ color:var(--ink); font-weight:500; }}
  .snap-comment em{{ font-style:normal; color:var(--ink); font-weight:500; }}
  .snap-charts{{ flex:1; min-width:0; display:flex; flex-direction:column; gap:1.25rem; }}
  .snap-chart-wrap{{ background:var(--paper-card); border:1px solid var(--rule); border-radius:4px; padding:1.25rem; }}
  .snap-chart-wrap h3{{ font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.12em;
                        text-transform:uppercase; color:var(--ink-faint); margin-bottom:.75rem; }}
  footer{{ background:var(--paper-warm); border-top:1px solid var(--rule);
           padding:1.25rem 3rem; font-family:'DM Mono',monospace; font-size:11px;
           color:var(--ink-faint); display:flex; justify-content:space-between; }}
  @media(max-width:900px){{
    .chart-with-comment{{ flex-direction:column; }}
    .comment-box{{ width:100%; }}
    .kpi-row{{ grid-template-columns:repeat(2,1fr); }}
    header{{ padding:2rem 1.5rem; }}
  }}
  /* ── Top nav ── */
  .topnav{{ background:#2d2a26; border-bottom:2px solid var(--accent); }}
  .topnav-inner{{ max-width:1200px; margin:0 auto; padding:.5rem 2rem; display:flex; align-items:center; justify-content:space-between; }}
  .topnav-brand{{ font-family:'DM Mono',monospace; font-size:11px; color:rgba(245,242,236,.4); letter-spacing:.1em; }}
  .topnav-links{{ display:flex; gap:3px; }}
  .tnav-link{{ font-family:'DM Mono',monospace; font-size:11px; letter-spacing:.08em; text-transform:uppercase;
               padding:4px 14px; border-radius:2px; text-decoration:none;
               color:rgba(245,242,236,.55); transition:all .15s; }}
  .tnav-link:hover{{ color:var(--paper); background:rgba(255,255,255,.08); }}
  .tnav-link.active{{ background:var(--accent); color:var(--paper); }}
</style>
</head>
<body>

<div class="topnav">
  <div class="topnav-inner">
    <span class="topnav-brand">Indonesia Macro Dashboards · SEKI April 2026</span>
    <div class="topnav-links">
      <a href="econdashboard.html" class="tnav-link active">GDP Growth</a>
      <a href="bop_consistency.html" class="tnav-link">Balance of Payments</a>
    </div>
  </div>
</div>

<header>
  <div class="header-label">SEKI — Real Sector Dashboard · Test</div>
  <h1>Indonesia GDP Growth<br><em>Quarterly Year-on-Year, Constant 2010 Prices</em></h1>
  <div class="header-meta">
    <div class="hm">Source <span>SEKI Bab VII · Bank Indonesia</span></div>
    <div class="hm">Base year <span>2010 Constant Prices</span></div>
    <div class="hm">Frequency <span>Quarterly</span></div>
    <div class="hm">Updated <span>April 2026</span></div>
  </div>
</header>

<div class="window-bar">
  <span class="window-label">Analytical window</span>
  <div class="window-btns">
    <button class="wbtn" onclick="setWindow('snap')" id="btnSnap" style="border-right:2px solid var(--rule); margin-right:4px; padding-right:16px;">Latest Quarter · {latest_period}</button>
    <button class="wbtn" onclick="setWindow(8)"      id="btn2y">Short · 2Y</button>
    <button class="wbtn" onclick="setWindow(16)"     id="btn4y">Medium · 4Y</button>
    <button class="wbtn active" onclick="setWindow(0)" id="btnAll">All · {periods[0]}–{periods[-1]}</button>
  </div>
</div>

<div id="tabTimeseries">
<div class="container">

  <div class="kpi-row" style="margin-top:1.5rem;">
    <div class="kpi">
      <div class="kpi-label">Latest GDP Growth</div>
      <div class="kpi-value {'pos' if latest_yoy >= 0 else 'neg'}">{latest_yoy:+.2f}%</div>
      <div class="kpi-sub">{latest_period} · YoY</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Previous Quarter</div>
      <div class="kpi-value {'pos' if prev_yoy >= 0 else 'neg'}">{prev_yoy:+.2f}%</div>
      <div class="kpi-sub">One quarter prior · YoY</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Change vs Prior Q</div>
      <div class="kpi-value {'pos' if delta >= 0 else 'neg'}">{delta:+.2f} pp</div>
      <div class="kpi-sub">Percentage points</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Pre-COVID Mean</div>
      <div class="kpi-value">{precovid_mean:.2f}%</div>
      <div class="kpi-sub">2015 Q1 – 2019 Q4</div>
    </div>
  </div>

  <!-- 01: Headline -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">01</span>
      <h2 class="block-title">Headline GDP Growth</h2>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>YoY Growth (%)</h3>
        <div style="position:relative;height:280px"><canvas id="chartGDP"></canvas></div>
        <div class="chart-note">YoY = current quarter vs same quarter prior year.
          Dashed = 2015–2019 pre-COVID mean ({precovid_mean:.2f}%). Source: SEKI 7.2, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtGDPtext"></div>
      </div>
    </div>
  </div>

  <!-- 02: Demand -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">02</span>
      <h2 class="block-title">Demand Components</h2>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap">
        <h3>YoY Growth by Component (%)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpGrowth"></canvas></div>
        <div class="chart-note">Source: SEKI 7.4, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtExpGrowthtext"></div>
      </div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap">
        <h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpContrib"></canvas></div>
        <div class="chart-note">Imports sign-reversed. Source: SEKI 7.4.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtExpContribtext"></div>
      </div>
    </div>
  </div>

  <!-- 02b: Household Consumption Detail -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">02b</span>
      <h2 class="block-title">Household Consumption — Sub-components</h2>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap">
        <h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhGrowth"></canvas></div>
        <div class="chart-note">Includes Household Total for SEKI consistency check. Source: CEIC / Statistics Indonesia, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtHhGrowthtext"></div>
      </div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap">
        <h3>Contribution to Household Consumption Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhContrib"></canvas></div>
        <div class="chart-note">Source: CEIC / Statistics Indonesia, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtHhContribtext"></div>
      </div>
    </div>
  </div>

  <!-- 02c: GFCF Detail -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">02c</span>
      <h2 class="block-title">Gross Fixed Capital Formation — Sub-components</h2>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap">
        <h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfGrowth"></canvas></div>
        <div class="chart-note">Includes GFCF Total for SEKI consistency check. Source: CEIC / Statistics Indonesia, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtGfcfGrowthtext"></div>
      </div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap">
        <h3>Contribution to GFCF Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfContrib"></canvas></div>
        <div class="chart-note">Source: CEIC / Statistics Indonesia, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtGfcfContribtext"></div>
      </div>
    </div>
  </div>

  <!-- 03: Supply -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">03</span>
      <h2 class="block-title">Supply — Sectoral (17 sectors)</h2>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap">
        <h3>YoY Growth by Sector (%)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecGrowth"></canvas></div>
        <div class="chart-note">Source: SEKI 7.2, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtSecGrowthtext"></div>
      </div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap">
        <h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecContrib"></canvas></div>
        <div class="chart-note">Source: SEKI 7.2, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtSecContribtext"></div>
      </div>
    </div>
  </div>

  <!-- 04: Manufacturing subsectors -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">04</span>
      <h2 class="block-title">Manufacturing — Subsector Drill-down</h2>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap">
        <h3>YoY Growth by Subsector (%)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgGrowth"></canvas></div>
        <div class="chart-note">16 manufacturing subsectors. Source: SEKI 7.2, constant 2010 prices.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtMfgGrowthtext"></div>
      </div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap">
        <h3>Contribution to Manufacturing Growth (pp)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgContrib"></canvas></div>
        <div class="chart-note">Contribution to INDUSTRI PENGOLAHAN aggregate growth. Source: SEKI 7.2.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="cmtMfgContribtext"></div>
      </div>
    </div>
  </div>

</div>

</div><!-- /container -->
</div><!-- /tabTimeseries -->

<!-- ══ TAB 2: LATEST QUARTER SNAPSHOT ══════════════════════════════════════ -->
<div id="tabSnapshot" style="display:none">
<div class="container" style="padding-top:2rem">

  <!-- Group 1: Economy Overview -->
  <div class="snap-group">
    <div class="snap-group-header">
      <span class="snap-group-num">01</span>
      <h2 class="snap-group-title">Economy Overview</h2>
    </div>
    <div class="snap-body">
      <div class="snap-comment">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="snapCmtOverview"></div>
      </div>
      <div class="snap-charts">
        <div class="snap-chart-wrap">
          <h3>Demand Component YoY Growth (%)</h3>
          <div style="position:relative;height:220px"><canvas id="snapExpGrowth"></canvas></div>
        </div>
        <div class="snap-chart-wrap">
          <h3>Demand Component Contributions to GDP Growth (pp)</h3>
          <div style="position:relative;height:220px"><canvas id="snapExpContrib"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Group 2: Household Consumption -->
  <div class="snap-group">
    <div class="snap-group-header">
      <span class="snap-group-num">02</span>
      <h2 class="snap-group-title">Household Consumption</h2>
    </div>
    <div class="snap-body">
      <div class="snap-comment">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="snapCmtHh"></div>
      </div>
      <div class="snap-charts">
        <div class="snap-chart-wrap">
          <h3>YoY Growth by Component (%) — incl. total for reference</h3>
          <div style="position:relative;height:260px"><canvas id="snapHhGrowth"></canvas></div>
        </div>
        <div class="snap-chart-wrap">
          <h3>Contribution to Household Consumption Growth (pp)</h3>
          <div style="position:relative;height:230px"><canvas id="snapHhContrib"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Group 3: GFCF -->
  <div class="snap-group">
    <div class="snap-group-header">
      <span class="snap-group-num">03</span>
      <h2 class="snap-group-title">Gross Fixed Capital Formation</h2>
    </div>
    <div class="snap-body">
      <div class="snap-comment">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="snapCmtGfcf"></div>
      </div>
      <div class="snap-charts">
        <div class="snap-chart-wrap">
          <h3>YoY Growth by Component (%) — incl. total for reference</h3>
          <div style="position:relative;height:235px"><canvas id="snapGfcfGrowth"></canvas></div>
        </div>
        <div class="snap-chart-wrap">
          <h3>Contribution to GFCF Growth (pp)</h3>
          <div style="position:relative;height:210px"><canvas id="snapGfcfContrib"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Group 4: Sectors -->
  <div class="snap-group">
    <div class="snap-group-header">
      <span class="snap-group-num">04</span>
      <h2 class="snap-group-title">Production — All Sectors</h2>
    </div>
    <div class="snap-body">
      <div class="snap-comment">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="snapCmtSectors"></div>
      </div>
      <div class="snap-charts">
        <div class="snap-chart-wrap">
          <h3>YoY Growth by Sector (%)</h3>
          <div style="position:relative;height:490px"><canvas id="snapSecGrowth"></canvas></div>
        </div>
        <div class="snap-chart-wrap">
          <h3>Contribution to GDP Growth (pp)</h3>
          <div style="position:relative;height:490px"><canvas id="snapSecContrib"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Group 5: Manufacturing -->
  <div class="snap-group">
    <div class="snap-group-header">
      <span class="snap-group-num">05</span>
      <h2 class="snap-group-title">Manufacturing Drill-down</h2>
    </div>
    <div class="snap-body">
      <div class="snap-comment">
        <div class="cb-label">Latest quarter · {latest_period}</div>
        <div id="snapCmtMfg"></div>
      </div>
      <div class="snap-charts">
        <div class="snap-chart-wrap">
          <h3>YoY Growth by Sub-sector (%)</h3>
          <div style="position:relative;height:470px"><canvas id="snapMfgGrowth"></canvas></div>
        </div>
        <div class="snap-chart-wrap">
          <h3>Contribution to Manufacturing Growth (pp)</h3>
          <div style="position:relative;height:470px"><canvas id="snapMfgContrib"></canvas></div>
        </div>
      </div>
    </div>
  </div>

</div><!-- /container -->
</div><!-- /tabSnapshot -->

<footer>
  <span>Test Dashboard · SEKI April 2026</span>
  <span>Constant 2010 Prices · 17 sectors · 16 mfg subsectors</span>
</footer>

<script>
const D = {json.dumps(data_js)};
const EXP_COLORS = {json.dumps(EXP_COLORS)};
const SEC_COLORS = {json.dumps(SEC_COLORS)};
const MFG_COLORS  = {json.dumps(MFG_COLORS)};
const HH_COLORS   = {json.dumps(HH_COLORS)};
const GFCF_COLORS = {json.dumps(GFCF_COLORS)};

const MONO = "'DM Mono', monospace";
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.color = '#8a8780';

function xAxis() {{
  return {{
    ticks: {{ font:{{ family:MONO, size:10 }}, maxRotation:45, autoSkip:true, maxTicksLimit:12 }},
    grid:  {{ color:'rgba(0,0,0,0.05)' }}
  }};
}}
function yAxis(title) {{
  return {{
    title: {{ display:true, text:title, font:{{ family:MONO, size:10 }}, color:'#8a8780' }},
    ticks: {{ font:{{ family:MONO, size:10 }} }},
    grid:  {{ color:'rgba(0,0,0,0.05)' }}
  }};
}}
function lineDS(label, data, color, opts={{}}) {{
  return {{
    label, data, borderColor:color, borderWidth:1.8,
    pointRadius:0, pointHoverRadius:4, tension:0, fill:false, ...opts
  }};
}}
function tooltipFmt(suffix) {{
  return {{
    itemSort: (a, b) => b.parsed.y - a.parsed.y,
    callbacks: {{
      label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y != null ? ctx.parsed.y.toFixed(2) : ''}}${{suffix}}`
    }}
  }};
}}
function legend() {{
  return {{ labels: {{ font:{{ family:MONO, size:10 }}, boxWidth:10, padding:10 }} }};
}}
function legendRight() {{
  return {{ position:'right', labels: {{ font:{{ family:MONO, size:10 }}, boxWidth:10, padding:10 }} }};
}}

// 01 Headline GDP — bar chart
const cGDP = new Chart(document.getElementById('chartGDP'), {{
  type: 'bar',
  data: {{
    labels: D.periods,
    datasets: [
      {{
        label: 'GDP YoY (%)',
        data: D.yoy,
        backgroundColor: D.yoy.map(v => v >= 0 ? 'rgba(45,90,39,0.75)' : 'rgba(181,70,15,0.75)'),
        borderColor:     D.yoy.map(v => v >= 0 ? '#2d5a27' : '#b5460f'),
        borderWidth:1, borderRadius:2, order:2,
      }},
      {{
        label: `Pre-COVID Mean (${{D.precovid_mean.toFixed(2)}}%)`,
        data: D.periods.map(() => D.precovid_mean),
        type:'line', borderColor:'#8a6c1a', borderDash:[5,4],
        borderWidth:1.5, pointRadius:0, tension:0, fill:false, order:1,
      }}
    ]
  }},
  options: {{
    responsive:true,
    interaction: {{ mode:'index', intersect:false }},
    plugins: {{
      legend: legend(),
      tooltip: {{
        backgroundColor:'rgba(26,24,20,0.92)',
        titleFont:{{ family:MONO, size:11 }}, bodyFont:{{ family:MONO, size:12 }}, padding:12,
        itemSort: (a, b) => b.parsed.y - a.parsed.y,
        callbacks: {{
          title: items => items[0].label,
          label: ctx => ctx.datasetIndex === 0
            ? ` GDP YoY: ${{ctx.parsed.y >= 0 ? '+' : ''}}${{ctx.parsed.y.toFixed(2)}}%`
            : ` Pre-COVID Mean: ${{ctx.parsed.y.toFixed(2)}}%`
        }}
      }}
    }},
    scales: {{ x:xAxis(), y:yAxis('YoY (%)') }},
    maintainAspectRatio: false
  }}
}});

function chartOpts(lgd, suffix, yLabel) {{
  return {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode:'index', intersect:false }},
    plugins: {{ legend: lgd, tooltip: tooltipFmt(suffix) }},
    scales: {{ x:xAxis(), y:yAxis(yLabel) }}
  }};
}}

const cExpG = new Chart(document.getElementById('chartExpGrowth'), {{
  type:'line',
  data: {{ labels:D.exp_g_periods, datasets:Object.entries(D.exp_g_data).map(([l,v]) =>
    lineDS(l, v, EXP_COLORS[l]||'#999', l==='GDP' ? {{borderWidth:2.5, borderDash:[4,3]}} : {{}})) }},
  options: chartOpts(legend(), '%', 'YoY (%)')
}});

const cExpC = new Chart(document.getElementById('chartExpContrib'), {{
  type:'line',
  data: {{ labels:D.exp_c_periods, datasets:Object.entries(D.exp_c_data).map(([l,v]) => lineDS(l,v,EXP_COLORS[l]||'#999')) }},
  options: chartOpts(legend(), ' pp', 'pp')
}});

const cHhG = new Chart(document.getElementById('chartHhGrowth'), {{
  type:'line',
  data: {{ labels:D.hh_g_periods, datasets:Object.entries(D.hh_g_data).map(([l,v]) =>
    lineDS(l, v, HH_COLORS[l]||'#999', l==='Household Total' ? {{borderWidth:2.5, borderDash:[4,3]}} : {{}})) }},
  options: chartOpts(legendRight(), '%', 'YoY (%)')
}});

const cHhC = new Chart(document.getElementById('chartHhContrib'), {{
  type:'line',
  data: {{ labels:D.hh_c_periods, datasets:Object.entries(D.hh_c_data).map(([l,v]) =>
    lineDS(l, v, HH_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), ' pp', 'pp')
}});

const cGfcfG = new Chart(document.getElementById('chartGfcfGrowth'), {{
  type:'line',
  data: {{ labels:D.gfcf_g_periods, datasets:Object.entries(D.gfcf_g_data).map(([l,v]) =>
    lineDS(l, v, GFCF_COLORS[l]||'#999', l==='GFCF Total' ? {{borderWidth:2.5, borderDash:[4,3]}} : {{}})) }},
  options: chartOpts(legendRight(), '%', 'YoY (%)')
}});

const cGfcfC = new Chart(document.getElementById('chartGfcfContrib'), {{
  type:'line',
  data: {{ labels:D.gfcf_c_periods, datasets:Object.entries(D.gfcf_c_data).map(([l,v]) =>
    lineDS(l, v, GFCF_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), ' pp', 'pp')
}});

const cSecG = new Chart(document.getElementById('chartSecGrowth'), {{
  type:'line',
  data: {{ labels:D.sec_g_periods, datasets:Object.entries(D.sec_g_data).map(([l,v]) => lineDS(l,v,SEC_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), '%', 'YoY (%)')
}});

const cSecC = new Chart(document.getElementById('chartSecContrib'), {{
  type:'line',
  data: {{ labels:D.sec_c_periods, datasets:Object.entries(D.sec_c_data).map(([l,v]) => lineDS(l,v,SEC_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), ' pp', 'pp')
}});

const cMfgG = new Chart(document.getElementById('chartMfgGrowth'), {{
  type:'line',
  data: {{ labels:D.mfg_g_periods, datasets:Object.entries(D.mfg_g_data).map(([l,v]) => lineDS(l,v,MFG_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), '%', 'YoY (%)')
}});

const cMfgC = new Chart(document.getElementById('chartMfgContrib'), {{
  type:'line',
  data: {{ labels:D.mfg_c_periods, datasets:Object.entries(D.mfg_c_data).map(([l,v]) => lineDS(l,v,MFG_COLORS[l]||'#999')) }},
  options: chartOpts(legendRight(), ' pp', 'pp')
}});

// ── window toggle ──────────────────────────────────────────────────────────────

const ALL_DATA = {{
  gdp:   {{ periods:D.periods,        datasets:[D.yoy, D.periods.map(()=>D.precovid_mean)] }},
  expG:  {{ periods:D.exp_g_periods,  datasets:Object.values(D.exp_g_data) }},
  expC:  {{ periods:D.exp_c_periods,  datasets:Object.values(D.exp_c_data) }},
  hhG:   {{ periods:D.hh_g_periods,   datasets:Object.values(D.hh_g_data) }},
  hhC:   {{ periods:D.hh_c_periods,   datasets:Object.values(D.hh_c_data) }},
  gfcfG: {{ periods:D.gfcf_g_periods, datasets:Object.values(D.gfcf_g_data) }},
  gfcfC: {{ periods:D.gfcf_c_periods, datasets:Object.values(D.gfcf_c_data) }},
  secG:  {{ periods:D.sec_g_periods,  datasets:Object.values(D.sec_g_data) }},
  secC:  {{ periods:D.sec_c_periods,  datasets:Object.values(D.sec_c_data) }},
  mfgG:  {{ periods:D.mfg_g_periods,  datasets:Object.values(D.mfg_g_data) }},
  mfgC:  {{ periods:D.mfg_c_periods,  datasets:Object.values(D.mfg_c_data) }},
}};

function applyWindow(chart, allPeriods, allDatasets, n) {{
  const labels = n ? allPeriods.slice(-n) : allPeriods;
  chart.data.labels = labels;
  chart.data.datasets.forEach((ds, i) => {{
    const vals = n ? allDatasets[i].slice(-n) : allDatasets[i];
    ds.data = vals;
    if (chart === cGDP && i === 0) {{
      ds.backgroundColor = vals.map(v => v >= 0 ? 'rgba(45,90,39,0.75)' : 'rgba(181,70,15,0.75)');
      ds.borderColor     = vals.map(v => v >= 0 ? '#2d5a27' : '#b5460f');
    }}
  }});
  if (chart === cGDP) chart.data.datasets[1].data = labels.map(() => D.precovid_mean);
  chart.update();
}}

// Populate commentary (once at load)
document.getElementById('cmtGDPtext').innerHTML        = D.comments.gdp;
document.getElementById('cmtExpGrowthtext').innerHTML  = D.comments.expGrowth;
document.getElementById('cmtExpContribtext').innerHTML = D.comments.expContrib;
document.getElementById('cmtSecGrowthtext').innerHTML  = D.comments.secGrowth;
document.getElementById('cmtSecContribtext').innerHTML = D.comments.secContrib;
document.getElementById('cmtHhGrowthtext').innerHTML   = D.comments.hhGrowth;
document.getElementById('cmtHhContribtext').innerHTML  = D.comments.hhContrib;
document.getElementById('cmtGfcfGrowthtext').innerHTML = D.comments.gfcfGrowth;
document.getElementById('cmtGfcfContribtext').innerHTML= D.comments.gfcfContrib;
document.getElementById('cmtMfgGrowthtext').innerHTML  = D.comments.mfgGrowth;
document.getElementById('cmtMfgContribtext').innerHTML = D.comments.mfgContrib;

// (tab switching now handled inside setWindow)

// ── Snapshot horizontal bar charts (built lazily on first tab switch) ─────────
let snapChartsBuilt = false;

function snapBarDS(labels, values, totalLabel) {{
  return {{
    label: '',
    data: values,
    backgroundColor: labels.map((l, i) =>
      l === totalLabel ? 'rgba(26,24,20,0.82)' :
      values[i] >= 0  ? 'rgba(45,90,39,0.75)' : 'rgba(181,70,15,0.75)'),
    borderColor: labels.map((l, i) =>
      l === totalLabel ? '#1a1814' :
      values[i] >= 0  ? '#2d5a27' : '#b5460f'),
    borderWidth: labels.map(l => l === totalLabel ? 2 : 1),
    borderRadius: 2,
  }};
}}

function snapOpts(suffix, refLine) {{
  const plugins = {{
    legend: {{ display: false }},
    tooltip: {{
      callbacks: {{
        label: ctx => ` ${{ctx.parsed.x != null ? ctx.parsed.x.toFixed(2) : ''}}${{suffix}}`
      }}
    }}
  }};
  if (refLine !== undefined) {{
    plugins.annotation = {{ annotations: {{
      ref: {{ type:'line', xMin:refLine, xMax:refLine,
              borderColor:'#8a6c1a', borderDash:[4,3], borderWidth:1.5 }}
    }}}};
  }}
  return {{
    responsive: true, maintainAspectRatio: false,
    indexAxis: 'y',
    plugins,
    scales: {{
      x: {{ ticks:{{ font:{{ family:MONO, size:10 }} }}, grid:{{ color:'rgba(0,0,0,0.05)' }} }},
      y: {{ ticks:{{ font:{{ family:MONO, size:10 }} }}, grid:{{ display:false }} }}
    }}
  }};
}}

function buildSnapChart(id, snap_data, suffix) {{
  return new Chart(document.getElementById(id), {{
    type: 'bar',
    data: {{ labels: snap_data.labels,
             datasets: [snapBarDS(snap_data.labels, snap_data.values, snap_data.total_label)] }},
    options: snapOpts(suffix)
  }});
}}

function buildSnapCharts() {{
  try {{
    const S = D.snap;

    document.getElementById('snapCmtOverview').innerHTML = S.comments.overview;
    document.getElementById('snapCmtHh').innerHTML       = S.comments.hh;
    document.getElementById('snapCmtGfcf').innerHTML     = S.comments.gfcf;
    document.getElementById('snapCmtSectors').innerHTML  = S.comments.sectors;
    document.getElementById('snapCmtMfg').innerHTML      = S.comments.mfg;

    buildSnapChart('snapExpContrib',  S.exp_contrib,  ' pp');
    buildSnapChart('snapExpGrowth',   S.exp_growth,   '%');
    buildSnapChart('snapHhGrowth',    S.hh_growth,    '%');
    buildSnapChart('snapHhContrib',   S.hh_contrib,   ' pp');
    buildSnapChart('snapGfcfGrowth',  S.gfcf_growth,  '%');
    buildSnapChart('snapGfcfContrib', S.gfcf_contrib, ' pp');
    buildSnapChart('snapSecGrowth',   S.sec_growth,   '%');
    buildSnapChart('snapSecContrib',  S.sec_contrib,  ' pp');
    buildSnapChart('snapMfgGrowth',   S.mfg_growth,   '%');
    buildSnapChart('snapMfgContrib',  S.mfg_contrib,  ' pp');

    snapChartsBuilt = true;
  }} catch(e) {{
    console.error('buildSnapCharts failed:', e);
  }}
}}

function setWindow(n) {{
  const isSnap = n === 'snap';
  document.getElementById('tabTimeseries').style.display = isSnap ? 'none'  : 'block';
  document.getElementById('tabSnapshot').style.display   = isSnap ? 'block' : 'none';
  document.querySelectorAll('.wbtn').forEach(b => b.classList.remove('active'));

  if (isSnap) {{
    document.getElementById('btnSnap').classList.add('active');
    document.body.classList.remove('short-active');
    if (!snapChartsBuilt) buildSnapCharts();
    return;
  }}

  applyWindow(cGDP,   ALL_DATA.gdp.periods,   ALL_DATA.gdp.datasets,   n);
  applyWindow(cExpG,  ALL_DATA.expG.periods,  ALL_DATA.expG.datasets,  n);
  applyWindow(cExpC,  ALL_DATA.expC.periods,  ALL_DATA.expC.datasets,  n);
  applyWindow(cHhG,   ALL_DATA.hhG.periods,   ALL_DATA.hhG.datasets,   n);
  applyWindow(cHhC,   ALL_DATA.hhC.periods,   ALL_DATA.hhC.datasets,   n);
  applyWindow(cGfcfG, ALL_DATA.gfcfG.periods, ALL_DATA.gfcfG.datasets, n);
  applyWindow(cGfcfC, ALL_DATA.gfcfC.periods, ALL_DATA.gfcfC.datasets, n);
  applyWindow(cSecG,  ALL_DATA.secG.periods,  ALL_DATA.secG.datasets,  n);
  applyWindow(cSecC,  ALL_DATA.secC.periods,  ALL_DATA.secC.datasets,  n);
  applyWindow(cMfgG,  ALL_DATA.mfgG.periods,  ALL_DATA.mfgG.datasets,  n);
  applyWindow(cMfgC,  ALL_DATA.mfgC.periods,  ALL_DATA.mfgC.datasets,  n);
  document.getElementById(n===8 ? 'btn2y' : n===16 ? 'btn4y' : 'btnAll').classList.add('active');
  document.body.classList.toggle('short-active', n === 8);
}}
</script>

</body>
</html>"""

out = os.path.join(HTML, "econdashboard.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written: {out}")
