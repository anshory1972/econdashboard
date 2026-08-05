"""Combined dashboard — GDP Growth + Balance of Payments → econdashboard.html"""
import pandas as pd, numpy as np, json, os, xlrd, re

CLEAN = r"C:\work\economist\rawdata\seki\clean"
HTML  = r"C:\work\economist\html"
os.makedirs(HTML, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# PART 1 · GDP DATA
# ══════════════════════════════════════════════════════════════════════════════
sec = pd.read_csv(os.path.join(CLEAN, "gdp_sector_constant.csv"))
exp = pd.read_csv(os.path.join(CLEAN, "gdp_expenditure_constant.csv"))

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

EXP_MAP = {
    'Rumah Tangga': 'Household Consumption', 'Pemerintah': 'Government',
    'Pembentukan Modal Tetap Domestik Bruto': 'Investment (PMTB)',
    'Ekspor Barang': 'Exports (Goods)', 'Impor Barang (-/-)': 'Imports (Goods)',
}
exp_components     = {k: v for k, v in EXP_MAP.items() if k in exp['series'].unique()}
gdp_total_name_exp = next(s for s in exp['series'].unique() if 'domestik bruto' in s.lower())
gdp_total_exp      = exp[exp['series'] == gdp_total_name_exp].sort_values('period').set_index('period')['value']

exp_growth_records, exp_contrib_records = [], []
for p, v in zip(periods, yoy_vals):
    exp_growth_records.append({'period': p, 'component': 'GDP', 'yoy': round(v, 2)})
for raw, label in exp_components.items():
    comp = exp[exp['series'] == raw].sort_values('period').set_index('period')['value']
    for p, v in (comp.pct_change(4)*100).dropna().items():
        if p >= '2015-Q1': exp_growth_records.append({'period':p,'component':label,'yoy':round(v,2)})
    sign = -1 if label == 'Imports (Goods)' else 1
    for p, v in ((comp-comp.shift(4))/gdp_total_exp.shift(4)*100).dropna().items():
        if p >= '2015-Q1': exp_contrib_records.append({'period':p,'component':label,'contribution':round(v*sign,3)})
exp_growth = pd.DataFrame(exp_growth_records)
exp_contrib = pd.DataFrame(exp_contrib_records)

SEC_MAP = {
    'PERTANIAN, KEHUTANAN & PERIKANAN':'Agriculture',
    'PERTAMBANGAN & PENGGALIAN':'Mining & Quarrying','INDUSTRI PENGOLAHAN':'Manufacturing',
    'PENGADAAN LISTRIK DAN GAS':'Electricity & Gas',
    'PENGADAAN AIR, PENGELOLAAN SAMPAH, LIMBAH DAN DAUR ULANG':'Water & Waste',
    'KONSTRUKSI':'Construction',
    'PERDAGANGAN BESAR DAN ECERAN, REPARASI MOBIL DAN MOTOR':'Trade',
    'TRANSPORTASI DAN PERGUDANGAN':'Transport & Storage',
    'PENYEDIAAN AKOMODASI DAN MAKAN MINUIM':'Accommodation & Food',
    'INFORMASI DAN KOMUNIKASI':'Info & Comms','JASA KEUANGAN DAN ASURANSI':'Finance & Insurance',
    'REAL ESTATE':'Real Estate','JASA PERUSAHAAN':'Business Services',
    'ADMINISTRASI PEMERINTAHAN, PERTAHANAN DAN JAMINAN SOSIAL WAJIB':'Government Admin',
    'JASA PENDIDIKAN':'Education','JASA KESEHATAN DAN KEGIATAN LAINNYA':'Health & Social',
    'JASA LAINNYA':'Other Services',
}
sec_avail    = {k: v for k, v in SEC_MAP.items() if k in sec['series'].unique()}
gdp_total_sec = sec[sec['series']=='PRODUK DOMESTIK BRUTO'].sort_values('period').set_index('period')['value']

sec_growth_records, sec_contrib_records = [], []
for raw, label in sec_avail.items():
    comp = sec[sec['series']==raw].sort_values('period').set_index('period')['value']
    for p, v in (comp.pct_change(4)*100).dropna().items():
        if p >= '2015-Q1': sec_growth_records.append({'period':p,'sector':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/gdp_total_sec.shift(4)*100).dropna().items():
        if p >= '2015-Q1': sec_contrib_records.append({'period':p,'sector':label,'contribution':round(v,3)})
sec_growth = pd.DataFrame(sec_growth_records)
sec_contrib = pd.DataFrame(sec_contrib_records)

MFG_MAP = {
    'Industri Makanan dan Minuman':'Food & Beverages','Pengolahan Tembakau':'Tobacco',
    'Industri Tekstil dan Pakaian Jadi':'Textiles & Apparel',
    'Industri Kulit, Barang dari Kulit dan Alas Kaki':'Leather & Footwear',
    'Industri Kayu, Barang dari Kayu, Gabus dan Barang Anyaman dari Bambu, Rotan dan sejenisnya':'Wood Products',
    'Industri Kertas dan Barang dari kertas, Percetakan dan Reproduksi Media Rekaman':'Paper & Printing',
    'Industri Batubara dan Pengilangan Migas':'Coal & Oil Refining',
    'industri Kimia, Farmasi dan Obat Tradisional':'Chemicals & Pharma',
    'Industri Karet, Barang dari Karet dan Plastik':'Rubber & Plastics',
    'Industri Barang Galian bukan logam':'Non-metallic Minerals','Industri Logam Dasar':'Basic Metals',
    'Industri Barang dari Logam, Komputer, Barang Elektronik, Optik dan Peralatan Listrik':'Metal Products & Electronics',
    'Industri Mesin dan Perlengkapan':'Machinery','Industri Alat Angkutan':'Transport Equipment',
    'Industri Furnitur':'Furniture',
    'Industri Pengolahan Lainnya, Jasa Reparasi dan Pemasangan Mesin dan Peralatan':'Other Manufacturing',
}
mfg_avail  = {k: v for k, v in MFG_MAP.items() if k in sec['series'].unique()}
mfg_total  = sec[sec['series']=='INDUSTRI PENGOLAHAN'].sort_values('period').set_index('period')['value']

mfg_growth_records, mfg_contrib_records = [], []
for raw, label in mfg_avail.items():
    comp = sec[sec['series']==raw].sort_values('period').set_index('period')['value']
    for p, v in (comp.pct_change(4)*100).dropna().items():
        if p >= '2015-Q1': mfg_growth_records.append({'period':p,'subsector':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/mfg_total.shift(4)*100).dropna().items():
        if p >= '2015-Q1': mfg_contrib_records.append({'period':p,'subsector':label,'contribution':round(v,3)})
mfg_growth = pd.DataFrame(mfg_growth_records)
mfg_contrib = pd.DataFrame(mfg_contrib_records)

ceic_raw = pd.read_csv(r'C:\work\economist\rawdata\ceic\ceic_gdp_exp.csv')
is_data  = ceic_raw.iloc[:,0].astype(str).str.match(r'^\d{2}/\d{4}$')
ceic     = ceic_raw[is_data].copy()
_qmap    = {'03':'Q1','06':'Q2','09':'Q3','12':'Q4'}
ceic['period'] = ceic.iloc[:,0].apply(lambda d: f"{d[3:]}-{_qmap[d[:2]]}")
ceic = ceic[ceic['period'] >= '2015-Q1'].reset_index(drop=True)
_pfx = 'Gross Domestic Product: SNA 2008: 2010p: '
ceic = ceic.rename(columns={c: c.replace(_pfx,'') for c in ceic.columns}).set_index('period')
for col in ceic.columns:
    if col != 'Unnamed: 0': ceic[col] = pd.to_numeric(ceic[col], errors='coerce')

HH_TOTAL = 'Consumption Expenditure: Household'
HH_MAP   = {
    'Consumption Expenditure: Household: Food & Beverages, Other than Restaurant':'Food & Beverages',
    'Consumption Expenditure: Household: Apparel, Footwear & Maintenance Services':'Apparel & Footwear',
    'Consumption Expenditure: Household: Equipments':'Household Equipment',
    'Consumption Expenditure: Household: Health & Education':'Health & Education',
    'Consumption Expenditure: Household: Transportation & Communication':'Transport & Comms',
    'Consumption Expenditure: Household: Restaurant & Hotel':'Restaurant & Hotel',
    'Consumption Expenditure: Household: Others':'Other Consumption',
}
hh_total = ceic[HH_TOTAL]
hh_growth_records, hh_contrib_records = [], []
for p, v in (hh_total.pct_change(4)*100).dropna().items():
    hh_growth_records.append({'period':p,'component':'Household Total','yoy':round(v,2)})
for raw, label in HH_MAP.items():
    comp = ceic[raw]
    for p, v in (comp.pct_change(4)*100).dropna().items():
        hh_growth_records.append({'period':p,'component':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/hh_total.shift(4)*100).dropna().items():
        hh_contrib_records.append({'period':p,'component':label,'contribution':round(v,3)})
hh_growth = pd.DataFrame(hh_growth_records)
hh_contrib = pd.DataFrame(hh_contrib_records)

GFCF_TOTAL = 'Gross Fixed Capital Formation'
GFCF_MAP   = {
    'GFCF: Buildings & Structures':'Buildings & Structures','GFCF: Machine & Equipment':'Machine & Equipment',
    'GFCF: Vehicles':'Vehicles','GFCF: Other Equipments':'Other Equipment',
    'GFCF: Cultivated Biological Resources':'Biological Resources',
    'GFCF: Intellectual Property Products':'Intellectual Property',
}
gfcf_total = ceic[GFCF_TOTAL]
gfcf_growth_records, gfcf_contrib_records = [], []
for p, v in (gfcf_total.pct_change(4)*100).dropna().items():
    gfcf_growth_records.append({'period':p,'component':'GFCF Total','yoy':round(v,2)})
for raw, label in GFCF_MAP.items():
    comp = ceic[raw]
    for p, v in (comp.pct_change(4)*100).dropna().items():
        gfcf_growth_records.append({'period':p,'component':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/gfcf_total.shift(4)*100).dropna().items():
        gfcf_contrib_records.append({'period':p,'component':label,'contribution':round(v,3)})

hh_yoy_series   = (hh_total.pct_change(4)*100).dropna()
gfcf_yoy_series = (gfcf_total.pct_change(4)*100).dropna()
mfg_yoy_series  = (mfg_total.pct_change(4)*100).dropna()
gfcf_growth = pd.DataFrame(gfcf_growth_records)
gfcf_contrib = pd.DataFrame(gfcf_contrib_records)

# ── GDP commentaries ──────────────────────────────────────────────────────────
def bold(x, suffix='%', decimals=2, sign=False):
    fmt = f'{x:+.{decimals}f}' if sign else f'{x:.{decimals}f}'
    return f'<strong>{fmt}{suffix}</strong>'
def hi(text): return f'<em>{text}</em>'
def vs_avg(v, avg, unit='%'):
    diff = v - avg
    return f"{'above' if diff>=0 else 'below'} its 8Q avg ({bold(avg,unit)}) by <strong>{abs(diff):.2f}{unit}</strong>"

g8=gdp.tail(8); q=g8.iloc[-1]['period']; g_now=g8.iloc[-1]['yoy']
g_prev=g8.iloc[-2]['yoy']; g_avg8=g8['yoy'].mean(); g_swing=g_now-g_prev

gdp_comment=(f"<p>GDP grew {bold(g_now)} YoY in {hi(q)}, "
    f"{'up' if g_swing>=0 else 'down'} {bold(abs(g_swing),sign=False)} pp from {bold(g_prev)} prior quarter.</p>"
    f"<p>Reading is {vs_avg(g_now,g_avg8)}, and {bold(g_now-precovid_mean,'%',sign=True)} vs "
    f"2015–2019 pre-COVID mean of {bold(precovid_mean)}.</p>")

eg8=exp_growth[exp_growth['period'].isin(g8['period'].tolist())]
eg_avg=eg8.groupby('component')['yoy'].mean()
eg_q=eg8[eg8['period']==q].set_index('component')['yoy'].sort_values(ascending=False)
eg_neg=[c for c in eg_q.index if eg_q[c]<0]
exp_growth_comment=(f"<p>Demand growth in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(c)}: {bold(v)} — {vs_avg(v,float(eg_avg.get(c,0)))}</p>" for c,v in eg_q.items())
    +(f"<p>{hi(', '.join(eg_neg))} contracted.</p>" if eg_neg else ""))

ec8=exp_contrib[exp_contrib['period'].isin(g8['period'].tolist())]
ec_avg=ec8.groupby('component')['contribution'].mean()
ec_q=ec8[ec8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)
ec_neg=[c for c in ec_q.index if ec_q[c]<0]
exp_contrib_comment=(f"<p>Contributions to {bold(g_now)} GDP growth in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(c)}: {bold(v,' pp',sign=True)} — {vs_avg(v,float(ec_avg.get(c,0)),' pp')}</p>" for c,v in ec_q.items())
    +(f"<p>Drag: {hi(', '.join(ec_neg))}.</p>" if ec_neg else ""))

sg8=sec_growth[sec_growth['period'].isin(g8['period'].tolist())]
sg_avg=sg8.groupby('sector')['yoy'].mean()
sg_q=sg8[sg8['period']==q].set_index('sector')['yoy'].sort_values(ascending=False)
sg_neg=[s for s in sg_q.index if sg_q[s]<0]
sec_growth_comment=(f"<p><strong>Top 3 sectors</strong> in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(sg_avg.get(s,0)))}</p>" for s,v in sg_q.head(3).items())
    +f"<p><strong>Bottom 3:</strong></p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(sg_avg.get(s,0)))}</p>" for s,v in sg_q.tail(3).items())
    +(f"<p>Contracting: {hi(', '.join(sg_neg))}.</p>" if sg_neg else ""))

sc8=sec_contrib[sec_contrib['period'].isin(g8['period'].tolist())]
sc_avg=sc8.groupby('sector')['contribution'].mean()
sc_q=sc8[sc8['period']==q].set_index('sector')['contribution'].sort_values(ascending=False)
sc_neg=[s for s in sc_q.index if sc_q[s]<0]
sec_contrib_comment=(f"<p><strong>Top 3 contributors</strong> in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v,' pp',sign=True)} — {vs_avg(v,float(sc_avg.get(s,0)),' pp')}</p>" for s,v in sc_q.head(3).items())
    +(f"<p>Drag: {hi(', '.join(sc_neg))}.</p>" if sc_neg else ""))

mg8=mfg_growth[mfg_growth['period'].isin(g8['period'].tolist())]
mg_avg=mg8.groupby('subsector')['yoy'].mean()
mg_q=mg8[mg8['period']==q].set_index('subsector')['yoy'].sort_values(ascending=False)
mg_neg=[s for s in mg_q.index if mg_q[s]<0]
mc8=mfg_contrib[mfg_contrib['period'].isin(g8['period'].tolist())]
mc_avg=mc8.groupby('subsector')['contribution'].mean()
mc_q=mc8[mc8['period']==q].set_index('subsector')['contribution'].sort_values(ascending=False)
mc_neg=[s for s in mc_q.index if mc_q[s]<0]
mfg_now=round(float(mfg_yoy_series.get(q,0)),2); mfg_prev=round(float(mfg_yoy_series.get(g8.iloc[-2]['period'],0)),2)
mfg_growth_comment=(f"<p>Manufacturing grew {bold(mfg_now)} in {hi(q)} ({'up' if mfg_now>=mfg_prev else 'down'} from {bold(mfg_prev)}).</p>"
    +f"<p><strong>Top 3:</strong></p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(mg_avg.get(s,0)))}</p>" for s,v in mg_q.head(3).items())
    +f"<p><strong>Bottom 3:</strong></p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(mg_avg.get(s,0)))}</p>" for s,v in mg_q.tail(3).items())
    +(f"<p>Contracting: {hi(', '.join(mg_neg))}.</p>" if mg_neg else ""))
mfg_contrib_comment=(f"<p>Contributions to manufacturing growth in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v,' pp',sign=True)} — {vs_avg(v,float(mc_avg.get(s,0)),' pp')}</p>" for s,v in mc_q.head(3).items())
    +(f"<p>Drag: {hi(', '.join(mc_neg))}.</p>" if mc_neg else ""))

hh8=hh_growth[hh_growth['period'].isin(g8['period'].tolist())&(hh_growth['component']!='Household Total')]
hh_avg=hh8.groupby('component')['yoy'].mean()
hh_q=hh8[hh8['period']==q].set_index('component')['yoy'].sort_values(ascending=False)
hh_neg=[c for c in hh_q.index if hh_q[c]<0]
hh_now=round(float(hh_yoy_series.get(q,0)),2); hh_prev=round(float(hh_yoy_series.get(g8.iloc[-2]['period'],0)),2)
hc8=hh_contrib[hh_contrib['period'].isin(g8['period'].tolist())]
hc_avg=hc8.groupby('component')['contribution'].mean()
hc_q=hc8[hc8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)
hh_growth_comment=(f"<p>Household consumption grew {bold(hh_now)} in {hi(q)} ({'up' if hh_now>=hh_prev else 'down'} from {bold(hh_prev)}).</p>"
    +f"<p><strong>Top components:</strong></p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(hh_avg.get(s,0)))}</p>" for s,v in hh_q.head(3).items())
    +(f"<p>Contracting: {hi(', '.join(hh_neg))}.</p>" if hh_neg else ""))
hh_contrib_comment=(f"<p>Contributions to HH consumption in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v,' pp',sign=True)} — {vs_avg(v,float(hc_avg.get(s,0)),' pp')}</p>" for s,v in hc_q.head(3).items())
    +(f"<p>Drag: {hi(', '.join([c for c in hc_q.index if hc_q[c]<0]))}.</p>" if any(hc_q<0) else ""))

gf8=gfcf_growth[gfcf_growth['period'].isin(g8['period'].tolist())&(gfcf_growth['component']!='GFCF Total')]
gf_avg=gf8.groupby('component')['yoy'].mean()
gf_q=gf8[gf8['period']==q].set_index('component')['yoy'].sort_values(ascending=False)
gf_neg=[c for c in gf_q.index if gf_q[c]<0]
gf_now=round(float(gfcf_yoy_series.get(q,0)),2); gf_prev=round(float(gfcf_yoy_series.get(g8.iloc[-2]['period'],0)),2)
gc8=gfcf_contrib[gfcf_contrib['period'].isin(g8['period'].tolist())]
gc_avg=gc8.groupby('component')['contribution'].mean()
gc_q=gc8[gc8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)
gfcf_growth_comment=(f"<p>GFCF grew {bold(gf_now)} in {hi(q)} ({'up' if gf_now>=gf_prev else 'down'} from {bold(gf_prev)}).</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v)} — {vs_avg(v,float(gf_avg.get(s,0)))}</p>" for s,v in gf_q.head(3).items())
    +(f"<p>Contracting: {hi(', '.join(gf_neg))}.</p>" if gf_neg else ""))
gfcf_contrib_comment=(f"<p>Contributions to GFCF growth in {hi(q)}:</p>"
    +"".join(f"<p>· {hi(s)}: {bold(v,' pp',sign=True)} — {vs_avg(v,float(gc_avg.get(s,0)),' pp')}</p>" for s,v in gc_q.head(3).items())
    +(f"<p>Drag: {hi(', '.join([c for c in gc_q.index if gc_q[c]<0]))}.</p>" if any(gc_q<0) else ""))

commentaries = {
    'gdp':gdp_comment,'expGrowth':exp_growth_comment,'expContrib':exp_contrib_comment,
    'hhGrowth':hh_growth_comment,'hhContrib':hh_contrib_comment,
    'gfcfGrowth':gfcf_growth_comment,'gfcfContrib':gfcf_contrib_comment,
    'secGrowth':sec_growth_comment,'secContrib':sec_contrib_comment,
    'mfgGrowth':mfg_growth_comment,'mfgContrib':mfg_contrib_comment,
}

def snap_cmt_overview():
    top2=ec_q.head(2); drag=[c for c in ec_q.index if ec_q[c]<0]
    s=(f"<p>GDP grew {bold(g_now)} YoY in {hi(q)}, {'up' if g_swing>=0 else 'down'} {bold(abs(g_swing),sign=False)} pp "
       f"from the prior quarter and {vs_avg(g_now,g_avg8)}.</p>"
       f"<p><strong>Main demand drivers:</strong> "+", ".join(f"{hi(c)} ({bold(v,' pp',sign=True)})" for c,v in top2.items())+".</p>")
    s+=(f"<p><strong>Drag:</strong> "+", ".join(f"{hi(c)} ({bold(ec_q[c],' pp',sign=True)})" for c in drag)+".</p>") if drag else "<p>No demand component in negative territory.</p>"
    return s
def snap_cmt_hh():
    hh8_avg=round(float(hh_yoy_series.reindex(g8['period'].tolist()).mean()),2)
    return (f"<p>HH consumption {bold(hh_now)} in {hi(q)}, {vs_avg(hh_now,hh8_avg)}.</p>"
        f"<p><strong>Fastest:</strong> {hi(hh_q.index[0])} {bold(hh_q.iloc[0])} (contrib {bold(float(hc_q.get(hh_q.index[0],0)),' pp',sign=True)}).</p>"
        f"<p><strong>Slowest:</strong> {hi(hh_q.index[-1])} {bold(hh_q.iloc[-1])}.</p>"
        +(f"<p>Contracting: {hi(', '.join([c for c in hh_q.index if hh_q[c]<0]))}.</p>" if any(hh_q<0) else "")
        +f"<p>Top contributor: {hi(hc_q.index[0])} {bold(hc_q.iloc[0],' pp',sign=True)}.</p>")
def snap_cmt_gfcf():
    gf8_avg=round(float(gfcf_yoy_series.reindex(g8['period'].tolist()).mean()),2)
    return (f"<p>GFCF {bold(gf_now)} in {hi(q)}, {vs_avg(gf_now,gf8_avg)}.</p>"
        f"<p><strong>Fastest:</strong> {hi(gf_q.index[0])} {bold(gf_q.iloc[0])}.</p>"
        f"<p><strong>Slowest:</strong> {hi(gf_q.index[-1])} {bold(gf_q.iloc[-1])}.</p>"
        +(f"<p>Contracting: {hi(', '.join(gf_neg))}.</p>" if gf_neg else "")
        +f"<p>Top contributor: {hi(gc_q.index[0])} {bold(gc_q.iloc[0],' pp',sign=True)}.</p>")
def snap_cmt_sectors():
    n_pos=sum(1 for v in sg_q.values if v>=0); n_neg=sum(1 for v in sg_q.values if v<0)
    mfg_rank=list(sg_q.index).index('Manufacturing')+1 if 'Manufacturing' in sg_q.index else None
    return (f"<p>In {hi(q)}, {n_pos}/17 sectors grew; {n_neg} contracted.</p>"
        f"<p><strong>Top 3:</strong> "+", ".join(f"{hi(sg_q.index[i])} ({bold(sg_q.iloc[i])})" for i in range(3))+".</p>"
        +f"<p><strong>Bottom 3:</strong> "+", ".join(f"{hi(sg_q.index[-(i+1)])} ({bold(sg_q.iloc[-(i+1)])})" for i in range(3))+".</p>"
        +(f"<p>Manufacturing ranked {mfg_rank}/17 at {bold(round(float(sg_q.get('Manufacturing',0)),2))}.</p>" if mfg_rank else "")
        +f"<p>Top GDP contributor: {hi(sc_q.index[0])} ({bold(sc_q.iloc[0],' pp',sign=True)}).</p>")
def snap_cmt_mfg():
    mfg8_avg=round(float(mfg_yoy_series.reindex(g8['period'].tolist()).mean()),2)
    n_pos=sum(1 for v in mg_q.values if v>=0); n_neg=sum(1 for v in mg_q.values if v<0)
    return (f"<p>Manufacturing {bold(mfg_now)} in {hi(q)}, {vs_avg(mfg_now,mfg8_avg)}.</p>"
        f"<p>{n_pos}/16 subsectors grew; {n_neg} contracted.</p>"
        f"<p><strong>Top 3:</strong> "+", ".join(f"{hi(mg_q.index[i])} ({bold(mg_q.iloc[i])})" for i in range(3))+".</p>"
        +f"<p>Top contributor: {hi(mc_q.index[0])} ({bold(mc_q.iloc[0],' pp',sign=True)}).</p>")

snap_comments={'overview':snap_cmt_overview(),'hh':snap_cmt_hh(),'gfcf':snap_cmt_gfcf(),'sectors':snap_cmt_sectors(),'mfg':snap_cmt_mfg()}

def pivot(df,gc,vc):
    ps=sorted(df['period'].unique()); out={}
    for name,grp in df.groupby(gc,sort=False):
        s=grp.set_index('period')[vc]; out[name]=[round(float(s.get(p,0) or 0),3) for p in ps]
    return ps,out

exp_g_periods,exp_g_data=pivot(exp_growth,'component','yoy')
exp_c_periods,exp_c_data=pivot(exp_contrib,'component','contribution')
hh_g_periods,hh_g_data=pivot(hh_growth,'component','yoy')
hh_c_periods,hh_c_data=pivot(hh_contrib,'component','contribution')
gfcf_g_periods,gfcf_g_data=pivot(gfcf_growth,'component','yoy')
gfcf_c_periods,gfcf_c_data=pivot(gfcf_contrib,'component','contribution')
sec_g_periods,sec_g_data=pivot(sec_growth,'sector','yoy')
sec_c_periods,sec_c_data=pivot(sec_contrib,'sector','contribution')
mfg_g_periods,mfg_g_data=pivot(mfg_growth,'subsector','yoy')
mfg_c_periods,mfg_c_data=pivot(mfg_contrib,'subsector','contribution')

TOTAL_KEYS={'Household Total','GFCF Total','GDP','Manufacturing Total'}
def snap_sort(dd):
    lat={k:round(float(v[-1] or 0),2) for k,v in dd.items()}
    tots=[(k,v) for k,v in lat.items() if k in TOTAL_KEYS]
    oth=sorted([(k,v) for k,v in lat.items() if k not in TOTAL_KEYS],key=lambda x:x[1],reverse=True)
    items=tots+oth
    return {'labels':[x[0] for x in items],'values':[x[1] for x in items],'total_label':tots[0][0] if tots else None}
def snap_fixed(dd,order):
    lat={k:round(float(v[-1] or 0),2) for k,v in dd.items()}
    items=[(k,lat[k]) for k in order if k in lat]+[(k,v) for k,v in lat.items() if k not in order]
    return {'labels':[x[0] for x in items],'values':[x[1] for x in items],
            'total_label':next((k for k in order if k in TOTAL_KEYS and k in lat),None)}

EXP_ORDER=['GDP','Household Consumption','Investment (PMTB)','Government','Exports (Goods)','Imports (Goods)']
EXP_ORDER_C=['Household Consumption','Investment (PMTB)','Government','Exports (Goods)','Imports (Goods)']
snap={'period':latest_period,'gdp_yoy':latest_yoy,'gdp_avg8':round(float(sum(yoy_vals[-8:])/min(8,len(yoy_vals))),2),
      'exp_growth':snap_fixed(exp_g_data,EXP_ORDER),'exp_contrib':snap_fixed(exp_c_data,EXP_ORDER_C),
      'hh_growth':snap_sort(hh_g_data),'hh_contrib':snap_sort(hh_c_data),
      'gfcf_growth':snap_sort(gfcf_g_data),'gfcf_contrib':snap_sort(gfcf_c_data),
      'sec_growth':snap_sort(sec_g_data),'sec_contrib':snap_sort(sec_c_data),
      'mfg_growth':snap_sort(mfg_g_data),'mfg_contrib':snap_sort(mfg_c_data),'comments':snap_comments}

gdp_js=json.dumps({'periods':periods,'yoy':yoy_vals,'precovid_mean':precovid_mean,
    'exp_g_periods':exp_g_periods,'exp_g_data':exp_g_data,'exp_c_periods':exp_c_periods,'exp_c_data':exp_c_data,
    'hh_g_periods':hh_g_periods,'hh_g_data':hh_g_data,'hh_c_periods':hh_c_periods,'hh_c_data':hh_c_data,
    'gfcf_g_periods':gfcf_g_periods,'gfcf_g_data':gfcf_g_data,'gfcf_c_periods':gfcf_c_periods,'gfcf_c_data':gfcf_c_data,
    'sec_g_periods':sec_g_periods,'sec_g_data':sec_g_data,'sec_c_periods':sec_c_periods,'sec_c_data':sec_c_data,
    'mfg_g_periods':mfg_g_periods,'mfg_g_data':mfg_g_data,'mfg_c_periods':mfg_c_periods,'mfg_c_data':mfg_c_data,
    'latest_period':latest_period,'latest_yoy':latest_yoy,'prev_yoy':prev_yoy,'delta':delta,
    'comments':commentaries,'snap':snap})

EXP_COLORS={'GDP':'#1a1814','Household Consumption':'#2563eb','Government':'#16a34a','Investment (PMTB)':'#d97706','Exports (Goods)':'#7c3aed','Imports (Goods)':'#dc2626'}
SEC_COLORS={'Agriculture':'#15803d','Mining & Quarrying':'#92400e','Manufacturing':'#ea580c','Electricity & Gas':'#ca8a04','Water & Waste':'#4d7c0f','Construction':'#0e7490','Trade':'#2563eb','Transport & Storage':'#7c3aed','Accommodation & Food':'#be185d','Info & Comms':'#0891b2','Finance & Insurance':'#db2777','Real Estate':'#9333ea','Business Services':'#0369a1','Government Admin':'#374151','Education':'#065f46','Health & Social':'#991b1b','Other Services':'#6b7280'}
MFG_COLORS={'Food & Beverages':'#15803d','Tobacco':'#374151','Textiles & Apparel':'#be185d','Leather & Footwear':'#92400e','Wood Products':'#4d7c0f','Paper & Printing':'#0369a1','Coal & Oil Refining':'#1a1814','Chemicals & Pharma':'#7c3aed','Rubber & Plastics':'#0e7490','Non-metallic Minerals':'#b45309','Basic Metals':'#6b7280','Metal Products & Electronics':'#2563eb','Machinery':'#0891b2','Transport Equipment':'#ea580c','Furniture':'#9333ea','Other Manufacturing':'#db2777'}
HH_COLORS={'Household Total':'#1a1814','Food & Beverages':'#15803d','Apparel & Footwear':'#be185d','Household Equipment':'#d97706','Health & Education':'#7c3aed','Transport & Comms':'#2563eb','Restaurant & Hotel':'#ea580c','Other Consumption':'#6b7280'}
GFCF_COLORS={'GFCF Total':'#1a1814','Buildings & Structures':'#0e7490','Machine & Equipment':'#ea580c','Vehicles':'#ca8a04','Other Equipment':'#6b7280','Biological Resources':'#15803d','Intellectual Property':'#7c3aed'}

print(f"GDP: {latest_period}, YoY {latest_yoy:+.2f}%")

# ══════════════════════════════════════════════════════════════════════════════
# PART 2 · BOP DATA
# ══════════════════════════════════════════════════════════════════════════════
wb = xlrd.open_workbook(os.path.join(r"C:\work\economist\rawdata\seki", "TABEL5_1.xls"))
sh = wb.sheet_by_name("5.1")

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
BOP_PERIODS = [p for p,_ in BOP_Q]
BN = len(BOP_PERIODS)

def bq(xls_row):
    vals=[]
    for _,c in BOP_Q:
        if sh.cell_type(xls_row,c)==xlrd.XL_CELL_EMPTY: vals.append(None)
        else:
            v=sh.cell_value(xls_row,c)
            vals.append(round(float(v),2) if isinstance(v,(int,float)) else None)
    return vals

bca=bq(6); bka=bq(31); bfa=bq(34); berr=bq(52); bbal=bq(53); bres_pos=bq(59); bres_months=bq(60)
# Negate VII so sign matches position direction: positive = accumulation, negative = drawdown
bres=[-v if v is not None else None for v in bq(54)]
bka_fa=[round((bka[i] or 0)+(bfa[i] or 0),2) if (bka[i] is not None or bfa[i] is not None) else None for i in range(BN)]
bca_goods=bq(7); bca_svcs=bq(22); bca_primary=bq(25); bca_second=bq(28)
bfa_di=bq(37); bfa_pi=bq(40); bfa_der=bq(45); bfa_oi=bq(46)

bli=max(i for i,v in enumerate(bca) if v is not None)
blp=BOP_PERIODS[bli]
bt8=slice(max(0,bli-7),bli+1)
def bavg8(s): vals=[v for v in s[bt8] if v is not None]; return round(sum(vals)/len(vals),2) if vals else None

bca_now=bca[bli]; bca_avg=bavg8(bca); bkafa_now=bka_fa[bli]; bkafa_avg=bavg8(bka_fa)
bbal_now=bbal[bli]; bres_now=bres[bli]; bresp_now=bres_pos[bli]
bca_prev=bca[bli-1] if bli>0 else None

def bhi(t): return f'<em>{t}</em>'
bca_cmt=(f"<p>CA: <strong>{bca_now:+,.0f} USD mn</strong> in {bhi(blp)}, "
    +("improving" if bca_prev and bca_now>bca_prev else "widening" if bca_prev and bca_now<bca_prev else "unchanged")
    +f" from {bca_prev:+,.0f} prior quarter.</p>"
    f"<p>Reading is {'above' if bca_now>=bca_avg else 'below'} its 8Q avg ({bca_avg:+,.0f}) by <strong>{abs(bca_now-bca_avg):.0f}</strong> USD mn.</p>"
    f"<p>Goods <strong>{bca_goods[bli]:+,.0f}</strong> · Services <strong>{bca_svcs[bli]:+,.0f}</strong> · "
    f"Primary income <strong>{bca_primary[bli]:+,.0f}</strong> · Secondary income <strong>{bca_second[bli]:+,.0f}</strong>.</p>")
bfa_now=bfa[bli]
bfa_cmt=(f"<p>FA: <strong>{bfa_now:+,.0f} USD mn</strong> in {bhi(blp)} ({'net inflow' if bfa_now>=0 else 'net outflow'}).</p>"
    f"<p>KA+FA combined: <strong>{bkafa_now:+,.0f}</strong>, {'above' if bkafa_now>=bkafa_avg else 'below'} 8Q avg ({bkafa_avg:+,.0f}) by <strong>{abs(bkafa_now-bkafa_avg):.0f}</strong>.</p>"
    f"<p>DI <strong>{bfa_di[bli]:+,.0f}</strong> · Portfolio <strong>{bfa_pi[bli]:+,.0f}</strong> · "
    f"Other <strong>{bfa_oi[bli]:+,.0f}</strong> · Derivatives <strong>{bfa_der[bli]:+,.0f}</strong>.</p>")
bres_months_now = bres_months[bli]
bres_cmt=(f"<p>Reserve change: <strong>{bres_now:+,.0f} USD mn</strong> in {bhi(blp)}.</p>"
    f"<p>{'Accumulation (positive = build-up)' if bres_now>0 else 'Draw-down (negative = reserves fell)'}.</p>"
    +(f"<p>End-period position: <strong>{bresp_now/1000:,.1f} USD bn</strong>.</p>" if bresp_now else "")
    +(f"<p>Import coverage: <strong>{bres_months_now:.2f} months</strong>.</p>" if bres_months_now else ""))

bop_js=json.dumps({'periods':BOP_PERIODS,
    'ca':bca,'ka_fa':bka_fa,'errors':berr,'balance':bbal,'res':bres,'res_pos':bres_pos,
    'res_months':bres_months,
    'ca_goods':bca_goods,'ca_svcs':bca_svcs,'ca_primary':bca_primary,'ca_second':bca_second,
    'fa':bfa,'fa_di':bfa_di,'fa_pi':bfa_pi,'fa_der':bfa_der,'fa_oi':bfa_oi})

print(f"BOP: {blp}, CA {bca_now:+,.0f}  KA+FA {bkafa_now:+,.0f}  Balance {bbal_now:+,.0f}")

# ══════════════════════════════════════════════════════════════════════════════
# PART 3 · FINANCIAL DATA
# ══════════════════════════════════════════════════════════════════════════════
FIN_DIR = r"C:\work\economist\rawdata\financial"

def _load_fin(key):
    p = os.path.join(FIN_DIR, f"financial_{key}.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"fx": {}, "equity": {}, "fetched_at": None, "window_label": key}

fin_3y = _load_fin("3y")
fin_1m = _load_fin("1m")
fin_1w = _load_fin("1w")
fin_fetched = (fin_3y.get("fetched_at") or "not yet fetched")[:16].replace("T", " ")
fin_js = json.dumps({"3y": fin_3y, "1m": fin_1m, "1w": fin_1w})

# ══════════════════════════════════════════════════════════════════════════════
# PART 4 · HTML
# ══════════════════════════════════════════════════════════════════════════════
with open(os.path.join(os.path.dirname(__file__), '_combined_template.py'), 'w') as _: pass  # sentinel

def write_html():
    # read template pieces from separate file to avoid single f-string size limit
    pass

# Write HTML directly
out_path = os.path.join(HTML, "econdashboard.html")

# Build in parts to keep each f-string manageable
HEAD = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indonesia Economic Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1814;--ink-light:#4a4740;--ink-faint:#8a8780;--paper:#f5f2ec;--paper-warm:#ede9e0;--paper-card:#faf8f4;--rule:#d8d3c8;--accent:#b5460f;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:300;font-size:15px;line-height:1.7;}}
/* ── Main nav ── */
#mainNav{{background:#1a1814;border-bottom:3px solid var(--accent);position:sticky;top:0;z-index:100;}}
.mn-brand-row{{padding:.6rem 2rem .4rem;text-align:center;}}
.mn-brand{{font-family:'DM Mono',monospace;font-size:13px;color:var(--paper);letter-spacing:.2em;text-transform:uppercase;font-weight:500;}}
.mn-brand em{{font-style:normal;color:var(--accent);margin-right:.6em;}}
.mn-tabs-row{{padding:.3rem 2rem .5rem;display:flex;gap:3px;justify-content:center;}}
.mn-tab{{font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase;
          padding:5px 20px;border-radius:3px;cursor:pointer;border:none;background:transparent;
          color:rgba(245,242,236,.45);transition:all .15s;}}
.mn-tab:hover{{color:var(--paper);background:rgba(255,255,255,.08);}}
.mn-tab.active{{background:var(--accent);color:var(--paper);}}
.mn-tab.disabled{{color:rgba(245,242,236,.18);cursor:default;pointer-events:none;}}
/* ── Shared header ── */
header{{background:var(--ink);color:var(--paper);padding:2.5rem 3rem 2rem;text-align:center;}}
.header-label{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
header h1{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:400;line-height:1.2;margin-bottom:1rem;}}
header h1 em{{font-style:italic;color:rgba(245,242,236,.6);}}
.header-meta{{display:flex;gap:2rem;flex-wrap:wrap;justify-content:center;}}
.hm{{font-family:'DM Mono',monospace;font-size:11px;color:rgba(245,242,236,.5);letter-spacing:.08em;}}
.hm span{{color:rgba(245,242,236,.9);display:block;font-size:13px;margin-top:2px;}}
/* ── Window bar ── */
.window-bar{{position:sticky;top:78px;z-index:50;background:var(--paper-warm);border-bottom:1px solid var(--rule);padding:.5rem 2rem .6rem;display:flex;flex-direction:column;align-items:center;gap:.35rem;}}
.window-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);}}
.window-btns{{display:flex;gap:4px;}}
.wbtn{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;padding:4px 14px;border-radius:2px;cursor:pointer;border:1px solid var(--rule);background:var(--paper-card);color:var(--ink-light);transition:all .15s;}}
.wbtn:hover{{background:var(--paper-warm);border-color:var(--ink-faint);color:var(--ink);}}
.wbtn.active{{background:var(--ink);border-color:var(--ink);color:var(--paper);font-weight:500;}}
/* ── Layout ── */
.container{{max-width:1200px;margin:0 auto;padding:2rem 2rem 5rem;}}
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:4px;overflow:hidden;margin-bottom:2.5rem;}}
.kpi{{background:var(--paper-card);padding:1.25rem 1.5rem;}}
.kpi-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.4rem;}}
.kpi-value{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:400;}}
.kpi-value.pos{{color:#2d5a27;}}.kpi-value.neg{{color:#b5460f;}}
.kpi-sub{{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);margin-top:.3rem;}}
.block{{margin-bottom:3rem;}}
.block-header{{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}}
.block-num{{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}}
.block-title{{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}}
.chart-wrap,.chart-full{{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.5rem;}}
.chart-wrap h3,.chart-full h3{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:1rem;}}
.chart-note{{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);margin-top:.75rem;}}
.fin-data-note{{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);letter-spacing:.05em;padding:.5rem 0 1rem;text-align:center;}}
.fin-data-note strong{{color:var(--ink-light);}} .fin-data-note code{{background:var(--paper-warm);padding:1px 5px;border-radius:2px;}}
.chart-with-comment{{display:flex;gap:1.5rem;align-items:flex-start;}}
.chart-with-comment .chart-full,.chart-with-comment .chart-wrap{{flex:1;min-width:0;}}
/* GDP time-series comment boxes always visible */
#gdpTabTS .comment-box{{display:block;}}
/* BOP comment boxes always visible */
#sectionBOP .comment-box{{display:block;}}
.comment-box{{width:260px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}}
.comment-box .cb-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
.comment-box p{{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}}
.comment-box p:last-child{{margin-bottom:0;}}
.comment-box strong{{color:var(--ink);font-weight:500;}}.comment-box em{{font-style:normal;color:var(--ink);font-weight:500;}}
/* Snapshot */
.snap-group{{margin-bottom:3rem;}}.snap-group-header{{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}}
.snap-group-num{{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}}
.snap-group-title{{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}}
.snap-body{{display:flex;gap:1.5rem;align-items:flex-start;}}
.snap-comment{{width:260px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}}
.snap-comment .cb-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
.snap-comment p{{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}}
.snap-comment strong{{color:var(--ink);font-weight:500;}}.snap-comment em{{font-style:normal;color:var(--ink);font-weight:500;}}
.snap-charts{{flex:1;min-width:0;display:flex;flex-direction:column;gap:1.25rem;}}
.snap-chart-wrap{{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.25rem;}}
.snap-chart-wrap h3{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.75rem;}}
/* BOP KPI delta */
.kpi-delta{{font-family:'DM Mono',monospace;font-size:11px;margin-top:.2rem;}}
.kpi-delta.pos{{color:#2d5a27;}}.kpi-delta.neg{{color:#b5460f;}}
footer{{background:var(--paper-warm);border-top:1px solid var(--rule);padding:1.25rem 3rem;font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;}}
@media(max-width:900px){{
  .chart-with-comment,.snap-body{{flex-direction:column;}}
  .comment-box,.snap-comment{{width:100%;}}
  .kpi-row{{grid-template-columns:repeat(2,1fr);}}
  header{{padding:2rem 1.5rem;}}
}}
</style>
</head>
<body>
"""

NAV = f"""
<div id="mainNav">
  <div class="mn-brand-row">
    <span class="mn-brand"><em>AAY</em>Indonesia Economic Dashboard</span>
  </div>
  <div class="mn-tabs-row">
    <button id="navGDP" class="mn-tab active" onclick="showSection('gdp')">GDP</button>
    <button id="navBOP" class="mn-tab" onclick="showSection('bop')">BoP</button>
    <button id="navFin" class="mn-tab" onclick="showSection('fin')">Financial</button>
    <button class="mn-tab disabled">Prices</button>
    <button class="mn-tab disabled">Fiscal</button>
  </div>
</div>
"""

GDP_SECTION = f"""
<div id="sectionGDP">

<header>
  <div class="header-label">Real Sector — National Accounts</div>
  <h1>Gross Domestic Product and Its Determinants</h1>
</header>

<div class="window-bar">
  <span class="window-label">Analytical window</span>
  <div class="window-btns">
    <button class="wbtn" onclick="setGDPWindow('snap')" id="gdpBtnSnap" style="border-right:2px solid var(--rule);margin-right:4px;padding-right:16px;">Latest Quarter · {latest_period}</button>
    <button class="wbtn" onclick="setGDPWindow(8)" id="gdpBtn2y">Short · 2Y</button>
    <button class="wbtn" onclick="setGDPWindow(16)" id="gdpBtn4y">Medium · 4Y</button>
    <button class="wbtn active" onclick="setGDPWindow(0)" id="gdpBtnAll">All · {periods[0]}–{periods[-1]}</button>
  </div>
</div>

<div id="gdpTabTS">
<div class="container">

  <div class="kpi-row" style="margin-top:1.5rem;">
    <div class="kpi"><div class="kpi-label">Latest GDP Growth</div>
      <div class="kpi-value {'pos' if latest_yoy>=0 else 'neg'}">{latest_yoy:+.2f}%</div>
      <div class="kpi-sub">{latest_period} · YoY</div></div>
    <div class="kpi"><div class="kpi-label">Previous Quarter</div>
      <div class="kpi-value {'pos' if prev_yoy>=0 else 'neg'}">{prev_yoy:+.2f}%</div>
      <div class="kpi-sub">One quarter prior · YoY</div></div>
    <div class="kpi"><div class="kpi-label">Change vs Prior Q</div>
      <div class="kpi-value {'pos' if delta>=0 else 'neg'}">{delta:+.2f} pp</div>
      <div class="kpi-sub">Percentage points</div></div>
    <div class="kpi"><div class="kpi-label">Pre-COVID Mean</div>
      <div class="kpi-value">{precovid_mean:.2f}%</div>
      <div class="kpi-sub">2015 Q1 – 2019 Q4</div></div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">01</span><h2 class="block-title">Headline GDP Growth</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full"><h3>YoY Growth (%)</h3>
        <div style="position:relative;height:280px"><canvas id="chartGDP"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Dashed = 2015–2019 pre-COVID mean ({precovid_mean:.2f}%). Source: SEKI 7.2, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGDPtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02</span><h2 class="block-title">Demand Components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Component (%)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: SEKI 7.4, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtExpGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Imports sign-reversed. Source: SEKI 7.4, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtExpContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02b</span><h2 class="block-title">Household Consumption — Sub-components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: CEIC, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtHhGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to Household Consumption Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: CEIC, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtHhContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02c</span><h2 class="block-title">Gross Fixed Capital Formation — Sub-components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: CEIC, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGfcfGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GFCF Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: CEIC, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGfcfContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">03</span><h2 class="block-title">Supply — Sectoral (17 sectors)</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Sector (%)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: SEKI 7.2, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtSecGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: SEKI 7.2, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtSecContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">04</span><h2 class="block-title">Manufacturing — Subsector Drill-down</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Subsector (%)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgGrowth"></canvas></div>
        <div class="chart-note">16 subsectors, quarterly YoY, constant 2010 prices. Source: SEKI 7.2, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtMfgGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to Manufacturing Growth (pp)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: SEKI 7.2, BPS.</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtMfgContribtext"></div></div>
    </div>
  </div>

</div></div>

<!-- Snapshot tab -->
<div id="gdpTabSnap" style="display:none">
<div class="container" style="padding-top:2rem">
  <div class="snap-group"><div class="snap-group-header"><span class="snap-group-num">01</span><h2 class="snap-group-title">Economy Overview</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {latest_period}</div><div id="snapCmtOverview"></div></div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>Demand Component YoY Growth (%)</h3><div style="position:relative;height:220px"><canvas id="snapExpGrowth"></canvas></div></div>
        <div class="snap-chart-wrap"><h3>Demand Component Contributions (pp)</h3><div style="position:relative;height:220px"><canvas id="snapExpContrib"></canvas></div></div>
      </div>
    </div>
  </div>
  <div class="snap-group"><div class="snap-group-header"><span class="snap-group-num">02</span><h2 class="snap-group-title">Household Consumption</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {latest_period}</div><div id="snapCmtHh"></div></div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>YoY Growth by Component (%)</h3><div style="position:relative;height:260px"><canvas id="snapHhGrowth"></canvas></div></div>
        <div class="snap-chart-wrap"><h3>Contribution to HH Consumption Growth (pp)</h3><div style="position:relative;height:230px"><canvas id="snapHhContrib"></canvas></div></div>
      </div>
    </div>
  </div>
  <div class="snap-group"><div class="snap-group-header"><span class="snap-group-num">03</span><h2 class="snap-group-title">Gross Fixed Capital Formation</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {latest_period}</div><div id="snapCmtGfcf"></div></div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>YoY Growth by Component (%)</h3><div style="position:relative;height:235px"><canvas id="snapGfcfGrowth"></canvas></div></div>
        <div class="snap-chart-wrap"><h3>Contribution to GFCF Growth (pp)</h3><div style="position:relative;height:210px"><canvas id="snapGfcfContrib"></canvas></div></div>
      </div>
    </div>
  </div>
  <div class="snap-group"><div class="snap-group-header"><span class="snap-group-num">04</span><h2 class="snap-group-title">Production — All Sectors</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {latest_period}</div><div id="snapCmtSectors"></div></div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>YoY Growth by Sector (%)</h3><div style="position:relative;height:490px"><canvas id="snapSecGrowth"></canvas></div></div>
        <div class="snap-chart-wrap"><h3>Contribution to GDP Growth (pp)</h3><div style="position:relative;height:490px"><canvas id="snapSecContrib"></canvas></div></div>
      </div>
    </div>
  </div>
  <div class="snap-group"><div class="snap-group-header"><span class="snap-group-num">05</span><h2 class="snap-group-title">Manufacturing Drill-down</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {latest_period}</div><div id="snapCmtMfg"></div></div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>YoY Growth by Sub-sector (%)</h3><div style="position:relative;height:470px"><canvas id="snapMfgGrowth"></canvas></div></div>
        <div class="snap-chart-wrap"><h3>Contribution to Manufacturing Growth (pp)</h3><div style="position:relative;height:470px"><canvas id="snapMfgContrib"></canvas></div></div>
      </div>
    </div>
  </div>
</div>
</div>

</div><!-- /sectionGDP -->
"""

# ── BOP snapshot commentaries ─────────────────────────────────────────────────
bop_sc1 = (
    f"<p>Overall balance: <strong>{bbal_now:+,.0f} USD mn</strong> in {bhi(blp)}.</p>"
    f"<p>CA {'surplus' if bca_now>=0 else 'deficit'} of <strong>{bca_now:+,.0f}</strong>; "
    f"KA+FA: <strong>{bkafa_now:+,.0f}</strong>.</p>"
    f"<p>Net errors &amp; omissions: <strong>{berr[bli]:+,.0f}</strong> USD mn.</p>"
)
bop_sc2 = (
    f"<p>CA: <strong>{bca_now:+,.0f} USD mn</strong>.</p>"
    f"<p>Goods: <strong>{bca_goods[bli]:+,.0f}</strong> · "
    f"Services: <strong>{bca_svcs[bli]:+,.0f}</strong>.</p>"
    f"<p>Primary income: <strong>{bca_primary[bli]:+,.0f}</strong> · "
    f"Secondary income: <strong>{bca_second[bli]:+,.0f}</strong>.</p>"
    f"<p>{'Goods surplus supports' if bca_goods[bli]>0 else 'Goods deficit drags'} the CA; "
    f"services and primary income {'add drag' if bca_svcs[bli]<0 and bca_primary[bli]<0 else 'mixed'}.</p>"
)
bop_sc3 = (
    f"<p>FA: <strong>{bfa_now:+,.0f} USD mn</strong> ({'net inflow' if bfa_now>=0 else 'net outflow'}) in {bhi(blp)}.</p>"
    f"<p>Direct Investment: <strong>{bfa_di[bli]:+,.0f}</strong> · "
    f"Portfolio: <strong>{bfa_pi[bli]:+,.0f}</strong>.</p>"
    f"<p>Other Investment: <strong>{bfa_oi[bli]:+,.0f}</strong> · "
    f"Derivatives: <strong>{bfa_der[bli]:+,.0f}</strong>.</p>"
)
bop_sc4 = (
    f"<p>Reserve change: <strong>{bres_now:+,.0f} USD mn</strong> in {bhi(blp)}.</p>"
    f"<p>{'Accumulation — reserves increased.' if bres_now>0 else 'Draw-down — reserves fell.'}</p>"
    +(f"<p>End-period position: <strong>{bresp_now/1000:,.1f} USD bn</strong>.</p>" if bresp_now else "")
    +(f"<p>Import coverage: <strong>{bres_months_now:.2f} months</strong>.</p>" if bres_months_now else "")
)

BOP_SECTION = f"""
<div id="sectionBOP" style="display:none">

<header>
  <div class="header-label">External Sector — Balance of Payments</div>
  <h1>Balance of Payments and Its Components</h1>
</header>

<div class="window-bar">
  <span class="window-label">Analytical window</span>
  <div class="window-btns">
    <button class="wbtn" onclick="setBOPWindow('snap')" id="bopBtnSnap" style="border-right:2px solid var(--rule);margin-right:4px;padding-right:16px;">Latest Quarter · {blp}</button>
    <button class="wbtn active" id="bopBtn2y" onclick="setBOPWindow(8)">Short · 2Y</button>
    <button class="wbtn" id="bopBtn4y" onclick="setBOPWindow(16)">Medium · 4Y</button>
    <button class="wbtn" id="bopBtnAll" onclick="setBOPWindow(0)">All · 2010–{blp}</button>
  </div>
</div>

<div id="bopTabTS">
<div class="container">
  <div class="kpi-row" style="margin-top:1.5rem;">
    <div class="kpi"><div class="kpi-label">Current Account</div>
      <div class="kpi-value {'pos' if bca_now>=0 else 'neg'}">{bca_now:+,.0f}</div>
      <div class="kpi-sub">{blp} · USD mn</div>
      <div class="kpi-delta {'pos' if bca_now>=bca_avg else 'neg'}">8Q avg {bca_avg:+,.0f}</div></div>
    <div class="kpi"><div class="kpi-label">Capital + Financial Account</div>
      <div class="kpi-value {'pos' if bkafa_now>=0 else 'neg'}">{bkafa_now:+,.0f}</div>
      <div class="kpi-sub">{blp} · USD mn</div>
      <div class="kpi-delta {'pos' if bkafa_now>=bkafa_avg else 'neg'}">8Q avg {bkafa_avg:+,.0f}</div></div>
    <div class="kpi"><div class="kpi-label">Overall Balance</div>
      <div class="kpi-value {'pos' if bbal_now>=0 else 'neg'}">{bbal_now:+,.0f}</div>
      <div class="kpi-sub">{blp} · USD mn</div>
      <div class="kpi-sub">VI. Neraca Keseluruhan</div></div>
    <div class="kpi"><div class="kpi-label">Reserve Position</div>
      <div class="kpi-value">{f'{bresp_now/1000:,.1f}' if bresp_now else '—'}</div>
      <div class="kpi-sub">{blp} · USD bn end-period</div>
      <div class="kpi-sub">Change: {bres_now:+,.0f} mn {'(build-up)' if bres_now>0 else '(draw-down)'}</div></div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">01</span><h2 class="block-title">BOP Overview — CA, Capital+Financial, Overall Balance</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full"><h3>Quarterly flows · USD million</h3>
        <div style="position:relative;height:320px"><canvas id="bopChartBOP"></canvas></div>
        <div class="chart-note">Quarterly, USD million. CA = I. Transaksi Berjalan. KA+FA = II+III. Balance = VI. Neraca Keseluruhan. Source: SEKI 5.1, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt01label"></div><div id="bopCmt01"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02</span><h2 class="block-title">Current Account — Components</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full"><h3>Stacked quarterly flows · USD million</h3>
        <div style="position:relative;height:320px"><canvas id="bopChartCA"></canvas></div>
        <div class="chart-note">Quarterly, USD million. A. Goods · B. Services · C. Primary Income · D. Secondary Income. Line = CA total. Source: SEKI 5.1, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt02label"></div><div id="bopCmt02"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">03</span><h2 class="block-title">Financial Account — Components</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full"><h3>Stacked quarterly flows · USD million (positive = net inflow)</h3>
        <div style="position:relative;height:320px"><canvas id="bopChartFA"></canvas></div>
        <div class="chart-note">Quarterly, USD million. 1. Direct Investment · 2. Portfolio · 3. Derivatives · 4. Other Investment. Line = FA total. Source: SEKI 5.1, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt03label"></div><div id="bopCmt03"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">04</span><h2 class="block-title">Reserve Assets</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Quarterly change (left) · End-period level (right)</h3>
        <div style="position:relative;height:220px"><canvas id="bopChartRes"></canvas></div>
        <h3 style="margin-top:1.25rem">Months of Import &amp; Official Debt Coverage</h3>
        <div style="position:relative;height:140px"><canvas id="bopChartMonths"></canvas></div>
        <div class="chart-note">Quarterly, USD million. Sign flipped — positive = accumulation, negative = drawdown. Bottom: months of imports coverage. Source: SEKI 5.1, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt04label"></div><div id="bopCmt04"></div></div>
    </div>
  </div>
</div>
</div><!-- /bopTabTS -->

<div id="bopTabSnap" style="display:none">
<div class="container" style="padding-top:2rem">

  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">01</span><h2 class="snap-group-title">BOP Summary</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {blp}</div>{bop_sc1}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>CA · KA+FA · Net Errors · Overall Balance (USD mn)</h3>
          <div style="position:relative;height:220px"><canvas id="bopSnapBOP"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">02</span><h2 class="snap-group-title">Current Account — Components</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {blp}</div>{bop_sc2}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>CA Components · incl. total for reference (USD mn)</h3>
          <div style="position:relative;height:260px"><canvas id="bopSnapCA"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">03</span><h2 class="snap-group-title">Financial Account — Components</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {blp}</div>{bop_sc3}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>FA Components · incl. total for reference (USD mn)</h3>
          <div style="position:relative;height:260px"><canvas id="bopSnapFA"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">04</span><h2 class="snap-group-title">Reserve Assets</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {blp}</div>{bop_sc4}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>Reserve change (USD mn) — positive = accumulation, negative = draw-down</h3>
          <div style="position:relative;height:160px"><canvas id="bopSnapRes"></canvas></div>
        </div>
      </div>
    </div>
  </div>

</div>
</div><!-- /bopTabSnap -->

</div><!-- /sectionBOP -->
"""

FINANCIAL_SECTION = f"""
<div id="sectionFin" style="display:none">

<header>
  <div class="header-label">Financial Markets</div>
  <h1>Exchange Rate &amp; Stock Market</h1>
</header>

<div class="window-bar">
  <span class="window-label">Analytical window</span>
  <div class="window-btns">
    <button class="wbtn active" id="finBtn3y" onclick="setFinWindow('3y')">3 Years · Monthly</button>
    <button class="wbtn" id="finBtn1m" onclick="setFinWindow('1m')">Last Month · Daily</button>
    <button class="wbtn" id="finBtn1w" onclick="setFinWindow('1w')">Last Week · Hourly</button>
  </div>
</div>

<div class="container">
  <div class="fin-data-note">Data fetched: <strong>{fin_fetched}</strong> · Run <code>python fetch_financial.py</code> then rebuild to update.</div>

  <div class="kpi-row" style="margin-top:1rem;">
    <div class="kpi"><div class="kpi-label">USD/IDR</div>
      <div class="kpi-value" id="finKpiRate">—</div>
      <div class="kpi-sub" id="finKpiRateSub">latest</div></div>
    <div class="kpi"><div class="kpi-label">IDR vs Window Start</div>
      <div class="kpi-value" id="finKpiRateChg">—</div>
      <div class="kpi-sub">+ = depreciation</div></div>
    <div class="kpi"><div class="kpi-label">IHSG</div>
      <div class="kpi-value" id="finKpiIHSG">—</div>
      <div class="kpi-sub" id="finKpiIHSGSub">latest</div></div>
    <div class="kpi"><div class="kpi-label">IHSG vs Window Start</div>
      <div class="kpi-value" id="finKpiIHSGChg">—</div>
      <div class="kpi-sub">+ = appreciation</div></div>
  </div>

  <div class="block">
    <div class="block-header"><span class="block-num">01</span><h2 class="block-title">USD/IDR Exchange Rate</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3 id="finFxH3">—</h3>
        <div style="position:relative;height:300px"><canvas id="chartFinFX"></canvas></div>
        <div class="chart-note">Higher = weaker Rupiah. Source: Yahoo Finance (USDIDR=X).</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="finFxCmtLabel">—</div><div id="cmtFinFXtext"></div></div>
    </div>
  </div>

  <div class="block">
    <div class="block-header"><span class="block-num">02</span><h2 class="block-title">IHSG — Jakarta Composite Index</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3 id="finEqH3">—</h3>
        <div style="position:relative;height:300px"><canvas id="chartFinEQ"></canvas></div>
        <div class="chart-note">Jakarta Composite Index. Source: Yahoo Finance (^JKSE).</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="finEqCmtLabel">—</div><div id="cmtFinEQtext"></div></div>
    </div>
  </div>

</div>
</div><!-- /sectionFin -->
"""

FOOTER = """
<footer>
  <span>Indonesia Economic Dashboard</span>
  <span>Source: SEKI BI, BPS, CEIC, Yahoo Finance</span>
</footer>
"""

JS = f"""
<script>
const D = {gdp_js};
const B = {bop_js};
const FIN = {fin_js};
const EXP_COLORS  = {json.dumps(EXP_COLORS)};
const SEC_COLORS  = {json.dumps(SEC_COLORS)};
const MFG_COLORS  = {json.dumps(MFG_COLORS)};
const HH_COLORS   = {json.dumps(HH_COLORS)};
const GFCF_COLORS = {json.dumps(GFCF_COLORS)};

const MONO = "'DM Mono', monospace";
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.color = '#8a8780';

/* ── Shared helpers ── */
function xAxis() {{
  return {{ticks:{{font:{{family:MONO,size:10}},maxRotation:45,autoSkip:true,maxTicksLimit:12}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function yAxis(title) {{
  return {{title:{{display:true,text:title,font:{{family:MONO,size:10}},color:'#8a8780'}},ticks:{{font:{{family:MONO,size:10}}}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function legend() {{ return {{labels:{{font:{{family:MONO,size:10}},boxWidth:10,padding:10}}}}; }}
function legendRight() {{ return {{position:'right',labels:{{font:{{family:MONO,size:10}},boxWidth:10,padding:10}}}}; }}
function lineDS(label,data,color,opts={{}}) {{
  return {{label,data,borderColor:color,borderWidth:1.8,pointRadius:0,pointHoverRadius:4,tension:0,fill:false,...opts}};
}}
function tooltipFmt(suffix) {{
  return {{itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?ctx.parsed.y.toFixed(2):''}}${{suffix}}`}}}};
}}
function chartOpts(lgd,suffix,yLabel) {{
  return {{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:lgd,tooltip:tooltipFmt(suffix)}},scales:{{x:xAxis(),y:yAxis(yLabel)}}}};
}}

/* ════════════════════════════════════════════
   GDP CHARTS
   ════════════════════════════════════════════ */
const cGDP = new Chart(document.getElementById('chartGDP'),{{
  type:'bar',
  data:{{labels:D.periods,datasets:[
    {{label:'GDP YoY (%)',data:D.yoy,
      backgroundColor:D.yoy.map(v=>v>=0?'rgba(45,90,39,0.75)':'rgba(181,70,15,0.75)'),
      borderColor:D.yoy.map(v=>v>=0?'#2d5a27':'#b5460f'),borderWidth:1,borderRadius:2,order:2}},
    {{label:`Pre-COVID Mean (${{D.precovid_mean.toFixed(2)}}%)`,data:D.periods.map(()=>D.precovid_mean),
      type:'line',borderColor:'#8a6c1a',borderDash:[5,4],borderWidth:1.5,pointRadius:0,tension:0,fill:false,order:1}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:legend(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
      itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{title:items=>items[0].label,
        label:ctx=>ctx.datasetIndex===0?` GDP YoY: ${{ctx.parsed.y>=0?'+':''}}${{ctx.parsed.y.toFixed(2)}}%`:` Pre-COVID Mean: ${{ctx.parsed.y.toFixed(2)}}%`}}}}}},
    scales:{{x:xAxis(),y:yAxis('YoY (%)')}}}}
}});

const cExpG  = new Chart(document.getElementById('chartExpGrowth'), {{type:'line',data:{{labels:D.exp_g_periods,datasets:Object.entries(D.exp_g_data).map(([l,v])=>lineDS(l,v,EXP_COLORS[l]||'#999',l==='GDP'?{{borderWidth:2.5,borderDash:[4,3]}}:{{}}))}},options:chartOpts(legend(),'%','YoY (%)')}});
const cExpC  = new Chart(document.getElementById('chartExpContrib'),{{type:'line',data:{{labels:D.exp_c_periods,datasets:Object.entries(D.exp_c_data).map(([l,v])=>lineDS(l,v,EXP_COLORS[l]||'#999'))}},options:chartOpts(legend(),' pp','pp')}});
const cHhG   = new Chart(document.getElementById('chartHhGrowth'),  {{type:'line',data:{{labels:D.hh_g_periods, datasets:Object.entries(D.hh_g_data).map(([l,v])=>lineDS(l,v,HH_COLORS[l]||'#999',l==='Household Total'?{{borderWidth:2.5,borderDash:[4,3]}}:{{}}))}},options:chartOpts(legendRight(),'%','YoY (%)')}});
const cHhC   = new Chart(document.getElementById('chartHhContrib'), {{type:'line',data:{{labels:D.hh_c_periods, datasets:Object.entries(D.hh_c_data).map(([l,v])=>lineDS(l,v,HH_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),' pp','pp')}});
const cGfcfG = new Chart(document.getElementById('chartGfcfGrowth'),{{type:'line',data:{{labels:D.gfcf_g_periods,datasets:Object.entries(D.gfcf_g_data).map(([l,v])=>lineDS(l,v,GFCF_COLORS[l]||'#999',l==='GFCF Total'?{{borderWidth:2.5,borderDash:[4,3]}}:{{}}))}},options:chartOpts(legendRight(),'%','YoY (%)')}});
const cGfcfC = new Chart(document.getElementById('chartGfcfContrib'),{{type:'line',data:{{labels:D.gfcf_c_periods,datasets:Object.entries(D.gfcf_c_data).map(([l,v])=>lineDS(l,v,GFCF_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),' pp','pp')}});
const cSecG  = new Chart(document.getElementById('chartSecGrowth'), {{type:'line',data:{{labels:D.sec_g_periods, datasets:Object.entries(D.sec_g_data).map(([l,v])=>lineDS(l,v,SEC_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),'%','YoY (%)')}});
const cSecC  = new Chart(document.getElementById('chartSecContrib'),{{type:'line',data:{{labels:D.sec_c_periods, datasets:Object.entries(D.sec_c_data).map(([l,v])=>lineDS(l,v,SEC_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),' pp','pp')}});
const cMfgG  = new Chart(document.getElementById('chartMfgGrowth'), {{type:'line',data:{{labels:D.mfg_g_periods, datasets:Object.entries(D.mfg_g_data).map(([l,v])=>lineDS(l,v,MFG_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),'%','YoY (%)')}});
const cMfgC  = new Chart(document.getElementById('chartMfgContrib'),{{type:'line',data:{{labels:D.mfg_c_periods, datasets:Object.entries(D.mfg_c_data).map(([l,v])=>lineDS(l,v,MFG_COLORS[l]||'#999'))}},options:chartOpts(legendRight(),' pp','pp')}});

const GDP_ALL = {{
  gdp:  {{p:D.periods,       d:[D.yoy,D.periods.map(()=>D.precovid_mean)]}},
  expG: {{p:D.exp_g_periods, d:Object.values(D.exp_g_data)}},
  expC: {{p:D.exp_c_periods, d:Object.values(D.exp_c_data)}},
  hhG:  {{p:D.hh_g_periods,  d:Object.values(D.hh_g_data)}},
  hhC:  {{p:D.hh_c_periods,  d:Object.values(D.hh_c_data)}},
  gfcfG:{{p:D.gfcf_g_periods,d:Object.values(D.gfcf_g_data)}},
  gfcfC:{{p:D.gfcf_c_periods,d:Object.values(D.gfcf_c_data)}},
  secG: {{p:D.sec_g_periods, d:Object.values(D.sec_g_data)}},
  secC: {{p:D.sec_c_periods, d:Object.values(D.sec_c_data)}},
  mfgG: {{p:D.mfg_g_periods, d:Object.values(D.mfg_g_data)}},
  mfgC: {{p:D.mfg_c_periods, d:Object.values(D.mfg_c_data)}},
}};

function applyGDPWindow(chart,allP,allD,n) {{
  const labels=n?allP.slice(-n):allP;
  chart.data.labels=labels;
  chart.data.datasets.forEach((ds,i)=>{{
    const vals=n?allD[i].slice(-n):allD[i]; ds.data=vals;
    if(chart===cGDP&&i===0){{ds.backgroundColor=vals.map(v=>v>=0?'rgba(45,90,39,0.75)':'rgba(181,70,15,0.75)');ds.borderColor=vals.map(v=>v>=0?'#2d5a27':'#b5460f');}}
  }});
  if(chart===cGDP)chart.data.datasets[1].data=labels.map(()=>D.precovid_mean);
  chart.update();
}}

let snapBuilt=false;
function snapBarDS(labels,values,tot) {{
  return {{label:'',data:values,
    backgroundColor:labels.map((l,i)=>l===tot?'rgba(26,24,20,0.82)':values[i]>=0?'rgba(45,90,39,0.75)':'rgba(181,70,15,0.75)'),
    borderColor:labels.map((l,i)=>l===tot?'#1a1814':values[i]>=0?'#2d5a27':'#b5460f'),
    borderWidth:labels.map(l=>l===tot?2:1),borderRadius:2}};
}}
function snapOpts(suffix) {{
  return {{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>` ${{ctx.parsed.x!=null?ctx.parsed.x.toFixed(2):''}}${{suffix}}`}}}}}},
    scales:{{x:{{ticks:{{font:{{family:MONO,size:10}}}},grid:{{color:'rgba(0,0,0,0.05)'}}}},y:{{ticks:{{font:{{family:MONO,size:10}}}},grid:{{display:false}}}}}}}};
}}
function buildSnapChart(id,sd,suffix) {{
  return new Chart(document.getElementById(id),{{type:'bar',data:{{labels:sd.labels,datasets:[snapBarDS(sd.labels,sd.values,sd.total_label)]}},options:snapOpts(suffix)}});
}}
function buildSnapCharts() {{
  try {{
    const S=D.snap;
    document.getElementById('snapCmtOverview').innerHTML=S.comments.overview;
    document.getElementById('snapCmtHh').innerHTML=S.comments.hh;
    document.getElementById('snapCmtGfcf').innerHTML=S.comments.gfcf;
    document.getElementById('snapCmtSectors').innerHTML=S.comments.sectors;
    document.getElementById('snapCmtMfg').innerHTML=S.comments.mfg;
    buildSnapChart('snapExpGrowth',S.exp_growth,'%');buildSnapChart('snapExpContrib',S.exp_contrib,' pp');
    buildSnapChart('snapHhGrowth',S.hh_growth,'%');buildSnapChart('snapHhContrib',S.hh_contrib,' pp');
    buildSnapChart('snapGfcfGrowth',S.gfcf_growth,'%');buildSnapChart('snapGfcfContrib',S.gfcf_contrib,' pp');
    buildSnapChart('snapSecGrowth',S.sec_growth,'%');buildSnapChart('snapSecContrib',S.sec_contrib,' pp');
    buildSnapChart('snapMfgGrowth',S.mfg_growth,'%');buildSnapChart('snapMfgContrib',S.mfg_contrib,' pp');
    snapBuilt=true;
  }} catch(e){{console.error(e);}}
}}

function setGDPWindow(n) {{
  const isSnap=n==='snap';
  document.getElementById('gdpTabTS').style.display=isSnap?'none':'block';
  document.getElementById('gdpTabSnap').style.display=isSnap?'block':'none';
  ['gdpBtnSnap','gdpBtn2y','gdpBtn4y','gdpBtnAll'].forEach(id=>document.getElementById(id).classList.remove('active'));
  if(isSnap){{document.getElementById('gdpBtnSnap').classList.add('active');if(!snapBuilt)buildSnapCharts();return;}}
  Object.entries(GDP_ALL).forEach(([k,v])=>{{
    const charts={{gdp:cGDP,expG:cExpG,expC:cExpC,hhG:cHhG,hhC:cHhC,gfcfG:cGfcfG,gfcfC:cGfcfC,secG:cSecG,secC:cSecC,mfgG:cMfgG,mfgC:cMfgC}};
    applyGDPWindow(charts[k],v.p,v.d,n);
  }});
  document.getElementById(n===8?'gdpBtn2y':n===16?'gdpBtn4y':'gdpBtnAll').classList.add('active');
  updateGDPCommentary(n);
}}

/* ════════════════════════════════════════════
   GDP COMMENTARY  (window-aware)
   ════════════════════════════════════════════ */
function updateGDPCommentary(n) {{
  const wlabel = n===0?'full period (2015–present)':n===8?'past 2 years':'past 4 years';
  const clabel = D.latest_period+' · '+(n===0?'All':n===8?'2Y':'4Y');

  // Slice last n items; n=0 means all
  const sl = arr => n?(arr||[]).slice(-n):(arr||[]);
  const slP = vals => n?(vals||[]).slice(-n):(vals||[]);

  // Stats
  const avg = a=>{{const v=a.filter(x=>x!=null&&!isNaN(x));return v.length?v.reduce((s,x)=>s+x,0)/v.length:0;}};
  const nNeg = a=>a.filter(x=>x!=null&&x<0).length;
  const nPos = a=>a.filter(x=>x!=null&&x>0).length;
  const mn = a=>{{const v=a.filter(x=>x!=null&&!isNaN(x));return v.length?Math.min(...v):0;}};
  const mx = a=>{{const v=a.filter(x=>x!=null&&!isNaN(x));return v.length?Math.max(...v):0;}};
  const last = a=>{{const v=a.filter(x=>x!=null&&!isNaN(x));return v.length?v[v.length-1]:0;}};
  const sd = a=>{{if(a.length<2)return 0;const m=avg(a);return Math.sqrt(a.reduce((s,v)=>s+(v-m)**2,0)/a.length);}};
  const trendFn = a=>{{
    if(a.length<4)return 'stable';
    const h=Math.floor(a.length/2),f=avg(a.slice(0,h)),s=avg(a.slice(h));
    return s>f+0.4?'accelerating':s<f-0.4?'moderating':'stable';
  }};
  const topN = (obj,k)=>Object.entries(obj).map(([key,vals])=>{{return{{key,v:last(slP(vals))}}}}).sort((a,b)=>b.v-a.v).slice(0,k);
  const botN = (obj,k)=>Object.entries(obj).map(([key,vals])=>{{return{{key,v:last(slP(vals))}}}}).sort((a,b)=>a.v-b.v).slice(0,k);

  // Format helpers
  const b  = (v,dec)=>{{if(v==null||isNaN(v))return'—';dec=dec??2;return'<strong>'+(v>=0?'+':'')+v.toFixed(dec)+'%</strong>';}};
  const bp = (v,dec)=>{{if(v==null||isNaN(v))return'—';dec=dec??2;return'<strong>'+(v>=0?'+':'')+v.toFixed(dec)+' pp</strong>';}};
  const bn = (v,dec)=>{{dec=dec??2;return'<strong>'+v.toFixed(dec)+'%</strong>';}};
  const em = t=>'<em>'+t+'</em>';
  const p  = t=>'<p>'+t+'</p>';

  // Update all time-series label divs at once
  document.querySelectorAll('#gdpTabTS .comment-box .cb-label').forEach(el=>el.textContent=clabel);

  // ── 01 Headline GDP ──────────────────────────────────────────────────────
  const yoy=sl(D.yoy);
  const g=last(yoy), gPrv=yoy[yoy.length-2]??0, gAvg=avg(yoy);
  const tr=trendFn(yoy);
  const h=Math.floor(yoy.length/2), f1=avg(yoy.slice(0,h)), f2=avg(yoy.slice(h));
  const vsPC=g-D.precovid_mean;

  const trMsg = tr==='accelerating'
    ? 'Growth has been <strong>accelerating</strong> over the '+wlabel+' — avg rose from '+bn(f1)+' to '+bn(f2)+' across the two halves of the window, pointing to building momentum.'
    : tr==='moderating'
    ? 'Growth has been <strong>moderating</strong> — avg slipped from '+bn(f1)+' to '+bn(f2)+' across the two halves of the window. Whether this is a healthy normalisation or softening demand is the key question to track.'
    : 'Growth has been <strong>broadly stable</strong> around '+bn(gAvg)+' — consistent with a steady-state expansion rather than a cyclical upswing or downswing.';
  const pcMsg = Math.abs(vsPC)<0.3
    ? 'At '+b(g)+', growth has essentially returned to its pre-COVID (2015–2019) cruise speed of '+bn(D.precovid_mean)+'. Structural normalisation looks complete.'
    : vsPC>0
    ? 'At '+b(g)+', Indonesia is running '+bn(vsPC)+' pp above its pre-COVID mean of '+bn(D.precovid_mean)+'. If sustained, this marks a genuine upshift — not just catch-up growth.'
    : 'At '+b(g)+', growth is still '+bn(Math.abs(vsPC))+' pp below the pre-COVID mean of '+bn(D.precovid_mean)+'. Full structural normalisation remains incomplete.';
  const covidCaveat = n===0?p('<em>Note: the full-period average spans the 2020 COVID collapse and the 2021 rebound. The 2Y or 4Y window gives a cleaner read of the post-pandemic trajectory.</em>'):'';

  document.getElementById('cmtGDPtext').innerHTML=
    p('GDP grew '+b(g)+' YoY in '+em(D.latest_period)+', '+(g>gPrv?'up':'down')+' '+bn(Math.abs(g-gPrv))+' pp from the prior quarter. Window avg: '+bn(gAvg)+'.') +
    p(trMsg)+p(pcMsg)+covidCaveat;

  // ── 02 Demand — YoY Growth ──────────────────────────────────────────────
  const egD=D.exp_g_data;
  const hhG=last(slP(egD['Household Consumption']||[])), invG=last(slP(egD['Investment (PMTB)']||[]));
  const govG=last(slP(egD['Government']||[])), expG=last(slP(egD['Exports (Goods)']||[]));
  const hhAvg=avg(slP(egD['Household Consumption']||[])), invAvg=avg(slP(egD['Investment (PMTB)']||[]));
  const hhTr=trendFn(slP(egD['Household Consumption']||[])), invTr=trendFn(slP(egD['Investment (PMTB)']||[]));
  const egNeg=Object.keys(egD).filter(k=>k!=='GDP'&&last(slP(egD[k]||[]))<0);
  // Determine demand driver by CONTRIBUTION (pp to GDP), not growth rate.
  // HH consumption is ~55% of GDP vs investment ~30%, so rate comparison is misleading.
  const hhC_lead=last(slP((D.exp_c_data||{{}})['Household Consumption']||[]));
  const invC_lead=last(slP((D.exp_c_data||{{}})['Investment (PMTB)']||[]));
  const lead=hhC_lead>=invC_lead?'consumption-led':'investment-led';

  const hhSynth=hhTr==='accelerating'
    ?'Household consumption at '+b(hhG)+' is accelerating — rising incomes and confidence are translating into stronger spending. A bullish signal for domestic demand.'
    :hhTr==='moderating'
    ?'Household consumption has moderated to '+b(hhG)+' (window avg '+bn(hhAvg)+') — the consumer engine is losing steam. Watch for pass-through from real wage trends.'
    :'Household consumption is steady at '+b(hhG)+' (window avg '+bn(hhAvg)+') — neither a growth driver nor a drag.';
  const invSynth=invTr==='accelerating'
    ?'Investment at '+b(invG)+' is accelerating — companies are expanding capacity, a leading indicator for future output potential.'
    :invTr==='moderating'
    ?'Investment at '+b(invG)+' is moderating (window avg '+bn(invAvg)+') — capex appetite is cooling, which could limit future growth potential if sustained.'
    :'Investment at '+b(invG)+' is stable (window avg '+bn(invAvg)+').';

  document.getElementById('cmtExpGrowthtext').innerHTML=
    p('Growth is currently <strong>'+lead+'</strong>.'+(egNeg.length?' <strong>Contracting</strong>: '+egNeg.join(', ')+'.':" All demand components positive.")+' Government: '+b(govG)+'; Exports: '+b(expG)+'.') +
    p(hhSynth)+p(invSynth);

  // ── 02 Demand — Contributions ────────────────────────────────────────────
  const ecD=D.exp_c_data;
  const hhC=last(slP(ecD['Household Consumption']||[])), invC=last(slP(ecD['Investment (PMTB)']||[]));
  const expC=last(slP(ecD['Exports (Goods)']||[])), impC=last(slP(ecD['Imports (Goods)']||[]));
  const govC=last(slP(ecD['Government']||[]));
  const netT=(expC||0)+(impC||0);
  const hhShare=g?Math.round((hhC/g)*100):0;
  const concMsg=Math.abs(hhC)>(Math.abs(invC)+Math.abs(govC))
    ?'Consumption is the dominant engine — growth quality depends heavily on household income trends and consumer sentiment. A single-source dependency worth monitoring.'
    :'Growth is reasonably distributed across demand components, reducing vulnerability to any single source weakening.';

  document.getElementById('cmtExpContribtext').innerHTML=
    p('Household consumption contributes '+bp(hhC)+' to the '+b(g)+' headline — roughly <strong>'+hhShare+'%</strong> of total growth. Investment adds '+bp(invC)+'; government '+bp(govC)+'.') +
    p('Net trade (exports '+bp(expC)+' plus imports '+bp(impC)+') is a <strong>'+(netT>=0?'tailwind':'headwind')+'</strong> of '+bp(netT)+'. '+(netT<-0.5?'Strong import growth typically signals healthy domestic demand, but it mechanically reduces the headline GDP number. The drag from imports here is a sign of economic strength, not weakness.':netT>0.5?'A positive trade contribution adds to the headline without relying solely on domestic demand — a more balanced growth mix.':'Net trade is broadly neutral.'))+
    p(concMsg);

  // ── 02b HH — YoY Growth ──────────────────────────────────────────────────
  const hgD=D.hh_g_data;
  const transG=last(slP(hgD['Transport & Comms']||[])), restG=last(slP(hgD['Restaurant & Hotel']||[]));
  const foodG=last(slP(hgD['Food & Beverages']||[])), equipG=last(slP(hgD['Household Equipment']||[]));
  const healG=last(slP(hgD['Health & Education']||[])), appG=last(slP(hgD['Apparel & Footwear']||[]));
  const hgTop=topN(hgD,2).filter(x=>x.key!=='Household Total');
  const hgBot=botN(hgD,1).filter(x=>x.key!=='Household Total');
  const discr=avg([transG,restG,equipG,appG].filter(v=>!isNaN(v)));
  const nonDiscr=avg([foodG,healG].filter(v=>!isNaN(v)));
  const confMsg=discr>nonDiscr
    ?'Discretionary categories (transport, dining, household equipment) are outpacing necessities — a sign of <strong>improving consumer confidence</strong> and real purchasing power.'
    :'Non-discretionary spending is growing faster than discretionary categories — consumers are <strong>prioritising essentials</strong> over upgrades, which can signal caution or cost-of-living pressure.';

  document.getElementById('cmtHhGrowthtext').innerHTML=
    p('Top HH components this quarter: '+hgTop.map(x=>em(x.key)+' '+b(x.v)).join(', ')+'. Lagging: '+hgBot.map(x=>em(x.key)+' '+b(x.v)).join(', ')+'.') +
    p(confMsg) +
    p('Transport & Comms ('+b(transG)+') and Restaurants ('+b(restG)+') are <strong>mobility and social spending indicators</strong> — they tend to lead the consumer cycle by 1–2 quarters. Their trajectory offers an early read on the consumer outlook.');

  // ── 02b HH — Contributions ───────────────────────────────────────────────
  const hcD=D.hh_c_data;
  const hcTop=topN(hcD,3);
  const foodC=last(slP(hcD['Food & Beverages']||[])), foodCavg=avg(slP(hcD['Food & Beverages']||[]));
  const hcNeg=Object.keys(hcD).filter(k=>last(slP(hcD[k]||[]))<0);
  const hhTop3sum=hcTop.reduce((s,x)=>s+x.v,0);
  const hhGNow=last(slP(hgD['Household Total']||[]));

  document.getElementById('cmtHhContribtext').innerHTML=
    p('Top contributors to HH consumption growth: '+hcTop.map(x=>em(x.key)+' '+bp(x.v)).join(', ')+'. Together: '+bp(hhTop3sum)+' of the '+bn(hhGNow)+' total.') +
    p('Food & Beverages contributes '+bp(foodC)+' (window avg '+bp(foodCavg)+') — its weight in the CPI basket makes it the most stable contributor, though also the least revealing about economic dynamism.') +
    (hcNeg.length?p('<strong>Drag</strong>: '+em(hcNeg.join(', '))+'. These categories are shrinking as a share of household spending — either due to substitution, price effects, or genuine demand weakness.'):p('No category is dragging on HH consumption this quarter — a fully broad-based consumer expansion.'));

  // ── 02c GFCF — YoY Growth ────────────────────────────────────────────────
  const ggD=D.gfcf_g_data;
  const bldG=last(slP(ggD['Buildings & Structures']||[])), machG=last(slP(ggD['Machine & Equipment']||[]));
  const vehG=last(slP(ggD['Vehicles']||[])), ipG=last(slP(ggD['Intellectual Property']||[]));
  const gfTot=last(slP(ggD['GFCF Total']||[]));
  const machAvg=avg(slP(ggD['Machine & Equipment']||[])), machTr=trendFn(slP(ggD['Machine & Equipment']||[]));
  const qualMsg=machG>bldG
    ?'<strong>Machinery is outpacing Buildings</strong> ('+b(machG)+' vs '+b(bldG)+') — a quality signal: the investment cycle is expanding productive capacity rather than just physical structures.'
    :'<strong>Buildings & Structures lead</strong> ('+b(bldG)+' vs machinery '+b(machG)+') — investment growth skews toward construction. While positive for short-run activity, it is less supportive of long-run productivity than equipment investment.';
  const ipMsg=ipG!=null&&!isNaN(ipG)?(ipG>5?'Intellectual property at '+b(ipG)+' points to rising R&D and digital asset investment — a promising quality upgrade signal.':ipG<0?'Intellectual property investment is contracting ('+b(ipG)+') — a concern for long-run innovation capacity.':'Intellectual property investment at '+b(ipG)+' is modest but positive.'):'';
  const machMoMsg=machTr==='accelerating'?' Machinery capex is accelerating — corporate confidence in future demand appears high.':machTr==='moderating'?' Machinery growth is moderating — potential sign of cooling capex appetite.':'';

  document.getElementById('cmtGfcfGrowthtext').innerHTML=
    p('Total GFCF grew '+b(gfTot)+'. Buildings: '+b(bldG)+' · Machinery: '+b(machG)+' · Vehicles: '+b(vehG)+'.') +
    p(qualMsg+machMoMsg) +
    (ipMsg?p(ipMsg):'');

  // ── 02c GFCF — Contributions ─────────────────────────────────────────────
  const gcD=D.gfcf_c_data;
  const gcTop=topN(gcD,3).filter(x=>x.key!=='GFCF Total');
  const bldC=last(slP(gcD['Buildings & Structures']||[])), machC=last(slP(gcD['Machine & Equipment']||[]));
  const gcNeg=Object.keys(gcD).filter(k=>k!=='GFCF Total'&&last(slP(gcD[k]||[]))<0);

  document.getElementById('cmtGfcfContribtext').innerHTML=
    p('Key GFCF contributors: '+gcTop.map(x=>em(x.key)+' '+bp(x.v)).join(', ')+'.') +
    p('Buildings contributes '+bp(bldC)+' and Machinery '+bp(machC)+'. '+(machC>bldC?'Machinery-led GFCF is the higher-quality scenario — it expands production capacity.':'Buildings-led GFCF is supportive of short-run activity but does less for productive capacity.')+' ') +
    (gcNeg.length?p('Drag from: '+em(gcNeg.join(', '))+'.'):p('All tracked GFCF components contribute positively — broadly based investment cycle.'));

  // ── 03 Sectors — YoY Growth ──────────────────────────────────────────────
  const sgD=D.sec_g_data;
  const sgAll=Object.entries(sgD).map(([k,v])=>{{return{{k,v:last(slP(v))}}}});
  const sgPos=sgAll.filter(x=>x.v>0).length, sgNeg_n=sgAll.filter(x=>x.v<0).length;
  const sgSorted=[...sgAll].sort((a,b)=>b.v-a.v);
  const sgTop3=sgSorted.slice(0,3), sgBot3=sgSorted.slice(-3);
  const mfgNow=last(slP(sgD['Manufacturing']||[])), mfgAvg=avg(slP(sgD['Manufacturing']||[]));
  const icNow=last(slP(sgD['Info & Comms']||[]));
  const mfgVsGDP=mfgNow-g;
  const breadthMsg=sgPos>=15?'Growth is <strong>extremely broad-based</strong> ('+sgPos+'/17 sectors expanding) — a high-quality headline that is not being driven by one or two outliers.':sgPos>=12?'Growth is <strong>broadly based</strong> at '+sgPos+'/17 sectors. Solid foundations across the economy.':sgPos>=9?'Growth is <strong>moderately widespread</strong> ('+sgPos+'/17). Positive, but some pockets of weakness persist.':'Growth is <strong>narrow</strong> — only '+sgPos+'/17 sectors expanding. The headline is masking significant under-performance across the economy.';

  document.getElementById('cmtSecGrowthtext').innerHTML=
    p(breadthMsg+(sgNeg_n>0?' <strong>Contracting</strong>: '+sgBot3.filter(x=>x.v<0).map(x=>em(x.k)).join(', ')+'.':'')) +
    p('<strong>Leaders</strong>: '+sgTop3.map(x=>em(x.k)+' '+b(x.v)).join(', ')+'. <strong>Laggards</strong>: '+sgBot3.map(x=>em(x.k)+' '+b(x.v)).join(', ')+'.') +
    p('Manufacturing at '+b(mfgNow)+' (window avg '+bn(mfgAvg)+') is <strong>'+(mfgVsGDP>0.3?'outperforming':mfgVsGDP<-0.3?'underperforming':'tracking')+'</strong> the headline'+(mfgVsGDP>0.3?' — the industrial base is punching above its weight.':mfgVsGDP<-0.3?' — services are doing the heavy lifting. If persistent, this suggests a structural shift toward a services-led growth model.':'.')+' Info & Comms at '+b(icNow)+' captures the digital economy\\'s growing footprint.');

  // ── 03 Sectors — Contributions ───────────────────────────────────────────
  const scD=D.sec_c_data;
  const scAll=Object.entries(scD).map(([k,v])=>{{return{{k,v:last(slP(v))}}}}).sort((a,b)=>b.v-a.v);
  const scTop3=scAll.slice(0,3), scNeg=scAll.filter(x=>x.v<0);
  const scTop3sum=scTop3.reduce((s,x)=>s+x.v,0);
  const concPct=g?Math.round((scTop3sum/g)*100):0;
  const concMsg2=concPct>70?'With the top three contributing <strong>'+concPct+'%</strong> of total growth, the expansion is <strong>highly concentrated</strong>. The headline overstates how widely shared the growth actually is.':concPct>50?'The top three sectors account for <strong>'+concPct+'%</strong> of growth — moderate concentration. Broad, but not evenly distributed.':'At <strong>'+concPct+'%</strong> from the top three, growth is <strong>well diversified</strong> across the economy — a high-quality result.';

  document.getElementById('cmtSecContribtext').innerHTML=
    p('Top contributors: '+scTop3.map(x=>em(x.k)+' '+bp(x.v)).join(', ')+'. Combined: '+bp(scTop3sum)+' of the '+b(g)+' headline.') +
    p(concMsg2) +
    (scNeg.length?p('<strong>Drag</strong>: '+scNeg.map(x=>em(x.k)+' '+bp(x.v)).join(', ')+'.'):p('No sector is a net drag this quarter — a uniformly positive sectoral picture.'));

  // ── 04 Manufacturing — YoY Growth ────────────────────────────────────────
  const mgD=D.mfg_g_data;
  const mgAll=Object.entries(mgD).map(([k,v])=>{{return{{k,v:last(slP(v))}}}});
  const mgPos=mgAll.filter(x=>x.v>0).length;
  const mgSorted=[...mgAll].sort((a,b)=>b.v-a.v);
  const mgTop3=mgSorted.slice(0,3), mgBot3=mgSorted.slice(-3);
  const foodMG=last(slP(mgD['Food & Beverages']||[]));
  const metalG=last(slP(mgD['Metal Products & Electronics']||[]));
  const mfgBreadthMsg=mgPos>=14?'Broad-based expansion: <strong>'+mgPos+'/'+mgAll.length+'</strong> subsectors growing.':mgPos>=10?'<strong>'+mgPos+'/'+mgAll.length+'</strong> subsectors growing — solid if not exceptional breadth.':'Narrow: only <strong>'+mgPos+'/'+mgAll.length+'</strong> subsectors expanding. Headline manufacturing growth is being carried by a few segments.';
  const mfgVsGDPMsg=mfgNow-g>0.3?'Manufacturing is <strong>outperforming</strong> the headline ('+b(mfgNow)+' vs GDP '+b(g)+') — the industrial base is a growth amplifier.':mfgNow-g<-0.3?'Manufacturing is <strong>lagging</strong> the headline ('+b(mfgNow)+' vs GDP '+b(g)+') — the economy\\'s growth is increasingly services-driven.':'Manufacturing is <strong>tracking the headline</strong> — in line with overall economic momentum.';
  const upgradeMsg=metalG>foodMG?'High-value Metal Products & Electronics ('+b(metalG)+') is outpacing commodity-oriented Food & Beverages ('+b(foodMG)+') — a positive value-chain upgrade signal.':'Food & Beverages ('+b(foodMG)+') continues to anchor manufacturing — Indonesia\\'s industrial base still leans toward lower value-add processing. Metal Products & Electronics at '+b(metalG)+' trails, suggesting limited progress up the value chain this quarter.';

  document.getElementById('cmtMfgGrowthtext').innerHTML=
    p(mfgBreadthMsg+' '+mfgVsGDPMsg) +
    p('<strong>Top</strong>: '+mgTop3.map(x=>em(x.k)+' '+b(x.v)).join(', ')+'. <strong>Weakest</strong>: '+mgBot3.map(x=>em(x.k)+' '+b(x.v)).join(', ')+'.') +
    p(upgradeMsg);

  // ── 04 Manufacturing — Contributions ─────────────────────────────────────
  const mcD=D.mfg_c_data;
  const mcAll=Object.entries(mcD).map(([k,v])=>{{return{{k,v:last(slP(v))}}}}).sort((a,b)=>b.v-a.v);
  const mcTop3=mcAll.slice(0,3), mcNeg=mcAll.filter(x=>x.v<0);
  const mcTop3sum=mcTop3.reduce((s,x)=>s+x.v,0);
  const mcConcPct=mfgNow?Math.round((mcTop3sum/mfgNow)*100):0;
  const foodMC=mcAll.find(x=>x.k==='Food & Beverages');
  const metalMC=mcAll.find(x=>x.k==='Metal Products & Electronics');

  document.getElementById('cmtMfgContribtext').innerHTML=
    p('Top contributors to mfg growth: '+mcTop3.map(x=>em(x.k)+' '+bp(x.v)).join(', ')+' — together '+bp(mcTop3sum)+' of the '+b(mfgNow)+' total ('+(mcConcPct)+'%).') +
    (foodMC?p(em('Food & Beverages')+' contributes '+bp(foodMC.v)+' — its consumer-market scale makes it structurally dominant, but also means headline mfg growth can be driven by food price and volume cycles rather than industrial upgrading.'):'')+
    (metalMC&&metalMC.v>0?p(em('Metal Products & Electronics')+' contributes '+bp(metalMC.v)+' — every percentage point of positive contribution here is more valuable than in food processing, as it signals capacity in higher-value global supply chains.'):'')+
    (mcNeg.length?p('<strong>Drag</strong>: '+mcNeg.map(x=>em(x.k)+' '+bp(x.v)).join(', ')+'. '+(mcNeg.length>4?'With '+mcNeg.length+' subsectors contracting, headline mfg growth is being driven by a narrow base — a quality concern.':'Localised weakness rather than systemic.')):p('No manufacturing subsector is a net drag — unusually clean, broad-based industrial expansion.'));
}}

/* ════════════════════════════════════════════
   BOP CHARTS (lazy — init on first tab switch)
   ════════════════════════════════════════════ */
let bopCharts=[], bopInited=false, bopSnapBuilt=false;

function setBOPWindow(n) {{
  const isSnap = n==='snap';
  document.getElementById('bopTabTS').style.display   = isSnap ? 'none'  : 'block';
  document.getElementById('bopTabSnap').style.display = isSnap ? 'block' : 'none';
  ['bopBtnSnap','bopBtn2y','bopBtn4y','bopBtnAll'].forEach(id=>document.getElementById(id).classList.remove('active'));
  if (isSnap) {{
    document.getElementById('bopBtnSnap').classList.add('active');
    if (!bopSnapBuilt) initBOPSnap();
    return;
  }}
  document.getElementById(n===8?'bopBtn2y':n===16?'bopBtn4y':'bopBtnAll').classList.add('active');
  bopCharts.forEach(ch=>{{
    const sl=arr=>n===0?arr:(arr||[]).slice(-n);
    ch.data.labels=sl(B.periods);
    ch.data.datasets.forEach(ds=>{{if(ds._full)ds.data=sl(ds._full);}});
    ch.update();
  }});
  updateBOPCommentary(n);
}}

function initBOPSnap() {{
  const li = B.ca.reduceRight((acc,v,i)=>acc===-1&&v!==null?i:acc,-1);

  function bSD(labels, values) {{
    return {{
      label:'', data:values,
      backgroundColor: values.map(v=>v!==null&&v>=0?'rgba(22,163,74,0.72)':'rgba(181,70,15,0.72)'),
      borderColor:     values.map(v=>v!==null&&v>=0?'#16a34a':'#b5460f'),
      borderWidth:1, borderRadius:2,
    }};
  }}
  function bSOpts(suffix) {{
    return {{
      responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>` ${{ctx.parsed.x!=null?ctx.parsed.x.toLocaleString('en-US',{{maximumFractionDigits:0}}):''}} ${{suffix}}`}}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{family:MONO,size:10}},callback:v=>(Math.abs(v)>=1000?(v/1000).toFixed(1)+'k':v.toFixed(0))}},grid:{{color:'rgba(0,0,0,0.05)'}}}},
        y:{{ticks:{{font:{{family:MONO,size:10}}}},grid:{{display:false}}}}
      }}
    }};
  }}

  // 01 BOP Summary
  new Chart(document.getElementById('bopSnapBOP'), {{
    type:'bar',
    data:{{
      labels:['Current Account','Capital+Financial','Net Errors','Overall Balance'],
      datasets:[bSD(['CA','KA+FA','Err','Bal'],[B.ca[li],B.ka_fa[li],B.errors[li],B.balance[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  // 02 CA Components
  new Chart(document.getElementById('bopSnapCA'), {{
    type:'bar',
    data:{{
      labels:['A. Goods','B. Services','C. Primary Income','D. Secondary Income','CA Total'],
      datasets:[bSD(['G','S','P','D','T'],[B.ca_goods[li],B.ca_svcs[li],B.ca_primary[li],B.ca_second[li],B.ca[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  // 03 FA Components
  new Chart(document.getElementById('bopSnapFA'), {{
    type:'bar',
    data:{{
      labels:['1. Direct Investment','2. Portfolio','3. Derivatives','4. Other Investment','FA Total'],
      datasets:[bSD(['DI','PI','D','OI','T'],[B.fa_di[li],B.fa_pi[li],B.fa_der[li],B.fa_oi[li],B.fa[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  // 04 Reserve Assets
  new Chart(document.getElementById('bopSnapRes'), {{
    type:'bar',
    data:{{
      labels:['Reserve Change'],
      datasets:[bSD(['R'],[B.res[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  bopSnapBuilt=true;
}}

function updateBOPCommentary(n) {{
  const li = B.ca.reduceRight((acc,v,i) => acc===-1 && v!==null ? i : acc, -1);
  const lp = B.periods[li];
  const wlabel = n===0 ? 'full period shown' : n===8 ? 'past 2 years' : 'past 4 years';
  const clabel = lp + ' · ' + (n===0 ? 'All' : n===8 ? '2Y' : '4Y');

  // Slice to window, keeping only non-null values up to latest index
  function sl(arr) {{
    const out = (arr||[]).slice(0, li+1).filter(v => v!==null);
    return n===0 ? out : out.slice(-n);
  }}

  const avg  = a => a.length ? a.reduce((s,v)=>s+v,0)/a.length : 0;
  const nNeg = a => a.filter(v=>v<0).length;
  const nPos = a => a.filter(v=>v>0).length;
  const mn   = a => a.length ? Math.min(...a) : 0;
  const mx   = a => a.length ? Math.max(...a) : 0;
  const sd   = a => {{ if(a.length<2)return 0; const m=avg(a); return Math.sqrt(a.reduce((s,v)=>s+(v-m)**2,0)/a.length); }};

  // Bold number helper
  function b(v, unit, dec) {{
    if(v===null||v===undefined)return '—';
    dec = dec||0; unit = unit||'';
    const abs=Math.abs(v), s = abs>=10000 ? (v/1000).toFixed(1)+'k' : v.toFixed(dec);
    return '<strong>'+(v>=0?'+':'')+s+(unit?' '+unit:'')+'</strong>';
  }}
  function bn(v,dec) {{ dec=dec||1; return '<strong>'+v.toFixed(dec)+'</strong>'; }}
  const em = t => '<em>'+t+'</em>';
  const p  = t => '<p>'+t+'</p>';

  const ca_w   = sl(B.ca),   kafa_w = sl(B.ka_fa), bal_w  = sl(B.balance);
  const gds_w  = sl(B.ca_goods), svcs_w = sl(B.ca_svcs);
  const prim_w = sl(B.ca_primary), sec_w = sl(B.ca_second);
  const fa_w   = sl(B.fa),   fadi_w = sl(B.fa_di), fapi_w = sl(B.fa_pi), faoi_w = sl(B.fa_oi);
  const res_w  = sl(B.res),  pos_w  = sl(B.res_pos), mth_w = sl(B.res_months);

  const ca_now = B.ca[li], ca_prv = B.ca[li-1]||null;
  const ca_avg = avg(ca_w), bal_avg = avg(bal_w);
  const ca_def = nNeg(ca_w), ca_len = ca_w.length;
  const fa_avg = avg(fa_w), fa_pos = nPos(fa_w);
  const fadi_avg = avg(fadi_w), fapi_avg = avg(fapi_w), faoi_avg = avg(faoi_w);
  const fadi_sd = sd(fadi_w), fapi_sd = sd(fapi_w);
  const mth_now = B.res_months[li], mth_avg = avg(mth_w), mth_min = mn(mth_w);
  const res_now = B.res[li], res_acc = nPos(res_w);
  const pos_now = B.res_pos[li], pos_first = pos_w[0];

  // ── 01 BOP Overview ──────────────────────────────────────────────────────
  const caMove = ca_prv!==null ? (ca_now > ca_prv ? 'narrowed' : 'widened') : '';
  const caLabel = ca_def > ca_len*0.7 ? 'persistently in deficit' :
                  ca_def > ca_len*0.4 ? 'frequently in deficit' : 'broadly balanced';
  const finMsg  = nPos(kafa_w) >= ca_len*0.75
    ? 'KA+FA inflows have reliably offset the deficit'
    : 'KA+FA financing has been inconsistent, leaving the overall balance dependent on reserves';
  const balMsg  = nNeg(bal_w) > ca_len*0.6
    ? 'reserve drawdowns have been the rule rather than the exception'
    : 'the overall balance has been roughly neutral on average';
  document.getElementById('bopCmt01label').textContent = clabel;
  document.getElementById('bopCmt01').innerHTML =
    p('CA '+caMove+' to '+b(ca_now,'USD mn')+' in '+em(lp)+
      ', vs a '+wlabel+' avg of '+b(ca_avg,'USD mn')+'.') +
    p('The CA has been '+caLabel+' — deficit in '+
      '<strong>'+ca_def+'</strong> of <strong>'+ca_len+'</strong> quarters. '+finMsg+'.') +
    p('Overall balance averaged '+b(bal_avg,'USD mn')+': '+balMsg+'.');

  // ── 02 Current Account Components ───────────────────────────────────────
  const gds_avg = avg(gds_w), svcs_avg = avg(svcs_w);
  const prim_avg = avg(prim_w), sec_avg = avg(sec_w);
  const gds_now = B.ca_goods[li], svcs_now = B.ca_svcs[li];
  const anchor = gds_avg > 0 ? 'Goods surplus (avg '+b(gds_avg,'USD mn')+') anchors the CA, though at '+b(gds_now,'USD mn')+' this quarter it is '+(gds_now < gds_avg ? 'below its average — a softening signal' : 'holding up') :
                               'The goods account is in deficit (avg '+b(gds_avg,'USD mn')+'), removing a traditional CA anchor';
  const structDrag = 'Services (avg '+b(svcs_avg,'USD mn')+') and primary income (avg '+b(prim_avg,'USD mn')+') are structural drags — reflecting shipping and tourism deficits alongside profit remittances to foreign investors.';
  const remitt = sec_avg > 0 ? 'Worker remittances (secondary income avg '+b(sec_avg,'USD mn')+') provide a partial offset.' :
                               'Secondary income offers limited support (avg '+b(sec_avg,'USD mn')+').';
  document.getElementById('bopCmt02label').textContent = clabel;
  document.getElementById('bopCmt02').innerHTML =
    p(anchor+'.') + p(structDrag) + p(remitt);

  // ── 03 Financial Account ─────────────────────────────────────────────────
  const faReliable = fa_pos >= ca_len*0.7 ? 'reliably positive' :
                     fa_pos >= ca_len*0.5 ? 'positive in most quarters but with reversals' : 'volatile and unreliable';
  const fdiMsg = 'FDI averaged '+b(fadi_avg,'USD mn')+
    ' with low volatility (std dev '+bn(fadi_sd/1000,1)+'k), reflecting stable long-term investment commitments.';
  const piMsg  = 'Portfolio flows averaged '+b(fapi_avg,'USD mn')+
    ' but with much higher volatility (std dev '+bn(fapi_sd/1000,1)+'k) — '+
    (fapi_sd > fadi_sd*1.5 ? 'more than '+ bn(fapi_sd/fadi_sd,1)+'× more volatile than FDI, making them the key risk factor in a sentiment shift.' :
     'a meaningful swing factor.');
  const oiMsg  = 'Other investment (avg '+b(faoi_avg,'USD mn')+') captures banking and trade credit flows.';
  document.getElementById('bopCmt03label').textContent = clabel;
  document.getElementById('bopCmt03').innerHTML =
    p('FA was '+faReliable+' (positive in <strong>'+fa_pos+'/'+ca_len+'</strong> quarters), averaging '+b(fa_avg,'USD mn')+'.') +
    p(fdiMsg) + p(piMsg) + p(oiMsg);

  // ── 04 Reserve Assets ────────────────────────────────────────────────────
  const resDir  = res_now > 0 ? 'built up' : 'drew down';
  const resTrend = res_acc >= res_w.length*0.6
    ? 'Reserves were accumulated in <strong>'+res_acc+'/'+res_w.length+'</strong> quarters — a broadly defensive posture'
    : 'Reserve changes have been mixed (accumulation in <strong>'+res_acc+'/'+res_w.length+'</strong> quarters)';
  const posChg  = pos_w.length>=2 ? pos_now - pos_first : null;
  const posMsg  = posChg!==null
    ? 'The stock '+(posChg>=0?'rose':'fell')+' by '+b(Math.abs(posChg/1000),null,1)+'k USD mn over the '+wlabel+'.'
    : '';
  const adequacy = mth_now < 3 ? 'below the 3-month minimum threshold — a serious vulnerability' :
                   mth_now < 5 ? 'above the minimum but approaching the lower bound of comfort (5 months)' :
                   mth_now < 7 ? 'within the comfortable 5–7 month range' : 'well above the 6-month adequacy standard';
  const mthTrend = mth_now < mth_avg - 0.3 ? 'Coverage has been declining — worth monitoring.' :
                   mth_now > mth_avg + 0.3 ? 'Coverage has improved over the window.' : 'Coverage has been relatively stable.';
  document.getElementById('bopCmt04label').textContent = clabel;
  document.getElementById('bopCmt04').innerHTML =
    p('Indonesia '+resDir+' reserves by '+b(Math.abs(res_now),'USD mn')+' in '+em(lp)+'. '+resTrend+'. '+posMsg) +
    p('At '+bn(mth_now)+' months of import coverage — '+adequacy+'. Avg over '+wlabel+': '+bn(mth_avg)+' months (min '+bn(mth_min)+').') +
    p(mthTrend);
}}

function bopDS(label,full,color,opts={{}}) {{
  return {{label,data:(full||[]).slice(-8),borderColor:color,backgroundColor:color,_full:full,...opts}};
}}

function initBOP() {{
  if(bopInited)return;

  // Chart 01: BOP Overview
  bopCharts.push(new Chart(document.getElementById('bopChartBOP'),{{
    type:'bar',
    data:{{labels:B.periods.slice(-8),datasets:[
      bopDS('Current Account',B.ca,'#2563eb',{{backgroundColor:B.ca.map(()=>'rgba(37,99,235,0.72)'),borderWidth:0.5,borderRadius:1,order:2}}),
      bopDS('Capital+Financial',B.ka_fa,'#16a34a',{{backgroundColor:B.ka_fa.map(()=>'rgba(22,163,74,0.68)'),borderWidth:0.5,borderRadius:1,order:3}}),
      bopDS('Net Errors',B.errors,'#d4cec6',{{backgroundColor:'rgba(139,132,124,0.45)',borderWidth:0.5,borderRadius:1,order:4}}),
      bopDS('Overall Balance',B.balance,'#1a1814',{{type:'line',borderWidth:2,pointRadius:2,pointHoverRadius:5,tension:0,fill:false,order:1}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?ctx.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:0}}):''}} USD mn`}}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('USD million'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v/1000).toFixed(0)+'k'}}}}}}}}
  }}));

  // Chart 02: CA Components
  bopCharts.push(new Chart(document.getElementById('bopChartCA'),{{
    type:'bar',
    data:{{labels:B.periods.slice(-8),datasets:[
      bopDS('A. Goods',B.ca_goods,'#2563eb',{{backgroundColor:'rgba(37,99,235,0.72)',borderWidth:0.5,stack:'ca',order:2}}),
      bopDS('B. Services',B.ca_svcs,'#dc2626',{{backgroundColor:'rgba(220,38,38,0.72)',borderWidth:0.5,stack:'ca',order:2}}),
      bopDS('C. Primary Income',B.ca_primary,'#9333ea',{{backgroundColor:'rgba(147,51,234,0.72)',borderWidth:0.5,stack:'ca',order:2}}),
      bopDS('D. Secondary Income',B.ca_second,'#16a34a',{{backgroundColor:'rgba(22,163,74,0.72)',borderWidth:0.5,stack:'ca',order:2}}),
      bopDS('CA Total',B.ca,'#1a1814',{{type:'line',borderWidth:2,pointRadius:2,pointHoverRadius:5,tension:0,fill:false,order:1}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?ctx.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:0}}):''}} USD mn`}}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('USD million'),stacked:true,ticks:{{font:{{family:MONO,size:10}},callback:v=>(v/1000).toFixed(0)+'k'}}}}}}}}
  }}));

  // Chart 03: FA Components
  bopCharts.push(new Chart(document.getElementById('bopChartFA'),{{
    type:'bar',
    data:{{labels:B.periods.slice(-8),datasets:[
      bopDS('1. Direct Investment',B.fa_di,'#0e7490',{{backgroundColor:'rgba(14,116,144,0.72)',borderWidth:0.5,stack:'fa',order:2}}),
      bopDS('2. Portfolio',B.fa_pi,'#7c3aed',{{backgroundColor:'rgba(124,58,237,0.72)',borderWidth:0.5,stack:'fa',order:2}}),
      bopDS('3. Derivatives',B.fa_der,'#ca8a04',{{backgroundColor:'rgba(202,138,4,0.72)',borderWidth:0.5,stack:'fa',order:2}}),
      bopDS('4. Other Investment',B.fa_oi,'#b5460f',{{backgroundColor:'rgba(181,70,15,0.72)',borderWidth:0.5,stack:'fa',order:2}}),
      bopDS('FA Total',B.fa,'#1a1814',{{type:'line',borderWidth:2,pointRadius:2,pointHoverRadius:5,tension:0,fill:false,order:1}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?ctx.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:0}}):''}} USD mn`}}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('USD million'),stacked:true,ticks:{{font:{{family:MONO,size:10}},callback:v=>(v/1000).toFixed(0)+'k'}}}}}}}}
  }}));

  // Chart 04: Reserves
  bopCharts.push(new Chart(document.getElementById('bopChartRes'),{{
    type:'bar',
    data:{{labels:B.periods.slice(-8),datasets:[
      bopDS('Reserve Change',B.res,'#0e7490',{{
        backgroundColor:B.res.map(v=>v===null?null:v>0?'rgba(14,116,144,0.72)':'rgba(181,70,15,0.72)'),
        borderColor:B.res.map(v=>v===null?null:v>0?'#0e7490':'#b5460f'),
        borderWidth:0.5,borderRadius:1,order:2,yAxisID:'y'}}),
      bopDS('Reserve Position',B.res_pos,'#ca8a04',{{type:'line',borderWidth:1.8,pointRadius:0,pointHoverRadius:4,tension:0,fill:false,order:1,yAxisID:'y2',borderDash:[4,3]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legend(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        callbacks:{{label:ctx=>{{const v=ctx.parsed.y;if(v==null)return'';return ctx.datasetIndex===0?` Change: ${{v.toLocaleString('en-US',{{maximumFractionDigits:0}})}} USD mn`:` Position: ${{(v/1000).toFixed(1)}} USD bn`;}}}}}}}},
      scales:{{x:xAxis(),
        y:{{...yAxis('Change (USD mn)'),position:'left',ticks:{{font:{{family:MONO,size:10}},callback:v=>(v/1000).toFixed(0)+'k'}}}},
        y2:{{...yAxis('Position (USD mn)'),position:'right',grid:{{drawOnChartArea:false}},ticks:{{font:{{family:MONO,size:10}},callback:v=>(v/1000).toFixed(0)+'k'}}}}}}}}
  }}));

  // Chart 04b: Months of import
  bopCharts.push(new Chart(document.getElementById('bopChartMonths'),{{
    type:'line',
    data:{{
      labels:B.periods.slice(-8),
      datasets:[
        bopDS('Months of import & official debt coverage',B.res_months,'#7c3aed',{{
          borderWidth:2,pointRadius:3,pointHoverRadius:5,tension:0,fill:false,
          backgroundColor:'rgba(124,58,237,0.08)'
        }}),
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'rgba(26,24,20,0.92)',
          titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
          callbacks:{{label:ctx=>` ${{ctx.parsed.y!=null?ctx.parsed.y.toFixed(2):''}} months`}}
        }}
      }},
      scales:{{
        x:xAxis(),
        y:{{
          title:{{display:true,text:'Months',font:{{family:MONO,size:10}},color:'#8a8780'}},
          ticks:{{font:{{family:MONO,size:10}},callback:v=>v.toFixed(1)}},
          grid:{{color:'rgba(0,0,0,0.05)'}},
          suggestedMin:3, suggestedMax:10
        }}
      }}
    }}
  }}));

  bopInited=true;
  setBOPWindow(8);  // also calls updateBOPCommentary(8)
}}

/* ════════════════════════════════════════════
   FINANCIAL
   ════════════════════════════════════════════ */
let cFinFX=null, cFinEQ=null, finInited=false;

function setFinWindow(key) {{
  const w = FIN[key];
  if(!w) return;
  const fx  = (w.fx  && w.fx.USDIDR)  || {{}};
  const eq  = (w.equity && w.equity.IHSG) || {{}};
  const fp  = fx.periods||[], fv=fx.values||[];
  const ep  = eq.periods||[], ev=eq.values||[];

  // KPIs
  const fLast=fv.length?fv[fv.length-1]:null;
  const fFirst=fv.length?fv[0]:null;
  const eLast=ev.length?ev[ev.length-1]:null;
  const eFirst=ev.length?ev[0]:null;
  const fChg = (fLast&&fFirst&&fFirst!==0)?((fLast/fFirst-1)*100):null;
  const eChg = (eLast&&eFirst&&eFirst!==0)?((eLast/eFirst-1)*100):null;

  document.getElementById('finKpiRate').textContent   = fLast?fLast.toLocaleString('en',{{minimumFractionDigits:0,maximumFractionDigits:0}}):'—';
  document.getElementById('finKpiRateSub').textContent= fp.length?fp[fp.length-1]:'—';
  document.getElementById('finKpiRateChg').textContent= fChg!==null?(fChg>=0?'+':'')+fChg.toFixed(2)+'%':'—';
  document.getElementById('finKpiRateChg').className  = 'kpi-value '+(fChg===null?'':(fChg>0?'neg':'pos'));

  document.getElementById('finKpiIHSG').textContent   = eLast?eLast.toLocaleString('en',{{minimumFractionDigits:0,maximumFractionDigits:0}}):'—';
  document.getElementById('finKpiIHSGSub').textContent= ep.length?ep[ep.length-1]:'—';
  document.getElementById('finKpiIHSGChg').textContent= eChg!==null?(eChg>=0?'+':'')+eChg.toFixed(2)+'%':'—';
  document.getElementById('finKpiIHSGChg').className  = 'kpi-value '+(eChg===null?'':(eChg>=0?'pos':'neg'));

  const wLabel = w.window_label||key;
  document.getElementById('finFxH3').textContent = 'USD/IDR · '+wLabel;
  document.getElementById('finEqH3').textContent = 'IHSG · '+wLabel;

  // Charts
  const accent='#b5460f';
  const blue='#2563eb';
  if(!finInited) {{
    cFinFX = new Chart(document.getElementById('chartFinFX').getContext('2d'),{{
      type:'line',
      data:{{labels:fp,datasets:[lineDS('USD/IDR',fv,accent)]}},
      options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
        plugins:{{legend:{{display:false}},tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',
          titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
          callbacks:{{label:ctx=>` ${{ctx.parsed.y!=null?ctx.parsed.y.toLocaleString('en',{{minimumFractionDigits:0}}):''}} IDR`}}}}}},
        scales:{{x:xAxis(),y:{{...yAxis('IDR per USD'),ticks:{{font:{{family:MONO,size:10}},callback:v=>v.toLocaleString('en',{{minimumFractionDigits:0}})}}}}}}}}
    }});
    cFinEQ = new Chart(document.getElementById('chartFinEQ').getContext('2d'),{{
      type:'line',
      data:{{labels:ep,datasets:[lineDS('IHSG',ev,blue)]}},
      options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
        plugins:{{legend:{{display:false}},tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',
          titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
          callbacks:{{label:ctx=>` ${{ctx.parsed.y!=null?ctx.parsed.y.toLocaleString('en',{{minimumFractionDigits:0}}):''}} pts`}}}}}},
        scales:{{x:xAxis(),y:{{...yAxis('Index points'),ticks:{{font:{{family:MONO,size:10}},callback:v=>v.toLocaleString('en',{{minimumFractionDigits:0}})}}}}}}}}
    }});
    finInited=true;
  }} else {{
    cFinFX.data.labels=fp; cFinFX.data.datasets[0].data=fv; cFinFX.update();
    cFinEQ.data.labels=ep; cFinEQ.data.datasets[0].data=ev; cFinEQ.update();
  }}

  ['finBtn3y','finBtn1m','finBtn1w'].forEach(id=>document.getElementById(id).classList.remove('active'));
  document.getElementById('finBtn'+key).classList.add('active');
  updateFinCommentary(key, fp, fv, ep, ev);
}}

/* ════════════════════════════════════════════
   FINANCIAL COMMENTARY  (window-aware)
   ════════════════════════════════════════════ */
function updateFinCommentary(key, fp, fv, ep, ev) {{
  const avg = a => {{ const v=a.filter(x=>x!=null&&!isNaN(x)); return v.length?v.reduce((s,x)=>s+x,0)/v.length:null; }};
  const mn  = a => {{ const v=a.filter(x=>x!=null&&!isNaN(x)); return v.length?Math.min(...v):null; }};
  const mx  = a => {{ const v=a.filter(x=>x!=null&&!isNaN(x)); return v.length?Math.max(...v):null; }};
  const last= a => {{ const v=a.filter(x=>x!=null&&!isNaN(x)); return v.length?v[v.length-1]:null; }};
  const pct = (a,b) => (a!=null&&b!=null&&b!==0)?((a/b-1)*100):null;
  const fmt0= v => v!=null?v.toLocaleString('en',{{minimumFractionDigits:0,maximumFractionDigits:0}}):'—';
  const fmtp= v => v!=null?(v>=0?'+':'')+v.toFixed(2)+'%':'—';
  const em  = t => '<em>'+t+'</em>';
  const b   = t => '<strong>'+t+'</strong>';
  const p   = t => '<p>'+t+'</p>';

  const fLast=last(fv), fFirst=fv.length?fv[0]:null, fMin=mn(fv), fMax=mx(fv);
  const eLast=last(ev), eFirst=ev.length?ev[0]:null, eMin=mn(ev), eMax=mx(ev);
  const fChg=pct(fLast,fFirst), eChg=pct(eLast,eFirst);
  const fAvg=avg(fv), eAvg=avg(ev);

  // half-period trend
  const h = n => Math.floor(n/2);
  const fH1=avg(fv.slice(0,h(fv.length))), fH2=avg(fv.slice(h(fv.length)));
  const eH1=avg(ev.slice(0,h(ev.length))), eH2=avg(ev.slice(h(ev.length)));

  // IDR direction: higher USD/IDR = weaker Rupiah
  const idrDir  = fChg===null?'unchanged':fChg>1?'depreciated':fChg<-1?'appreciated':'largely stable';
  const idrTrend= (fH1&&fH2)?(fH2>fH1+50?'weakening trend':fH2<fH1-50?'strengthening trend':'broadly stable'):'—';
  const ihsgDir = eChg===null?'unchanged':eChg>1?'gained':eChg<-1?'lost':'largely flat';
  const ihsgTrend=(eH1&&eH2)?(eH2>eH1*1.03?'uptrend':eH2<eH1*0.97?'downtrend':'sideways'):'—';

  // Simple correlation signal: if IDR depreciates AND IHSG falls → outflow signal
  const outflowSignal = fChg!=null&&eChg!=null&&fChg>1&&eChg<-1;
  const inflowSignal  = fChg!=null&&eChg!=null&&fChg<-1&&eChg>1;

  let fxCmt='', eqCmt='', label='';

  if(key==='3y') {{
    // ── 3-YEAR CHART · LAST-12-MONTH COMMENTARY (monthly) ────────────────
    label = 'Last 12 Months · Monthly';
    // Restrict commentary stats to last 12 months even though chart shows 3Y
    const fv12 = fv.slice(-12), fp12 = fp.slice(-12);
    const ev12 = ev.slice(-12), ep12 = ep.slice(-12);
    const fL12=last(fv12), fF12=fv12.length?fv12[0]:null, fMin12=mn(fv12), fMax12=mx(fv12), fAvg12=avg(fv12);
    const eL12=last(ev12), eF12=ev12.length?ev12[0]:null, eMin12=mn(ev12), eMax12=mx(ev12), eAvg12=avg(ev12);
    const fChg12=pct(fL12,fF12), eChg12=pct(eL12,eF12);
    const fH1_12=avg(fv12.slice(0,6)), fH2_12=avg(fv12.slice(6));
    const eH1_12=avg(ev12.slice(0,6)), eH2_12=avg(ev12.slice(6));
    const idrDir12  = fChg12===null?'unchanged':fChg12>1?'depreciated':fChg12<-1?'appreciated':'largely stable';
    const idrTr12   = (fH1_12&&fH2_12)?(fH2_12>fH1_12+50?'weakening':fH2_12<fH1_12-50?'strengthening':'broadly stable'):'broadly stable';
    const ihsgDir12 = eChg12===null?'unchanged':eChg12>1?'gained':eChg12<-1?'lost':'largely flat';
    const ihsgTr12  = (eH1_12&&eH2_12)?(eH2_12>eH1_12*1.03?'uptrend':eH2_12<eH1_12*0.97?'downtrend':'sideways'):'sideways';
    const out12 = fChg12!=null&&eChg12!=null&&fChg12>1&&eChg12<-1;
    const in12  = fChg12!=null&&eChg12!=null&&fChg12<-1&&eChg12>1;
    const startPeriod = fp12.length?fp12[0].slice(0,7):'—';
    const endPeriod   = fp12.length?fp12[fp12.length-1].slice(0,7):'—';

    const fxTrMsg = idrTr12==='weakening'
      ? 'The trend over this period has been one of '+b('Rupiah weakening')+' — the second 6 months averaged '+b(fmt0(fH2_12))+' vs '+b(fmt0(fH1_12))+' in the first, pointing to sustained depreciation pressure.'
      : idrTr12==='strengthening'
      ? 'The Rupiah has been on a '+b('strengthening path')+' over this period — the second 6 months averaged '+b(fmt0(fH2_12))+', improving from '+b(fmt0(fH1_12))+' in the first half.'
      : 'USD/IDR has been '+b('broadly stable')+' over the past year, averaging '+b(fmt0(fAvg12))+' with no persistent directional drift.';

    const eqTrMsg = ihsgTr12==='uptrend'
      ? 'IHSG has been in an '+b('uptrend')+' over the year — the second 6-month average ('+fmt0(eH2_12)+') is above the first ('+fmt0(eH1_12)+'), confirming sustained buying interest.'
      : ihsgTr12==='downtrend'
      ? 'IHSG has been in a '+b('downtrend')+' — the second 6-month average ('+fmt0(eH2_12)+') fell from '+fmt0(eH1_12)+' in the first half, pointing to persistent selling pressure.'
      : 'IHSG has traded in a '+b('sideways')+' pattern over the year, averaging '+b(fmt0(eAvg12))+' with no clear directional trend.';

    fxCmt = p('Over the past 12 months ('+startPeriod+' – '+endPeriod+'), the Rupiah has '+b(idrDir12)+' by '+b(fmtp(fChg12))+' against the USD, from '+b(fmt0(fF12))+' to '+b(fmt0(fL12))+'.')
           +p(fxTrMsg+' The year\\'s range was '+b(fmt0(fMin12))+' – '+b(fmt0(fMax12))+'.')
           +p('At '+b(fmt0(fL12))+', the Rupiah is '+(fL12>fAvg12?'above its 12-month average ('+fmt0(fAvg12)+') — weaker than the annual mean':'below its 12-month average ('+fmt0(fAvg12)+') — stronger than the annual mean')+'. The 3-year chart provides the longer-run context.');

    eqCmt = p('IHSG has '+b(ihsgDir12)+' by '+b(fmtp(eChg12))+' over the past 12 months, from '+b(fmt0(eF12))+' to '+b(fmt0(eL12))+'. The year\\'s range: '+b(fmt0(eMin12))+' – '+b(fmt0(eMax12))+'.')
           +p(eqTrMsg)
           +(out12?p(b('Joint signal: ')+' Both Rupiah and IHSG have weakened over the past year — a pattern consistent with net foreign portfolio outflows from Indonesian assets.')
           :in12?p(b('Joint signal: ')+' Rupiah appreciation and IHSG gains coincide over the past year — pointing to net inflows and sustained risk appetite for Indonesian assets.')
           :p('Rupiah and IHSG have moved in mixed directions over the past year, suggesting the drivers are idiosyncratic rather than a unified inflow/outflow cycle.'));

  }} else if(key==='1m') {{
    // ── 1-MONTH TACTICAL VIEW (daily) ────────────────────────────────────
    label = 'Monthly View · Daily';
    const pts = fv.length;
    const fxMid = avg(fv);
    const fxVol = fv.length>1 ? (() => {{ const m=fxMid; return Math.sqrt(fv.reduce((s,v)=>s+(v-m)**2,0)/fv.length); }})() : 0;
    const volDesc = fxVol > 200 ? 'elevated daily volatility' : fxVol > 80 ? 'moderate volatility' : 'low volatility';

    fxCmt = p('This month USD/IDR has moved '+b(fmtp(fChg))+', from '+b(fmt0(fFirst))+' at the start of the period to '+b(fmt0(fLast))+' at the latest reading.')
           +p('The month\\'s trading range was '+b(fmt0(fMin))+' – '+b(fmt0(fMax))+' (a '+b(fmt0(fMax-fMin))+' IDR band), reflecting '+b(volDesc)+'. '
             +(fLast===fMax?'The Rupiah is currently at its '+em('weakest')+' point of the month — pressure on the currency has not yet reversed.':fLast===fMin?'The Rupiah is at its '+em('strongest')+' point of the month, having recovered from earlier lows.':'The current rate of '+fmt0(fLast)+' sits within the month\\'s range, with room in both directions.'))
           +p(fChg!==null&&Math.abs(fChg)>2
             ? 'A move of '+b(fmtp(fChg))+' within a single month is '+b('significant')+' by historical standards. Typical monthly IDR moves cluster within ±1–2%. This suggests an identifiable catalyst — monitor BI policy, global USD sentiment, and capital flow data.'
             : 'The monthly move of '+b(fmtp(fChg))+' is within the normal range of month-to-month IDR fluctuation. No structural break is indicated.');

    const eqVol = ev.length>1 ? (() => {{ const m=avg(ev); return Math.sqrt(ev.reduce((s,v)=>s+(v-m)**2,0)/ev.length); }})() : 0;
    const eqVolDesc = eqVol > 150 ? 'high daily volatility' : eqVol > 50 ? 'moderate daily swings' : 'relatively calm trading';
    eqCmt = p('IHSG has '+b(ihsgDir)+' by '+b(fmtp(eChg))+' this month, from '+b(fmt0(eFirst))+' to '+b(fmt0(eLast))+'.')
           +p('The intra-month range was '+b(fmt0(eMin))+' – '+b(fmt0(eMax))+', with '+eqVolDesc+'. '
             +(eLast===eMax?'The index is currently at its '+em('monthly high')+' — buying momentum has been sustained through the period.':eLast===eMin?'The index is at its '+em('monthly low')+', with selling pressure most recent. Watch for support levels.':'At '+fmt0(eLast)+', the index sits mid-range, with neither a clear breakout nor a breakdown.'))
           +(outflowSignal?p(em('Joint signal: ')+' Both the Rupiah and equities have weakened this month. The co-movement points to foreign portfolio outflows — a risk-off dynamic where domestic assets are being sold together.')
           :inflowSignal?p(em('Joint signal: ')+' Rupiah strengthening and IHSG gains are occurring simultaneously — a sign of foreign inflows and improved risk appetite toward Indonesian assets.')
           :p('IDR and IHSG have moved in different directions this month, suggesting domestic-driven equity flows rather than pure FX-linked portfolio positioning.'));

  }} else {{
    // ── 1-WEEK INTRAWEEK VIEW (hourly) ────────────────────────────────────
    label = 'Weekly View · Hourly';
    const latestDate = fp.length?fp[fp.length-1].slice(0,10):'—';
    const latestTime = fp.length?fp[fp.length-1].slice(11,16):'—';

    fxCmt = p('Over the past week\\'s trading sessions, USD/IDR has ranged from '+b(fmt0(fMin))+' to '+b(fmt0(fMax))+'. The most recent reading is '+b(fmt0(fLast))+' ('+latestDate+(latestTime?' · '+latestTime:'')+').')
           +p(fChg!==null
             ?'From the week\\'s first observation the Rupiah has '+b(idrDir)+' by '+b(fmtp(fChg))+'. '+(Math.abs(fChg)>1?'A move of this size within a single week is notable — intraweek FX moves of >1% are uncommon outside of event-driven catalysts (BI decisions, US payrolls, global risk-off episodes).':'The weekly move is within normal bounds for IDR, consistent with routine liquidity ebbs and flows rather than a directional catalyst.')
             :'Insufficient data to compute week-on-week change.')
           +p('Note: USD/IDR trades 24 hours on weekdays. Hourly readings reflect OTC interbank market prices and may include thin-liquidity periods outside Asian trading hours (Jakarta: GMT+7).');

    const sessionsCount = [...new Set((ep||[]).map(t=>t.slice(0,10)))].length;
    eqCmt = p('IHSG data covers '+b(sessionsCount+' trading session'+(sessionsCount!==1?'s':''))+' this week. The latest reading is '+b(fmt0(eLast))+', with a weekly range of '+b(fmt0(eMin))+' – '+b(fmt0(eMax))+'.')
           +p(eChg!==null
             ?'From the week\\'s open, IHSG has '+b(ihsgDir)+' by '+b(fmtp(eChg))+'. '+(Math.abs(eChg)>2?'A weekly equity move of this magnitude warrants attention — check for domestic catalysts (BI, government announcements) or external shocks (Fed, commodity prices, regional risk-off).':'The weekly move is modest, consistent with normal session-by-session fluctuation at the IDX.')
             :'Insufficient data to compute week-on-week change.')
           +p('Note: IDX trading hours are Mon–Fri, 09:00–15:00 WIB (02:00–08:00 UTC). Hourly readings outside these hours will show the prior session\\'s closing price.')
           +(outflowSignal?p(em('This week: ')+' Both Rupiah and IHSG are weaker — the joint move is consistent with foreign selling of Indonesian assets. Typically precedes broader risk-off positioning if sustained.')
           :inflowSignal?p(em('This week: ')+' Rupiah appreciation alongside IHSG gains — risk-on inflow signal. If sustained into month-end, may reflect improving portfolio positioning toward Indonesia.'):'');
  }}

  document.getElementById('finFxCmtLabel').textContent = label;
  document.getElementById('finEqCmtLabel').textContent = label;
  document.getElementById('cmtFinFXtext').innerHTML = fxCmt;
  document.getElementById('cmtFinEQtext').innerHTML = eqCmt;
}}

/* ════════════════════════════════════════════
   NAVIGATION
   ════════════════════════════════════════════ */
function showSection(sec) {{
  ['sectionGDP','sectionBOP','sectionFin'].forEach(id=>
    document.getElementById(id).style.display='none');
  ['navGDP','navBOP','navFin'].forEach(id=>
    document.getElementById(id).classList.remove('active'));
  const secMap={{gdp:'sectionGDP',bop:'sectionBOP',fin:'sectionFin'}};
  const navMap={{gdp:'navGDP',bop:'navBOP',fin:'navFin'}};
  document.getElementById(secMap[sec]).style.display='';
  document.getElementById(navMap[sec]).classList.add('active');
  if(sec==='bop'&&!bopInited) initBOP();
  if(sec==='fin') setFinWindow('3y');
}}

// Init GDP default window
setGDPWindow(0);
</script>
</body>
</html>
"""

html = HEAD + NAV + GDP_SECTION + BOP_SECTION + FINANCIAL_SECTION + FOOTER + JS

# Clean up sentinel
import os as _os
_os.remove(os.path.join(os.path.dirname(__file__), '_combined_template.py'))

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written: {out_path}  ({os.path.getsize(out_path)//1024} KB)")
