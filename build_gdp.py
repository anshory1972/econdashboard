"""GDP dashboard builder → html/econdashboard.html"""
import pandas as pd, numpy as np, json, os, re

CLEAN = r"C:\work\economist\rawdata\seki\clean"
HTML  = r"C:\work\economist\html"
os.makedirs(HTML, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# GDP DATA
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
# Exact match, not a substring search: 'Pembentukan Modal Tetap Domestik Bruto'
# also contains 'domestik bruto' and sorts first, which silently made GFCF the
# contribution denominator and inflated every demand contribution ~3.3x.
gdp_total_name_exp = 'Produk Domestik Bruto'
assert gdp_total_name_exp in set(exp['series']), \
    f"GDP total missing from expenditure CSV; have: {sorted(exp['series'].unique())}"
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
# This filter drops unmatched names silently, which would remove a sector from the
# chart, the breadth count and the commentary while "n/17" kept printing. Fail loud.
assert len(sec_avail) == len(SEC_MAP), f"dropped sectors: {set(SEC_MAP) - set(sec_avail)}"
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
assert len(mfg_avail) == len(MFG_MAP), f"dropped subsectors: {set(MFG_MAP) - set(mfg_avail)}"
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

def exp_series(name):
    """One expenditure series, period-indexed, filtered as the CEIC frame was.

    These 13 sub-components used to come from a manual CEIC export; they now come
    from the same BPS table as everything else (var 1956). CEIC arrived already
    trimmed to 2015-Q1 — the BPS frame carries full history from 2010, so the
    filter has to be applied here or pivot() pads 2011-2014 with zeros and draws
    them as real readings at the left edge of the household and GFCF charts.
    """
    s = (exp[exp['series'] == name].sort_values('period')
         .set_index('period')['value'])
    if s.empty:
        raise KeyError(f"missing expenditure series: {name!r}")
    return s[s.index >= '2015-Q1']

HH_TOTAL = 'Rumah Tangga'
HH_MAP   = {
    'RT: Makanan dan Minuman, Selain Restoran':'Food & Beverages',
    'RT: Pakaian, Alas Kaki dan Jasa Perawatannya':'Apparel & Footwear',
    # BPS 130 is Perumahan *dan* Perlengkapan — housing plus equipment. CEIC
    # labelled it 'Equipments', which understated what the category covers.
    'RT: Perumahan dan Perlengkapan Rumahtangga':'Housing & Equipment',
    'RT: Kesehatan dan Pendidikan':'Health & Education',
    'RT: Transportasi dan Komunikasi':'Transport & Comms',
    'RT: Restoran dan Hotel':'Restaurant & Hotel',
    'RT: Lainnya':'Other Consumption',
}
hh_total = exp_series(HH_TOTAL)
hh_growth_records, hh_contrib_records = [], []
for p, v in (hh_total.pct_change(4)*100).dropna().items():
    hh_growth_records.append({'period':p,'component':'Household Total','yoy':round(v,2)})
for raw, label in HH_MAP.items():
    comp = exp_series(raw)
    for p, v in (comp.pct_change(4)*100).dropna().items():
        hh_growth_records.append({'period':p,'component':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/hh_total.shift(4)*100).dropna().items():
        hh_contrib_records.append({'period':p,'component':label,'contribution':round(v,3)})
hh_growth = pd.DataFrame(hh_growth_records)
hh_contrib = pd.DataFrame(hh_contrib_records)

GFCF_TOTAL = 'Pembentukan Modal Tetap Domestik Bruto'
GFCF_MAP   = {
    'PMTB: Bangunan':'Buildings & Structures','PMTB: Mesin dan Perlengkapan':'Machine & Equipment',
    'PMTB: Kendaraan':'Vehicles','PMTB: Peralatan Lainnya':'Other Equipment',
    'PMTB: CBR':'Biological Resources',
    'PMTB: Produk Kekayaan Intelektual':'Intellectual Property',
}
gfcf_total = exp_series(GFCF_TOTAL)
gfcf_growth_records, gfcf_contrib_records = [], []
for p, v in (gfcf_total.pct_change(4)*100).dropna().items():
    gfcf_growth_records.append({'period':p,'component':'GFCF Total','yoy':round(v,2)})
for raw, label in GFCF_MAP.items():
    comp = exp_series(raw)
    for p, v in (comp.pct_change(4)*100).dropna().items():
        gfcf_growth_records.append({'period':p,'component':label,'yoy':round(v,2)})
    for p, v in ((comp-comp.shift(4))/gfcf_total.shift(4)*100).dropna().items():
        gfcf_contrib_records.append({'period':p,'component':label,'contribution':round(v,3)})

hh_yoy_series   = (hh_total.pct_change(4)*100).dropna()
gfcf_yoy_series = (gfcf_total.pct_change(4)*100).dropna()
mfg_yoy_series  = (mfg_total.pct_change(4)*100).dropna()

# Equipment as a group: machinery + vehicles + other equipment. Growth rates
# cannot be summed, so this is derived from levels and passed to the JS
# separately. It replaces a machinery-only test that reported "buildings lead"
# in quarters where equipment as a whole was in fact growing faster.
equip_total      = (exp_series('PMTB: Mesin dan Perlengkapan')
                    + exp_series('PMTB: Kendaraan')
                    + exp_series('PMTB: Peralatan Lainnya'))
equip_yoy_series = (equip_total.pct_change(4)*100).dropna()
gfcf_growth = pd.DataFrame(gfcf_growth_records)
gfcf_contrib = pd.DataFrame(gfcf_contrib_records)

# ── Snapshot commentary ───────────────────────────────────────────────────────
# Only the "Latest Quarter" snapshot text is generated here. The eight
# time-series comment boxes are written at runtime by updateGDPCommentary() in
# the JS below, because they have to recompute on every window toggle. A second
# Python-side copy of that prose used to be generated and embedded here; it was
# never read — the JS overwrote all eleven divs on init — so it has been removed
# rather than left as a copy that looks editable but changes nothing on the page.
def bold(x, suffix='%', decimals=2, sign=False):
    fmt = f'{x:+.{decimals}f}' if sign else f'{x:.{decimals}f}'
    return f'<strong>{fmt}{suffix}</strong>'
def hi(text): return f'<em>{text}</em>'
def vs_avg(v, avg, unit='%'):
    diff = v - avg
    return f"{'above' if diff>=0 else 'below'} its 8Q avg ({bold(avg,unit)}) by <strong>{abs(diff):.2f}{unit}</strong>"

g8=gdp.tail(8); q=g8.iloc[-1]['period']; g_now=g8.iloc[-1]['yoy']
g_prev=g8.iloc[-2]['yoy']; g_avg8=g8['yoy'].mean(); g_swing=g_now-g_prev

ec8=exp_contrib[exp_contrib['period'].isin(g8['period'].tolist())]
ec_q=ec8[ec8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)

sg8=sec_growth[sec_growth['period'].isin(g8['period'].tolist())]
sg_q=sg8[sg8['period']==q].set_index('sector')['yoy'].sort_values(ascending=False)

sc8=sec_contrib[sec_contrib['period'].isin(g8['period'].tolist())]
sc_q=sc8[sc8['period']==q].set_index('sector')['contribution'].sort_values(ascending=False)

mg8=mfg_growth[mfg_growth['period'].isin(g8['period'].tolist())]
mg_q=mg8[mg8['period']==q].set_index('subsector')['yoy'].sort_values(ascending=False)
mc8=mfg_contrib[mfg_contrib['period'].isin(g8['period'].tolist())]
mc_q=mc8[mc8['period']==q].set_index('subsector')['contribution'].sort_values(ascending=False)
mfg_now=round(float(mfg_yoy_series.get(q,0)),2)

hh8=hh_growth[hh_growth['period'].isin(g8['period'].tolist())&(hh_growth['component']!='Household Total')]
hh_q=hh8[hh8['period']==q].set_index('component')['yoy'].sort_values(ascending=False)
hh_now=round(float(hh_yoy_series.get(q,0)),2)
hc8=hh_contrib[hh_contrib['period'].isin(g8['period'].tolist())]
hc_q=hc8[hc8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)

gf8=gfcf_growth[gfcf_growth['period'].isin(g8['period'].tolist())&(gfcf_growth['component']!='GFCF Total')]
gf_q=gf8[gf8['period']==q].set_index('component')['yoy'].sort_values(ascending=False)
gf_neg=[c for c in gf_q.index if gf_q[c]<0]
gf_now=round(float(gfcf_yoy_series.get(q,0)),2)
gc8=gfcf_contrib[gfcf_contrib['period'].isin(g8['period'].tolist())]
gc_q=gc8[gc8['period']==q].set_index('component')['contribution'].sort_values(ascending=False)

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
    return (f"<p>In {hi(q)}, {n_pos}/{len(sec_avail)} sectors grew; {n_neg} contracted.</p>"
        f"<p><strong>Top 3:</strong> "+", ".join(f"{hi(sg_q.index[i])} ({bold(sg_q.iloc[i])})" for i in range(3))+".</p>"
        +f"<p><strong>Bottom 3:</strong> "+", ".join(f"{hi(sg_q.index[-(i+1)])} ({bold(sg_q.iloc[-(i+1)])})" for i in range(3))+".</p>"
        +(f"<p>Manufacturing ranked {mfg_rank}/{len(sec_avail)} at {bold(round(float(sg_q.get('Manufacturing',0)),2))}.</p>" if mfg_rank else "")
        +f"<p>Top GDP contributor: {hi(sc_q.index[0])} ({bold(sc_q.iloc[0],' pp',sign=True)}).</p>")
def snap_cmt_mfg():
    mfg8_avg=round(float(mfg_yoy_series.reindex(g8['period'].tolist()).mean()),2)
    n_pos=sum(1 for v in mg_q.values if v>=0); n_neg=sum(1 for v in mg_q.values if v<0)
    return (f"<p>Manufacturing {bold(mfg_now)} in {hi(q)}, {vs_avg(mfg_now,mfg8_avg)}.</p>"
        f"<p>{n_pos}/{len(mfg_avail)} subsectors grew; {n_neg} contracted.</p>"
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
equip_g=[round(float(equip_yoy_series.get(p,0) or 0),3) for p in gfcf_g_periods]

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
    'equip_g':equip_g,
    'latest_period':latest_period,'latest_yoy':latest_yoy,'prev_yoy':prev_yoy,'delta':delta,
    'snap':snap})

EXP_COLORS={'GDP':'#1a1814','Household Consumption':'#2563eb','Government':'#16a34a','Investment (PMTB)':'#d97706','Exports (Goods)':'#7c3aed','Imports (Goods)':'#dc2626'}
SEC_COLORS={'Agriculture':'#15803d','Mining & Quarrying':'#92400e','Manufacturing':'#ea580c','Electricity & Gas':'#ca8a04','Water & Waste':'#4d7c0f','Construction':'#0e7490','Trade':'#2563eb','Transport & Storage':'#7c3aed','Accommodation & Food':'#be185d','Info & Comms':'#0891b2','Finance & Insurance':'#db2777','Real Estate':'#9333ea','Business Services':'#0369a1','Government Admin':'#374151','Education':'#065f46','Health & Social':'#991b1b','Other Services':'#6b7280'}
MFG_COLORS={'Food & Beverages':'#15803d','Tobacco':'#374151','Textiles & Apparel':'#be185d','Leather & Footwear':'#92400e','Wood Products':'#4d7c0f','Paper & Printing':'#0369a1','Coal & Oil Refining':'#1a1814','Chemicals & Pharma':'#7c3aed','Rubber & Plastics':'#0e7490','Non-metallic Minerals':'#b45309','Basic Metals':'#6b7280','Metal Products & Electronics':'#2563eb','Machinery':'#0891b2','Transport Equipment':'#ea580c','Furniture':'#9333ea','Other Manufacturing':'#db2777'}
HH_COLORS={'Household Total':'#1a1814','Food & Beverages':'#15803d','Apparel & Footwear':'#be185d','Housing & Equipment':'#d97706','Health & Education':'#7c3aed','Transport & Comms':'#2563eb','Restaurant & Hotel':'#ea580c','Other Consumption':'#6b7280'}
GFCF_COLORS={'GFCF Total':'#1a1814','Buildings & Structures':'#0e7490','Machine & Equipment':'#ea580c','Vehicles':'#ca8a04','Other Equipment':'#6b7280','Biological Resources':'#15803d','Intellectual Property':'#7c3aed'}

print(f"GDP: {latest_period}, YoY {latest_yoy:+.2f}%")

# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════
out_path = os.path.join(HTML, "econdashboard.html")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indonesia Economic Dashboard — GDP</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{--ink:#1a1814;--ink-light:#4a4740;--ink-faint:#8a8780;--paper:#f5f2ec;--paper-warm:#ede9e0;--paper-card:#faf8f4;--rule:#d8d3c8;--accent:#b5460f;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:300;font-size:15px;line-height:1.7;}
/* ── Main nav ── */
#mainNav{background:#1a1814;border-bottom:3px solid var(--accent);position:sticky;top:0;z-index:100;}
.mn-brand-row{padding:.6rem 2rem .4rem;text-align:center;}
.mn-brand{font-family:'DM Mono',monospace;font-size:13px;color:var(--paper);letter-spacing:.2em;text-transform:uppercase;font-weight:500;}
.mn-brand em{font-style:normal;color:var(--accent);margin-right:.6em;}
.mn-tabs-row{padding:.3rem 2rem .5rem;display:flex;gap:3px;justify-content:center;}
.mn-tab{font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase;
          padding:5px 20px;border-radius:3px;cursor:pointer;border:none;background:transparent;
          color:rgba(245,242,236,.45);transition:all .15s;text-decoration:none;display:inline-block;}
.mn-tab:hover{color:var(--paper);background:rgba(255,255,255,.08);}
.mn-tab.active{background:var(--accent);color:var(--paper);}
.mn-tab.disabled{color:rgba(245,242,236,.18);cursor:default;pointer-events:none;}
/* ── Shared header ── */
header{background:var(--ink);color:var(--paper);padding:2.5rem 3rem 2rem;text-align:center;}
.header-label{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}
header h1{font-family:'Playfair Display',serif;font-size:2rem;font-weight:400;line-height:1.2;margin-bottom:1rem;}
header h1 em{font-style:italic;color:rgba(245,242,236,.6);}
.header-meta{display:flex;gap:2rem;flex-wrap:wrap;justify-content:center;}
.hm{font-family:'DM Mono',monospace;font-size:11px;color:rgba(245,242,236,.5);letter-spacing:.08em;}
.hm span{color:rgba(245,242,236,.9);display:block;font-size:13px;margin-top:2px;}
/* ── Window bar ── */
.window-bar{position:sticky;top:78px;z-index:50;background:var(--paper-warm);border-bottom:1px solid var(--rule);padding:.5rem 2rem .6rem;display:flex;flex-direction:column;align-items:center;gap:.35rem;}
.window-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);}
.window-btns{display:flex;gap:4px;}
.wbtn{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;padding:4px 14px;border-radius:2px;cursor:pointer;border:1px solid var(--rule);background:var(--paper-card);color:var(--ink-light);transition:all .15s;}
.wbtn:hover{background:var(--paper-warm);border-color:var(--ink-faint);color:var(--ink);}
.wbtn.active{background:var(--ink);border-color:var(--ink);color:var(--paper);font-weight:500;}
/* ── Layout ── */
.container{max-width:1200px;margin:0 auto;padding:2rem 2rem 5rem;}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:4px;overflow:hidden;margin-bottom:2.5rem;}
.kpi{background:var(--paper-card);padding:1.25rem 1.5rem;}
.kpi-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.4rem;}
.kpi-value{font-family:'Playfair Display',serif;font-size:2rem;font-weight:400;}
.kpi-value.pos{color:#2d5a27;}.kpi-value.neg{color:#b5460f;}
.kpi-sub{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);margin-top:.3rem;}
.block{margin-bottom:3rem;}
.block-header{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}
.block-num{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}
.block-title{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}
.chart-wrap,.chart-full{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.5rem;}
.chart-wrap h3,.chart-full h3{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:1rem;}
.chart-note{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);margin-top:.75rem;}
.chart-with-comment{display:flex;gap:1.5rem;align-items:flex-start;}
.chart-with-comment .chart-full,.chart-with-comment .chart-wrap{flex:1;min-width:0;}
/* GDP time-series comment boxes always visible */
.comment-box{display:block;}
.comment-box{width:260px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}
.comment-box .cb-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}
.comment-box p{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}
.comment-box p:last-child{margin-bottom:0;}
.comment-box strong{color:var(--ink);font-weight:500;}.comment-box em{font-style:normal;color:var(--ink);font-weight:500;}
/* Snapshot */
.snap-group{margin-bottom:3rem;}.snap-group-header{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}
.snap-group-num{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}
.snap-group-title{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}
.snap-body{display:flex;gap:1.5rem;align-items:flex-start;}
.snap-comment{width:260px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}
.snap-comment .cb-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}
.snap-comment p{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}
.snap-comment strong{color:var(--ink);font-weight:500;}.snap-comment em{font-style:normal;color:var(--ink);font-weight:500;}
.snap-charts{flex:1;min-width:0;display:flex;flex-direction:column;gap:1.25rem;}
.snap-chart-wrap{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.25rem;}
.snap-chart-wrap h3{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.75rem;}
footer{background:var(--paper-warm);border-top:1px solid var(--rule);padding:1.25rem 3rem;font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;}
@media(max-width:900px){
  .chart-with-comment,.snap-body{flex-direction:column;}
  .comment-box,.snap-comment{width:100%;}
  .kpi-row{grid-template-columns:repeat(2,1fr);}
  header{padding:2rem 1.5rem;}
}
</style>
</head>
<body>
"""

NAV = """
<div id="mainNav">
  <div class="mn-brand-row">
    <span class="mn-brand"><em>AAY</em>Indonesia Economic Dashboard</span>
  </div>
  <div class="mn-tabs-row">
    <a href="econdashboard.html" class="mn-tab active">GDP</a>
    <a href="bop.html" class="mn-tab">BoP</a>
    <a href="financial.html" class="mn-tab">Financial</a>
    <span class="mn-tab disabled">Prices</span>
    <span class="mn-tab disabled">Fiscal</span>
  </div>
</div>
"""

FOOTER = """
<footer>
  <span>Indonesia Economic Dashboard</span>
  <span>Source: BPS (Statistics Indonesia), WebAPI</span>
</footer>
"""

GDP_SECTION = f"""
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
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Dashed = 2015–2019 pre-COVID mean ({precovid_mean:.2f}%). Source: BPS (var 65).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGDPtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02</span><h2 class="block-title">Demand Components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Component (%)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtExpGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:300px"><canvas id="chartExpContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Imports sign-reversed. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtExpContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02b</span><h2 class="block-title">Household Consumption — Sub-components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtHhGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to Household Consumption Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartHhContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtHhContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">02c</span><h2 class="block-title">Gross Fixed Capital Formation — Sub-components</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth (%)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGfcfGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GFCF Growth (pp)</h3>
        <div style="position:relative;height:340px"><canvas id="chartGfcfContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: BPS (var 1956).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtGfcfContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">03</span><h2 class="block-title">Supply — Sectoral (17 sectors)</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Sector (%)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecGrowth"></canvas></div>
        <div class="chart-note">Quarterly YoY, constant 2010 prices. Source: BPS (var 65).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtSecGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to GDP Growth (pp)</h3>
        <div style="position:relative;height:480px"><canvas id="chartSecContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: BPS (var 65).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtSecContribtext"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">04</span><h2 class="block-title">Manufacturing — Subsector Drill-down</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem;">
      <div class="chart-wrap"><h3>YoY Growth by Subsector (%)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgGrowth"></canvas></div>
        <div class="chart-note">16 subsectors, quarterly YoY, constant 2010 prices. Source: BPS (var 65).</div>
      </div>
      <div class="comment-box"><div class="cb-label">Latest · {latest_period}</div><div id="cmtMfgGrowthtext"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-wrap"><h3>Contribution to Manufacturing Growth (pp)</h3>
        <div style="position:relative;height:460px"><canvas id="chartMfgContrib"></canvas></div>
        <div class="chart-note">Quarterly, constant 2010 prices. Source: BPS (var 65).</div>
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
"""

JS = f"""
<script>
const D = {gdp_js};
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

  const sl = arr => n?(arr||[]).slice(-n):(arr||[]);
  const slP = vals => n?(vals||[]).slice(-n):(vals||[]);

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

  const b  = (v,dec)=>{{if(v==null||isNaN(v))return'—';dec=dec??2;return'<strong>'+(v>=0?'+':'')+v.toFixed(dec)+'%</strong>';}};
  const bp = (v,dec)=>{{if(v==null||isNaN(v))return'—';dec=dec??2;return'<strong>'+(v>=0?'+':'')+v.toFixed(dec)+' pp</strong>';}};
  const bn = (v,dec)=>{{dec=dec??2;return'<strong>'+v.toFixed(dec)+'%</strong>';}};
  const em = t=>'<em>'+t+'</em>';
  const p  = t=>'<p>'+t+'</p>';

  document.querySelectorAll('.comment-box .cb-label').forEach(el=>el.textContent=clabel);

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
  const hhC_lead=last(slP((D.exp_c_data||{{}})['Household Consumption']||[]));
  const invC_lead=last(slP((D.exp_c_data||{{}})['Investment (PMTB)']||[]));
  const lead=hhC_lead>=invC_lead?'consumption-led':'investment-led';

  const hhSynth=hhTr==='accelerating'
    ?'Household consumption at '+b(hhG)+' is accelerating — rising incomes and confidence are translating into stronger spending. A bullish signal for domestic demand.'
    :hhTr==='moderating'
    ?'Household consumption has moderated to '+b(hhG)+' (window avg '+bn(hhAvg)+') — the consumer engine is losing steam. Watch for pass-through from real wage trends.'
    :'Household consumption is steady at '+b(hhG)+' (window avg '+bn(hhAvg)+'). Steady is not the same as immaterial: at '+bp(hhC_lead)+' it is still the largest single contribution to the '+b(g)+' headline. A stable growth rate on a ~56% GDP share is what holds the expansion up.';
  const invSynth=invTr==='accelerating'
    ?'Investment at '+b(invG)+' is accelerating — companies are expanding capacity, a leading indicator for future output potential.'
    :invTr==='moderating'
    ?'Investment at '+b(invG)+' is moderating (window avg '+bn(invAvg)+') — capex appetite is cooling, which could limit future growth potential if sustained.'
    :'Investment at '+b(invG)+' is holding above its window average of '+bn(invAvg)+', contributing '+bp(invC_lead)+' to the headline — the second-largest source of growth after households.';

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
  // Government consumption is lumpy. Judge it against its own recent norm in
  // contribution terms — a large YoY growth rate on a ~7% GDP share can still be
  // immaterial, and a bare percentage tells the reader nothing either way.
  const govCavg=avg(slP(ecD['Government']||[]));
  const fiscalMsg=(!isNaN(govC)&&!isNaN(govCavg)&&govC>govCavg*1.75&&govC>0.5)
    ?'Government consumption is running well clear of its own recent norm, contributing '+bp(govC)+' against a window average of '+bp(govCavg)+'. A fiscal impulse this size is the main reason the growth mix looks broad this quarter — and it is the least durable component of the four: government spending is lumpy, and quarters like this typically give some of it back.'
    :'';
  const concMsg=Math.abs(hhC)>(Math.abs(invC)+Math.abs(govC))
    ?'Consumption is the dominant engine — growth quality depends heavily on household income trends and consumer sentiment. A single-source dependency worth monitoring.'
    :'Growth is reasonably distributed across demand components, reducing vulnerability to any single source weakening.'+(fiscalMsg?' That breadth rests partly on the government impulse noted above, so it may prove temporary.':'');

  document.getElementById('cmtExpContribtext').innerHTML=
    p('Household consumption contributes '+bp(hhC)+' to the '+b(g)+' headline — roughly <strong>'+hhShare+'%</strong> of total growth. Investment adds '+bp(invC)+'; government '+bp(govC)+'.') +
    p('Net trade (exports '+bp(expC)+' plus imports '+bp(impC)+') is a <strong>'+(netT>=0?'tailwind':'headwind')+'</strong> of '+bp(netT)+'. '+(netT<-0.5?'Strong import growth typically signals healthy domestic demand, but it mechanically reduces the headline GDP number. The drag from imports here is a sign of economic strength, not weakness.':netT>0.5?'A positive trade contribution adds to the headline without relying solely on domestic demand — a more balanced growth mix.':'Net trade is broadly neutral.'))+
    (fiscalMsg?p(fiscalMsg):'')+
    p(concMsg);

  // ── 02b HH — YoY Growth ──────────────────────────────────────────────────
  const hgD=D.hh_g_data;
  const transG=last(slP(hgD['Transport & Comms']||[])), restG=last(slP(hgD['Restaurant & Hotel']||[]));
  const foodG=last(slP(hgD['Food & Beverages']||[])), housG=last(slP(hgD['Housing & Equipment']||[]));
  const healG=last(slP(hgD['Health & Education']||[])), appG=last(slP(hgD['Apparel & Footwear']||[]));
  const hgTop=topN(hgD,2).filter(x=>x.key!=='Household Total');
  const hgBot=botN(hgD,1).filter(x=>x.key!=='Household Total');
  // Housing & Equipment is excluded from both baskets: it is predominantly
  // housing, which is neither discretionary nor a cost-of-living necessity in
  // the sense this comparison is testing. It is reported on its own below.
  const discr=avg([transG,restG,appG].filter(v=>!isNaN(v)));
  const nonDiscr=avg([foodG,healG].filter(v=>!isNaN(v)));
  const confMsg=discr>nonDiscr
    ?'Discretionary categories (transport, dining, apparel) are growing '+bn(discr)+' against '+bn(nonDiscr)+' for necessities (food, health &amp; education) — a sign of <strong>improving consumer confidence</strong> and real purchasing power.'
    :'Necessities (food, health &amp; education) are growing '+bn(nonDiscr)+' against '+bn(discr)+' for discretionary categories — consumers are <strong>prioritising essentials</strong> over upgrades, which can signal caution or cost-of-living pressure.';

  document.getElementById('cmtHhGrowthtext').innerHTML=
    p('Top HH components this quarter: '+hgTop.map(x=>em(x.key)+' '+b(x.v)).join(', ')+'. Lagging: '+hgBot.map(x=>em(x.key)+' '+b(x.v)).join(', ')+'.') +
    p(confMsg) +
    p('Housing & Equipment — the second-largest household category — grew '+b(housG)+'.') +
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
    p('Food & Beverages contributes '+bp(foodC)+' (window avg '+bp(foodCavg)+') — its share of the household basket makes it the most stable contributor, though also the least revealing about economic dynamism.') +
    (hcNeg.length?p('<strong>Drag</strong>: '+em(hcNeg.join(', '))+'. These categories are shrinking as a share of household spending — either due to substitution, price effects, or genuine demand weakness.'):p('No category is dragging on HH consumption this quarter — a fully broad-based consumer expansion.'));

  // ── 02c GFCF — YoY Growth ────────────────────────────────────────────────
  const ggD=D.gfcf_g_data;
  const bldG=last(slP(ggD['Buildings & Structures']||[])), machG=last(slP(ggD['Machine & Equipment']||[]));
  const vehG=last(slP(ggD['Vehicles']||[])), ipG=last(slP(ggD['Intellectual Property']||[]));
  const gfTot=last(slP(ggD['GFCF Total']||[]));
  const machAvg=avg(slP(ggD['Machine & Equipment']||[])), machTr=trendFn(slP(ggD['Machine & Equipment']||[]));
  // Test equipment as a GROUP (machinery + vehicles + other equipment), not
  // machinery alone: machinery can stall while vehicles and other equipment
  // carry the equipment cycle, and the old machinery-only test then reported
  // "buildings lead" in quarters where equipment was in fact growing faster.
  const equipG=last(slP(D.equip_g||[]));
  const othG=last(slP(ggD['Other Equipment']||[]));
  const qualMsg=equipG>bldG
    ?'<strong>Equipment is outpacing Buildings</strong> ('+b(equipG)+' vs '+b(bldG)+') — a quality signal: the investment cycle is expanding productive capacity rather than just physical structures.'
    :'<strong>Buildings & Structures lead</strong> ('+b(bldG)+' vs equipment '+b(equipG)+') — investment growth skews toward construction. While positive for short-run activity, it is less supportive of long-run productivity than equipment investment.';
  // The composition inside equipment matters as much as the aggregate.
  const splitMsg=(!isNaN(machG)&&!isNaN(vehG)&&Math.abs(vehG-machG)>8)
    ?' But equipment is not moving as a bloc: vehicles '+b(vehG)+' and other equipment '+b(othG)+' against machinery at just '+b(machG)+' (window avg '+bn(machAvg)+'). Transport and general equipment are carrying the cycle while machinery — the component most tied to productive capacity — is the laggard.'
    :'';
  const ipMsg=ipG!=null&&!isNaN(ipG)?(ipG>5?'Intellectual property at '+b(ipG)+' points to rising R&D and digital asset investment — a promising quality upgrade signal.':ipG<0?'Intellectual property investment is contracting ('+b(ipG)+') — a concern for long-run innovation capacity.':'Intellectual property investment at '+b(ipG)+' is modest but positive.'):'';
  const machMoMsg=machTr==='accelerating'?' Machinery capex is accelerating — corporate confidence in future demand appears high.':machTr==='moderating'?' Machinery growth is moderating — potential sign of cooling capex appetite.':'';

  document.getElementById('cmtGfcfGrowthtext').innerHTML=
    p('Total GFCF grew '+b(gfTot)+'. Buildings: '+b(bldG)+' · Machinery: '+b(machG)+' · Vehicles: '+b(vehG)+' · Other equipment: '+b(othG)+'.') +
    // machMoMsg reads the trend across window halves, which can say
    // "accelerating" in a quarter where machinery is plainly the laggard.
    // When splitMsg has already made that call, suppress it rather than
    // printing both.
    p(qualMsg+splitMsg+(splitMsg?'':machMoMsg)) +
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
  // Value-chain claims are judged on contributions, not growth rates: a faster
  // rate on a much smaller base is a trend, not an achieved shift in the mix.
  const mcD0=D.mfg_c_data||{{}};
  const foodUpC=last(slP(mcD0['Food & Beverages']||[]));
  const metalUpC=last(slP(mcD0['Metal Products & Electronics']||[]));
  const upgradeMsg=metalG>foodMG?'Metal Products & Electronics ('+b(metalG)+') is growing faster than commodity-oriented Food & Beverages ('+b(foodMG)+') — an encouraging direction. On contributions the ranking still reverses, though: Food & Beverages adds '+bp(foodUpC)+' to manufacturing growth against '+bp(metalUpC)+' for metals and electronics. The faster rate sits on a much smaller base, so this is a promising trend rather than a completed move up the value chain.':'Food & Beverages ('+b(foodMG)+', contributing '+bp(foodUpC)+') continues to anchor manufacturing — Indonesia\\'s industrial base still leans toward lower value-add processing. Metal Products & Electronics at '+b(metalG)+' ('+bp(metalUpC)+') trails, suggesting limited progress up the value chain this quarter.';

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

// Init all data window
setGDPWindow(0);
</script>
</body>
</html>
"""

html = HEAD + NAV + GDP_SECTION + FOOTER + JS

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written: {out_path}  ({os.path.getsize(out_path)//1024} KB)")
