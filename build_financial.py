"""Financial dashboard builder → html/financial.html"""
import json, os

FIN_DIR = r"C:\work\economist\rawdata\financial"
HTML    = r"C:\work\economist\html"
os.makedirs(HTML, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL DATA
# ══════════════════════════════════════════════════════════════════════════════
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

print(f"Financial data fetched: {fin_fetched}")

# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════
out_path = os.path.join(HTML, "financial.html")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indonesia Economic Dashboard — Financial Markets</title>
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
.block{margin-bottom:3rem;}
.block-header{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}
.block-num{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}
.block-title{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}
.chart-wrap,.chart-full{background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.5rem;}
.chart-wrap h3,.chart-full h3{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:1rem;}
.chart-note{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);margin-top:.75rem;}
.fin-data-note{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);letter-spacing:.05em;padding:.5rem 0 1rem;text-align:center;}
.fin-data-note strong{color:var(--ink-light);} .fin-data-note code{background:var(--paper-warm);padding:1px 5px;border-radius:2px;}
.chart-with-comment{display:flex;gap:1.5rem;align-items:flex-start;}
.chart-with-comment .chart-full,.chart-with-comment .chart-wrap{flex:1;min-width:0;}
.comment-box{width:260px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}
.comment-box .cb-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}
.comment-box p{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}
.comment-box p:last-child{margin-bottom:0;}
.comment-box strong{color:var(--ink);font-weight:500;}.comment-box em{font-style:normal;color:var(--ink);font-weight:500;}
footer{background:var(--paper-warm);border-top:1px solid var(--rule);padding:1.25rem 3rem;font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;}
@media(max-width:900px){
  .chart-with-comment{flex-direction:column;}
  .comment-box{width:100%;}
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
    <a href="bop.html" class="mn-tab">BoP</a>
    <a href="financial.html" class="mn-tab active">Financial</a>
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

FINANCIAL_SECTION = f"""
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
"""

JS = f"""
<script>
const FIN = {fin_js};

const MONO = "'DM Mono', monospace";
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.color = '#8a8780';

function xAxis() {{
  return {{ticks:{{font:{{family:MONO,size:10}},maxRotation:45,autoSkip:true,maxTicksLimit:12}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function yAxis(title) {{
  return {{title:{{display:true,text:title,font:{{family:MONO,size:10}},color:'#8a8780'}},ticks:{{font:{{family:MONO,size:10}}}},grid:{{color:'rgba(0,0,0,0.05)'}}}};
}}
function lineDS(label,data,color,opts={{}}) {{
  return {{label,data,borderColor:color,borderWidth:1.8,pointRadius:0,pointHoverRadius:4,tension:0,fill:false,...opts}};
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

  const h = n => Math.floor(n/2);
  const fH1=avg(fv.slice(0,h(fv.length))), fH2=avg(fv.slice(h(fv.length)));
  const eH1=avg(ev.slice(0,h(ev.length))), eH2=avg(ev.slice(h(ev.length)));

  const idrDir  = fChg===null?'unchanged':fChg>1?'depreciated':fChg<-1?'appreciated':'largely stable';
  const idrTrend= (fH1&&fH2)?(fH2>fH1+50?'weakening trend':fH2<fH1-50?'strengthening trend':'broadly stable'):'—';
  const ihsgDir = eChg===null?'unchanged':eChg>1?'gained':eChg<-1?'lost':'largely flat';
  const ihsgTrend=(eH1&&eH2)?(eH2>eH1*1.03?'uptrend':eH2<eH1*0.97?'downtrend':'sideways'):'—';

  const outflowSignal = fChg!=null&&eChg!=null&&fChg>1&&eChg<-1;
  const inflowSignal  = fChg!=null&&eChg!=null&&fChg<-1&&eChg>1;

  let fxCmt='', eqCmt='', label='';

  if(key==='3y') {{
    label = 'Last 12 Months · Monthly';
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

// Init default window
setFinWindow('3y');
</script>
</body>
</html>
"""

html = HEAD + NAV + FINANCIAL_SECTION + FOOTER + JS

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written: {out_path}  ({os.path.getsize(out_path)//1024} KB)")
