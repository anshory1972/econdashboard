"""BOP dashboard builder → html/bop.html"""
import json, os, csv

HTML  = r"C:\work\economist\html"
CLEAN = r"C:\work\economist\rawdata\seki\clean"
os.makedirs(HTML, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOP DATA  (reads from clean CSV — run parse_bop.py first to regenerate)
# ══════════════════════════════════════════════════════════════════════════════
def read_col(rows, col):
    return [float(r[col]) if r[col] not in ('', 'None', None) else None for r in rows]

with open(os.path.join(CLEAN, 'bop_quarterly.csv'), newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

BOP_PERIODS = [r['period'] for r in rows]
BN = len(BOP_PERIODS)

bca       = read_col(rows, 'current_account')
bka       = read_col(rows, 'capital_account')
bfa       = read_col(rows, 'financial_account')
berr      = read_col(rows, 'net_errors_omissions')
bbal      = read_col(rows, 'overall_balance')
bres_pos  = read_col(rows, 'reserve_position')
bres_months = read_col(rows, 'import_coverage_months')
# Negate reserve_assets_raw so positive = accumulation, negative = drawdown
bres      = [-v if v is not None else None for v in read_col(rows, 'reserve_assets_raw')]
bka_fa    = [round((bka[i] or 0)+(bfa[i] or 0),2) if (bka[i] is not None or bfa[i] is not None) else None for i in range(BN)]
bca_goods   = read_col(rows, 'ca_goods')
bca_svcs    = read_col(rows, 'ca_services')
bca_primary = read_col(rows, 'ca_primary_income')
bca_second  = read_col(rows, 'ca_secondary_income')
bfa_di  = read_col(rows, 'fa_direct_investment')
bfa_pi  = read_col(rows, 'fa_portfolio')
bfa_der = read_col(rows, 'fa_derivatives')
bfa_oi  = read_col(rows, 'fa_other_investment')

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

# ── YoY growth helper — calendar-based (handles gaps in quarterly data) ────────
def yoy(periods, series):
    """Compare each period to the same quarter one year earlier by name, not by position."""
    lookup = {p: v for p, v in zip(periods, series)}
    result = []
    for p, v in zip(periods, series):
        yr, q = p.split('-')
        prev_p = f'{int(yr)-1}-{q}'
        prev_v = lookup.get(prev_p)
        if v is None or prev_v is None or prev_v == 0:
            result.append(None)
        else:
            result.append(round((v / prev_v - 1) * 100, 2))
    return result

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT BY COMMODITY  (run parse_exports.py first)
# ══════════════════════════════════════════════════════════════════════════════
with open(os.path.join(CLEAN, 'exports_by_commodity.csv'), newline='', encoding='utf-8') as f:
    erows = list(csv.DictReader(f))
EXP_PERIODS  = [r['period'] for r in erows]
exp_coal     = read_col(erows, 'mining_coal')
exp_palm     = read_col(erows, 'manuf_palm_oil')
exp_crude    = read_col(erows, 'mining_crude_oil')
exp_gas      = read_col(erows, 'mining_natural_gas')
exp_lng      = read_col(erows, 'mining_lng')
exp_nickel   = read_col(erows, 'mining_nickel_ore')
exp_copper   = read_col(erows, 'mining_copper_ore')
exp_rubber   = read_col(erows, 'manuf_rubber')
exp_textiles = read_col(erows, 'manuf_textiles')
eli = max(i for i,v in enumerate(exp_coal) if v is not None)
elp = EXP_PERIODS[eli]
y_ecoal=yoy(EXP_PERIODS,exp_coal); y_epalm=yoy(EXP_PERIODS,exp_palm); y_ecrude=yoy(EXP_PERIODS,exp_crude)
y_egas=yoy(EXP_PERIODS,exp_gas);   y_elng=yoy(EXP_PERIODS,exp_lng);   y_enickel=yoy(EXP_PERIODS,exp_nickel)
y_ecopper=yoy(EXP_PERIODS,exp_copper); y_erubber=yoy(EXP_PERIODS,exp_rubber); y_etex=yoy(EXP_PERIODS,exp_textiles)
exp_js = json.dumps({'periods':EXP_PERIODS,
    'coal':y_ecoal,'palm':y_epalm,'crude':y_ecrude,'gas':y_egas,'lng':y_elng,
    'nickel':y_enickel,'copper':y_ecopper,'rubber':y_erubber,'textiles':y_etex})
def fmtpct(v): return f'{v:+.1f}%' if v is not None else '—'
print(f"Exports YoY: {elp}  Coal {fmtpct(y_ecoal[eli])}  Palm {fmtpct(y_epalm[eli])}  Nickel {fmtpct(y_enickel[eli])}")
exp_ranked = sorted([
    ('Coal',y_ecoal[eli]),('Palm Oil',y_epalm[eli]),('Crude Oil',y_ecrude[eli]),
    ('Nat. Gas',y_egas[eli]),('LNG',y_elng[eli]),('Nickel Ore',y_enickel[eli]),
    ('Copper Ore',y_ecopper[eli]),('Rubber',y_erubber[eli]),('Textiles',y_etex[eli]),
], key=lambda x: -(x[1] if x[1] is not None else -999))
exp_sc5 = (
    f"<p>Commodity exports YoY growth in <em>{elp}</em>:</p>"
    + "".join(f"<p><strong>{nm}</strong>: {fmtpct(v)}</p>" for nm,v in exp_ranked if v is not None)
)

# ══════════════════════════════════════════════════════════════════════════════
# IMPORT BY ECONOMIC CATEGORY  (run parse_imports.py first)
# ══════════════════════════════════════════════════════════════════════════════
with open(os.path.join(CLEAN, 'imports_by_category.csv'), newline='', encoding='utf-8') as f:
    irows = list(csv.DictReader(f))
IMP_PERIODS      = [r['period'] for r in irows]
imp_cons_total   = read_col(irows, 'cons_total')
imp_rawmat_total = read_col(irows, 'rawmat_total')
imp_cap_total    = read_col(irows, 'capgoods_total')
imp_total_cif    = read_col(irows, 'total_cif')
imp_cons_fuel    = read_col(irows, 'cons_fuel_oil_products')
imp_cons_fproc   = read_col(irows, 'cons_food_bev_processed')
imp_cons_semidur = read_col(irows, 'cons_semidurable')
imp_cons_nondur  = read_col(irows, 'cons_nondurable')
imp_cons_fraw    = read_col(irows, 'cons_food_bev_raw')
imp_raw_sproc    = read_col(irows, 'rawmat_supply_processed')
imp_raw_spares   = read_col(irows, 'rawmat_spares_capgoods')
imp_raw_fuelp    = read_col(irows, 'rawmat_fuel_processed')
imp_raw_fuelr    = read_col(irows, 'rawmat_fuel_raw')
imp_raw_crude    = read_col(irows, 'rawmat_crude_oil')
imp_cap_excl     = read_col(irows, 'capgoods_excl_transport')
imp_cap_cars     = read_col(irows, 'capgoods_passenger_cars')
imp_cap_trans    = read_col(irows, 'capgoods_transport_other')
ili = max(i for i,v in enumerate(imp_cons_total) if v is not None)
ilp = IMP_PERIODS[ili]
# YoY growth for all import series
y_icons=yoy(IMP_PERIODS,imp_cons_total); y_iraw=yoy(IMP_PERIODS,imp_rawmat_total)
y_icap=yoy(IMP_PERIODS,imp_cap_total);  y_itot=yoy(IMP_PERIODS,imp_total_cif)
y_cfuel=yoy(IMP_PERIODS,imp_cons_fuel); y_cfproc=yoy(IMP_PERIODS,imp_cons_fproc)
y_csemi=yoy(IMP_PERIODS,imp_cons_semidur); y_cnon=yoy(IMP_PERIODS,imp_cons_nondur); y_cfraw=yoy(IMP_PERIODS,imp_cons_fraw)
y_rsproc=yoy(IMP_PERIODS,imp_raw_sproc); y_rspares=yoy(IMP_PERIODS,imp_raw_spares)
y_rfuelp=yoy(IMP_PERIODS,imp_raw_fuelp); y_rfuelr=yoy(IMP_PERIODS,imp_raw_fuelr); y_rcrude=yoy(IMP_PERIODS,imp_raw_crude)
y_cex=yoy(IMP_PERIODS,imp_cap_excl); y_ccar=yoy(IMP_PERIODS,imp_cap_cars); y_ctr=yoy(IMP_PERIODS,imp_cap_trans)
imp_js = json.dumps({'periods':IMP_PERIODS,
    'cons':y_icons,'rawmat':y_iraw,'cap':y_icap,'total':y_itot,
    'cons_fuel':y_cfuel,'cons_fproc':y_cfproc,
    'cons_semidur':y_csemi,'cons_nondur':y_cnon,'cons_fraw':y_cfraw,
    'raw_sproc':y_rsproc,'raw_spares':y_rspares,
    'raw_fuelp':y_rfuelp,'raw_fuelr':y_rfuelr,'raw_crude':y_rcrude,
    'cap_excl':y_cex,'cap_cars':y_ccar,'cap_trans':y_ctr})
print(f"Imports YoY: {ilp}  Cons {fmtpct(y_icons[ili])}  Raw {fmtpct(y_iraw[ili])}  Cap {fmtpct(y_icap[ili])}")
imp_sc6a = (
    f"<p>Import YoY growth in <em>{ilp}</em>:</p>"
    f"<p><strong>Raw Materials</strong>: {fmtpct(y_iraw[ili])}</p>"
    f"<p><strong>Consumer Goods</strong>: {fmtpct(y_icons[ili])}</p>"
    f"<p><strong>Capital Goods</strong>: {fmtpct(y_icap[ili])}</p>"
    f"<p>Total CIF: <strong>{fmtpct(y_itot[ili])}</strong>.</p>"
)

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

# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════
out_path = os.path.join(HTML, "bop.html")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indonesia Economic Dashboard — Balance of Payments</title>
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
.kpi-delta{font-family:'DM Mono',monospace;font-size:11px;margin-top:.2rem;}
.kpi-delta.pos{color:#2d5a27;}.kpi-delta.neg{color:#b5460f;}
.block{margin-bottom:3rem;}
.block-header{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}
.block-num{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}
.block-title{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}
.chart-wrap,.chart-full{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.5rem;}
.chart-wrap h3,.chart-full h3{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:1rem;}
.chart-note{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);margin-top:.75rem;}
.chart-with-comment{display:flex;gap:1.5rem;align-items:flex-start;}
.chart-with-comment .chart-full,.chart-with-comment .chart-wrap{flex:1;min-width:0;}
/* BOP comment boxes always visible */
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
    <a href="econdashboard.html" class="mn-tab">GDP</a>
    <a href="bop.html" class="mn-tab active">BoP</a>
    <a href="financial.html" class="mn-tab">Financial</a>
    <span class="mn-tab disabled">Prices</span>
    <span class="mn-tab disabled">Fiscal</span>
  </div>
</div>
"""

FOOTER = """
<footer>
  <span>Indonesia Economic Dashboard</span>
  <span>Source: SEKI BI, BPS, CEIC, Yahoo Finance</span>
</footer>
"""

BOP_SECTION = f"""
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

  <div class="block"><div class="block-header"><span class="block-num">05</span><h2 class="block-title">Exports by Key Commodity</h2></div>
    <div class="chart-with-comment">
      <div class="chart-full"><h3>Quarterly exports · USD million</h3>
        <div style="position:relative;height:320px"><canvas id="bopChartExp"></canvas></div>
        <div class="chart-note">YoY % change. Data through {elp}. Source: SEKI 5.10, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt05label"></div><div id="bopCmt05"></div></div>
    </div>
  </div>

  <div class="block"><div class="block-header"><span class="block-num">06</span><h2 class="block-title">Imports by Economic Category</h2></div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem">
      <div class="chart-full"><h3>Top-level categories · USD million</h3>
        <div style="position:relative;height:280px"><canvas id="bopChartImpTop"></canvas></div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt06label"></div><div id="bopCmt06"></div></div>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem">
      <div class="chart-full">
        <h3>Consumer Goods — top 5 sub-items · USD mn</h3>
        <div style="position:relative;height:280px"><canvas id="bopChartImpCons"></canvas></div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt06blabel"></div><div id="bopCmt06b"></div></div>
    </div>
    <div class="chart-with-comment" style="margin-bottom:1.5rem">
      <div class="chart-full">
        <h3>Raw Materials — top 5 sub-items · USD mn</h3>
        <div style="position:relative;height:280px"><canvas id="bopChartImpRaw"></canvas></div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt06clabel"></div><div id="bopCmt06c"></div></div>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Capital Goods — all sub-items · USD million</h3>
        <div style="position:relative;height:220px"><canvas id="bopChartImpCap"></canvas></div>
        <div class="chart-note">YoY % change. Source: SEKI 5.19, BI.</div>
      </div>
      <div class="comment-box"><div class="cb-label" id="bopCmt06dlabel"></div><div id="bopCmt06d"></div></div>
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


  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">05</span><h2 class="snap-group-title">Exports by Key Commodity</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {elp}</div>{exp_sc5}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>Key commodity exports · latest quarter · USD mn</h3>
          <div style="position:relative;height:280px"><canvas id="bopSnapExp"></canvas></div>
        </div>
      </div>
    </div>
  </div>

  <div class="snap-group">
    <div class="snap-group-header"><span class="snap-group-num">06</span><h2 class="snap-group-title">Imports by Economic Category</h2></div>
    <div class="snap-body">
      <div class="snap-comment"><div class="cb-label">Latest · {ilp}</div>{imp_sc6a}</div>
      <div class="snap-charts">
        <div class="snap-chart-wrap"><h3>Import categories · latest quarter · USD mn</h3>
          <div style="position:relative;height:220px"><canvas id="bopSnapImpTop"></canvas></div>
        </div>
      </div>
    </div>
  </div>

</div>
</div><!-- /bopTabSnap -->
"""

JS = f"""
<script>
const B   = {bop_js};
const EXP = {exp_js};
const IMP = {imp_js};

const MONO = "'DM Mono', monospace";
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.color = '#8a8780';

function xAxis() {{
  return {{ticks:{{font:{{family:MONO,size:10}},maxRotation:45,autoSkip:true,maxTicksLimit:12}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function yAxis(title) {{
  return {{title:{{display:true,text:title,font:{{family:MONO,size:10}},color:'#8a8780'}},ticks:{{font:{{family:MONO,size:10}}}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function legend() {{ return {{labels:{{font:{{family:MONO,size:10}},boxWidth:10,padding:10}}}}; }}
function legendRight() {{ return {{position:'right',labels:{{font:{{family:MONO,size:10}},boxWidth:10,padding:10}}}}; }}

/* ════════════════════════════════════════════
   BOP CHARTS
   ════════════════════════════════════════════ */
let bopCharts=[], bopSnapBuilt=false;

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
    const periods=ch._periods||B.periods;
    const sl=arr=>n===0?arr:(arr||[]).slice(-n);
    ch.data.labels=sl(periods);
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

  new Chart(document.getElementById('bopSnapBOP'), {{
    type:'bar',
    data:{{
      labels:['Current Account','Capital+Financial','Net Errors','Overall Balance'],
      datasets:[bSD(['CA','KA+FA','Err','Bal'],[B.ca[li],B.ka_fa[li],B.errors[li],B.balance[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  new Chart(document.getElementById('bopSnapCA'), {{
    type:'bar',
    data:{{
      labels:['A. Goods','B. Services','C. Primary Income','D. Secondary Income','CA Total'],
      datasets:[bSD(['G','S','P','D','T'],[B.ca_goods[li],B.ca_svcs[li],B.ca_primary[li],B.ca_second[li],B.ca[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  new Chart(document.getElementById('bopSnapFA'), {{
    type:'bar',
    data:{{
      labels:['1. Direct Investment','2. Portfolio','3. Derivatives','4. Other Investment','FA Total'],
      datasets:[bSD(['DI','PI','D','OI','T'],[B.fa_di[li],B.fa_pi[li],B.fa_der[li],B.fa_oi[li],B.fa[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  new Chart(document.getElementById('bopSnapRes'), {{
    type:'bar',
    data:{{
      labels:['Reserve Change'],
      datasets:[bSD(['R'],[B.res[li]])]
    }},
    options:bSOpts('USD mn')
  }});

  const eli2=EXP.coal.reduceRight((acc,v,i)=>acc===-1&&v!==null?i:acc,-1);
  const ili2=IMP.cons.reduceRight((acc,v,i)=>acc===-1&&v!==null?i:acc,-1);

  const expVals=[EXP.coal[eli2],EXP.palm[eli2],EXP.lng[eli2],EXP.nickel[eli2],
                 EXP.gas[eli2],EXP.crude[eli2],EXP.copper[eli2],EXP.rubber[eli2],EXP.textiles[eli2]];
  const expPairs=[['Coal',EXP.coal[eli2]],['Palm Oil',EXP.palm[eli2]],['LNG',EXP.lng[eli2]],
    ['Nickel Ore',EXP.nickel[eli2]],['Nat. Gas',EXP.gas[eli2]],['Crude Oil',EXP.crude[eli2]],
    ['Copper Ore',EXP.copper[eli2]],['Rubber',EXP.rubber[eli2]],['Textiles',EXP.textiles[eli2]]]
    .filter(([,v])=>v!==null).sort((a,bb)=>bb[1]-a[1]);

  function bSOptsPct() {{
    return {{
      responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>` ${{ctx.parsed.x!=null?(ctx.parsed.x>=0?'+':'')+ctx.parsed.x.toFixed(1)+'%':''}}` }}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}},
        y:{{ticks:{{font:{{family:MONO,size:10}}}},grid:{{display:false}}}}
      }}
    }};
  }}

  new Chart(document.getElementById('bopSnapExp'),{{
    type:'bar',
    data:{{
      labels:expPairs.map(([l])=>l),
      datasets:[bSD([],expPairs.map(([,v])=>v))]
    }},
    options:bSOptsPct()
  }});

  new Chart(document.getElementById('bopSnapImpTop'),{{
    type:'bar',
    data:{{
      labels:['Raw Materials','Consumer Goods','Capital Goods'],
      datasets:[bSD([],[IMP.rawmat[ili2],IMP.cons[ili2],IMP.cap[ili2]])]
    }},
    options:bSOptsPct()
  }});

  bopSnapBuilt=true;
}}

function updateBOPCommentary(n) {{
  const li = B.ca.reduceRight((acc,v,i) => acc===-1 && v!==null ? i : acc, -1);
  const lp = B.periods[li];
  const wlabel = n===0 ? 'full period shown' : n===8 ? 'past 2 years' : 'past 4 years';
  const clabel = lp + ' · ' + (n===0 ? 'All' : n===8 ? '2Y' : '4Y');

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

  function pct(v,dec) {{
    if(v===null||v===undefined)return '<strong>—</strong>';
    dec=dec!==undefined?dec:1;
    return '<strong>'+(v>=0?'+':'')+v.toFixed(dec)+'%</strong>';
  }}
  const wlbl2=n===0?'All':n===8?'2Y':'4Y';

  // ── 05 Exports by Commodity ──────────────────────────────────────────────
  const eli3=EXP.coal.reduceRight((acc,v,i)=>acc===-1&&v!==null?i:acc,-1);
  const elp3=EXP.periods[eli3];
  function slE(arr) {{
    const out=(arr||[]).slice(0,eli3+1).filter(v=>v!==null);
    return n===0?out:out.slice(-n);
  }}
  const coal_w=slE(EXP.coal),palm_w=slE(EXP.palm),nickel_w=slE(EXP.nickel),lng_w=slE(EXP.lng);
  const crude_ew=slE(EXP.crude),tex_ew=slE(EXP.textiles);
  const ePairs=[['Coal',EXP.coal[eli3]],['Palm Oil',EXP.palm[eli3]],['Crude Oil',EXP.crude[eli3]],
    ['LNG',EXP.lng[eli3]],['Nat. Gas',EXP.gas[eli3]],['Nickel',EXP.nickel[eli3]],
    ['Copper',EXP.copper[eli3]],['Rubber',EXP.rubber[eli3]],['Textiles',EXP.textiles[eli3]]]
    .filter(([,v])=>v!==null).sort((a,bb)=>bb[1]-a[1]);
  const etop=ePairs[0]; const ebot=ePairs[ePairs.length-1];
  const ePos=ePairs.filter(([,v])=>v>0).length; const eLen=ePairs.length;
  document.getElementById('bopCmt05label').textContent=elp3+' · '+wlbl2;
  document.getElementById('bopCmt05').innerHTML=
    p('Strongest growth in '+em(elp3)+': <strong>'+etop[0]+'</strong> at '+pct(etop[1])+
      (ebot[1]<0?'; weakest: <strong>'+ebot[0]+'</strong> at '+pct(ebot[1])+'.':'.'))+
    p(ePos+' of '+eLen+' key commodities posted positive YoY growth. Window avgs — Coal: '+pct(avg(coal_w))+
      ' · Palm Oil: '+pct(avg(palm_w))+' · LNG: '+pct(avg(lng_w))+'.')+
    p('YoY rates reflect both volume and price effects. Sharp swings often signal commodity price cycles rather than structural trade shifts.');

  // ── 06 Imports by Category ───────────────────────────────────────────────
  const ili3=IMP.cons.reduceRight((acc,v,i)=>acc===-1&&v!==null?i:acc,-1);
  const ilp3=IMP.periods[ili3];
  function slI(arr) {{
    const out=(arr||[]).slice(0,ili3+1).filter(v=>v!==null);
    return n===0?out:out.slice(-n);
  }}
  const cons_w2=slI(IMP.cons),raw_w2=slI(IMP.rawmat),cap_w2=slI(IMP.cap),tot_w2=slI(IMP.total);
  const cons_n=IMP.cons[ili3],raw_n=IMP.rawmat[ili3],cap_n=IMP.cap[ili3],tot_n=IMP.total[ili3];
  const capDir=cap_n!==null&&avg(cap_w2)!==0?
    (cap_n>avg(cap_w2)*1.1?'accelerating above window avg — capex uptick signal':
     cap_n<avg(cap_w2)*0.85?'contracting below window avg — capex slowing':'moving near window avg'):'—';
  document.getElementById('bopCmt06label').textContent=ilp3+' · '+wlbl2;
  document.getElementById('bopCmt06').innerHTML=
    p('Import YoY in '+em(ilp3)+': Total CIF '+pct(tot_n)+'. Raw Materials '+pct(raw_n)+
      ', Consumer Goods '+pct(cons_n)+', Capital Goods '+pct(cap_n)+'.')+
    p('Window avgs — Raw: '+pct(avg(raw_w2))+' · Consumer: '+pct(avg(cons_w2))+' · Capital: '+pct(avg(cap_w2))+'.')+
    p('Capital goods growth is '+capDir+'. Raw materials and consumer goods broadly track the economic cycle.');

  // ── 06b Consumer Goods sub-items ────────────────────────────────────────
  const cfuel_w=slI(IMP.cons_fuel),cfproc_w=slI(IMP.cons_fproc);
  const csemi_w=slI(IMP.cons_semidur),cnon_w=slI(IMP.cons_nondur),cfraw_w=slI(IMP.cons_fraw);
  const cfuel_n=IMP.cons_fuel[ili3],cfproc_n=IMP.cons_fproc[ili3];
  const csemi_n=IMP.cons_semidur[ili3],cnon_n=IMP.cons_nondur[ili3];
  const cPairs=[['Fuel/Oil',cfuel_n],['Processed F&B',cfproc_n],['Semi-durable',csemi_n],
    ['Non-durable',cnon_n],['Raw F&B',IMP.cons_fraw[ili3]]].filter(([,v])=>v!==null).sort((a,bb)=>bb[1]-a[1]);
  const ctop=cPairs[0];
  document.getElementById('bopCmt06blabel').textContent=ilp3+' · '+wlbl2;
  document.getElementById('bopCmt06b').innerHTML=
    p('Strongest consumer import growth in '+em(ilp3)+': <strong>'+ctop[0]+'</strong> at '+pct(ctop[1])+'.')+
    p('Window avgs — Fuel/Oil: '+pct(avg(cfuel_w))+' · Processed F&B: '+pct(avg(cfproc_w))+
      ' · Semi-durable: '+pct(avg(csemi_w))+' · Non-durable: '+pct(avg(cnon_w))+'.')+
    p('Fuel/oil YoY is heavily driven by global oil price movements. Processed F&B and semi-durable goods track domestic consumer purchasing power.');

  // ── 06c Raw Materials sub-items ──────────────────────────────────────────
  const rsproc_w=slI(IMP.raw_sproc),rspares_w=slI(IMP.raw_spares);
  const rfuelp_w=slI(IMP.raw_fuelp),rfuelr_w=slI(IMP.raw_fuelr),rcrude_w=slI(IMP.raw_crude);
  const rsproc_n=IMP.raw_sproc[ili3],rspares_n=IMP.raw_spares[ili3];
  const rfuelp_n=IMP.raw_fuelp[ili3],rfuelr_n=IMP.raw_fuelr[ili3],rcrude_n=IMP.raw_crude[ili3];
  const rPairs=[['Proc. Supplies',rsproc_n],['Cap Spares',rspares_n],['Proc. Fuel',rfuelp_n],
    ['Raw Fuel',rfuelr_n],['Crude Oil',rcrude_n]].filter(([,v])=>v!==null).sort((a,bb)=>bb[1]-a[1]);
  const rtop=rPairs[0];
  document.getElementById('bopCmt06clabel').textContent=ilp3+' · '+wlbl2;
  document.getElementById('bopCmt06c').innerHTML=
    p('Fastest-growing raw material in '+em(ilp3)+': <strong>'+rtop[0]+'</strong> at '+pct(rtop[1])+'.')+
    p('Window avgs — Proc. Supplies: '+pct(avg(rsproc_w))+' · Cap Spares: '+pct(avg(rspares_w))+
      ' · Proc. Fuel: '+pct(avg(rfuelp_w))+' · Crude Oil: '+pct(avg(rcrude_w))+'.')+
    p('Cap goods spares track factory utilisation; crude oil and fuel track energy costs. Sustained growth in processed supplies signals rising manufacturing throughput.');

  // ── 06d Capital Goods sub-items ──────────────────────────────────────────
  const cex_w=slI(IMP.cap_excl),ccar_w=slI(IMP.cap_cars),ctr_w=slI(IMP.cap_trans);
  const cex_n=IMP.cap_excl[ili3],ccar_n=IMP.cap_cars[ili3],ctr_n=IMP.cap_trans[ili3];
  const kPairs=[['Cap Goods excl. Transport',cex_n],['Passenger Cars',ccar_n],['Other Transport',ctr_n]]
    .filter(([,v])=>v!==null).sort((a,bb)=>bb[1]-a[1]);
  const ktop=kPairs[0];
  document.getElementById('bopCmt06dlabel').textContent=ilp3+' · '+wlbl2;
  document.getElementById('bopCmt06d').innerHTML=
    p('Capital goods growth in '+em(ilp3)+': machinery excl. transport '+pct(cex_n)+
      ', passenger cars '+pct(ccar_n)+', other transport '+pct(ctr_n)+'.')+
    p('Window avgs — Machinery: '+pct(avg(cex_w))+' · Passenger cars: '+pct(avg(ccar_w))+
      ' · Other transport: '+pct(avg(ctr_w))+'.')+
    p('Machinery imports (excl. transport) are the cleanest investment signal. Other transport is lumpy — large one-off ship or aircraft orders can dominate a quarter.');
}}

function bopDS(label,full,color,opts={{}}) {{
  return {{label,data:(full||[]).slice(-8),borderColor:color,backgroundColor:color,_full:full,...opts}};
}}

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

// Chart 05: Exports by Key Commodity — YoY growth
(function(){{
  const ch=new Chart(document.getElementById('bopChartExp'),{{
    type:'line',
    data:{{labels:EXP.periods.slice(-8),datasets:[
      bopDS('Coal',EXP.coal,'#1a1814',{{borderWidth:2.5,pointRadius:0,tension:0,fill:false}}),
      bopDS('Palm Oil',EXP.palm,'#ca8a04',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Nickel Ore',EXP.nickel,'#0e7490',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('LNG',EXP.lng,'#7c3aed',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Crude Oil',EXP.crude,'#b5460f',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[3,2]}}),
      bopDS('Nat. Gas',EXP.gas,'#16a34a',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[3,2]}}),
      bopDS('Copper Ore',EXP.copper,'#dc2626',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false}}),
      bopDS('Rubber',EXP.rubber,'#9333ea',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[2,2]}}),
      bopDS('Textiles',EXP.textiles,'#0891b2',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[2,2]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%':''}}` }}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('% YoY'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},
        grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}}}}}}
  }});
  ch._periods=EXP.periods; bopCharts.push(ch);
}})();

// Chart 06a: Import Top-level Categories — YoY growth
(function(){{
  const ch=new Chart(document.getElementById('bopChartImpTop'),{{
    type:'line',
    data:{{labels:IMP.periods.slice(-8),datasets:[
      bopDS('Consumer Goods',IMP.cons,'#2563eb',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Raw Materials',IMP.rawmat,'#16a34a',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Capital Goods',IMP.cap,'#b5460f',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Total CIF',IMP.total,'#1a1814',{{borderWidth:2.5,pointRadius:0,tension:0,fill:false,borderDash:[4,3]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%':''}}` }}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('% YoY'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},
        grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}}}}}}
  }});
  ch._periods=IMP.periods; bopCharts.push(ch);
}})();

// Chart 06b: Consumer Goods Top 5 — YoY growth
(function(){{
  const ch=new Chart(document.getElementById('bopChartImpCons'),{{
    type:'line',
    data:{{labels:IMP.periods.slice(-8),datasets:[
      bopDS('Fuel/Oil Products',IMP.cons_fuel,'#b5460f',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Processed F&B',IMP.cons_fproc,'#2563eb',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Semi-durable',IMP.cons_semidur,'#16a34a',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Non-durable',IMP.cons_nondur,'#7c3aed',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Raw F&B',IMP.cons_fraw,'#0e7490',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[3,2]}}),
      bopDS('Consumer Total',IMP.cons,'#1a1814',{{borderWidth:2.5,pointRadius:0,tension:0,fill:false,borderDash:[4,3]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%':''}}` }}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('% YoY'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},
        grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}}}}}}
  }});
  ch._periods=IMP.periods; bopCharts.push(ch);
}})();

// Chart 06c: Raw Materials Top 5 — YoY growth
(function(){{
  const ch=new Chart(document.getElementById('bopChartImpRaw'),{{
    type:'line',
    data:{{labels:IMP.periods.slice(-8),datasets:[
      bopDS('Processed Supplies',IMP.raw_sproc,'#16a34a',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Cap Goods Spares',IMP.raw_spares,'#2563eb',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Processed Fuel',IMP.raw_fuelp,'#b5460f',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Raw Fuel',IMP.raw_fuelr,'#ca8a04',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[3,2]}}),
      bopDS('Crude Oil',IMP.raw_crude,'#7c3aed',{{borderWidth:1.5,pointRadius:0,tension:0,fill:false,borderDash:[3,2]}}),
      bopDS('Raw Mat. Total',IMP.rawmat,'#1a1814',{{borderWidth:2.5,pointRadius:0,tension:0,fill:false,borderDash:[4,3]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%':''}}` }}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('% YoY'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},
        grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}}}}}}
  }});
  ch._periods=IMP.periods; bopCharts.push(ch);
}})();

// Chart 06d: Capital Goods All Sub-items — YoY growth
(function(){{
  const ch=new Chart(document.getElementById('bopChartImpCap'),{{
    type:'line',
    data:{{labels:IMP.periods.slice(-8),datasets:[
      bopDS('Cap Goods excl. Transport',IMP.cap_excl,'#0e7490',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Passenger Cars',IMP.cap_cars,'#7c3aed',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Other Transport',IMP.cap_trans,'#ca8a04',{{borderWidth:2,pointRadius:0,tension:0,fill:false}}),
      bopDS('Capital Total',IMP.cap,'#1a1814',{{borderWidth:2.5,pointRadius:0,tension:0,fill:false,borderDash:[4,3]}}),
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:legendRight(),tooltip:{{backgroundColor:'rgba(26,24,20,0.92)',titleFont:{{family:MONO,size:11}},bodyFont:{{family:MONO,size:12}},padding:12,
        callbacks:{{label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y!=null?(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%':''}}` }}}}}},
      scales:{{x:xAxis(),y:{{...yAxis('% YoY'),ticks:{{font:{{family:MONO,size:10}},callback:v=>(v>=0?'+':'')+v.toFixed(0)+'%'}},
        grid:{{color:ctx=>ctx.tick.value===0?'rgba(0,0,0,0.2)':'rgba(0,0,0,0.05)'}}}}}}}}
  }});
  ch._periods=IMP.periods; bopCharts.push(ch);
}})();

// Init default window (2Y)
setBOPWindow(8);
</script>
</body>
</html>
"""

html = HEAD + NAV + BOP_SECTION + FOOTER + JS

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written: {out_path}  ({os.path.getsize(out_path)//1024} KB)")
