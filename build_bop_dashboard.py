"""
Build bop_consistency.html — Balance of Payments dashboard.
Charts: BOP overview, CA components, FA components, Reserve Assets.
Default window: Short · 2Y so the latest quarter is immediately visible.
"""
import xlrd, json, os, re

RAW  = r"C:\work\economist\rawdata\seki"
HTML = r"C:\work\economist\html"
os.makedirs(HTML, exist_ok=True)

wb = xlrd.open_workbook(os.path.join(RAW, "TABEL5_1.xls"))
sh = wb.sheet_by_name("5.1")

# ── All quarterly columns: 2010-Q1 → 2026-Q1 ─────────────────────────────────
ALL_Q = [
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
PERIODS = [p for p, _ in ALL_Q]
N = len(PERIODS)

def get_q(xls_row):
    vals = []
    for _, c in ALL_Q:
        if sh.cell_type(xls_row, c) == xlrd.XL_CELL_EMPTY:
            vals.append(None)
        else:
            v = sh.cell_value(xls_row, c)
            vals.append(round(float(v), 2) if isinstance(v, (int, float)) else None)
    return vals

# ── Extract key quarterly series ──────────────────────────────────────────────
ca      = get_q(6)   # I.   Current Account
ka      = get_q(31)  # II.  Capital Account
fa      = get_q(34)  # III. Financial Account
errors  = get_q(52)  # V.   Net Errors & Omissions
balance = get_q(53)  # VI.  Overall Balance
res     = get_q(54)  # VII. Reserve Assets (neg = accumulation)
res_pos = get_q(59)  # Memorandum: reserve position stock, end-of-period

ka_fa = [
    round((ka[i] or 0) + (fa[i] or 0), 2)
    if (ka[i] is not None or fa[i] is not None) else None
    for i in range(N)
]

ca_goods   = get_q(7)   # A. Goods
ca_svcs    = get_q(22)  # B. Services
ca_primary = get_q(25)  # C. Primary Income
ca_second  = get_q(28)  # D. Secondary Income

fa_di  = get_q(37)  # 1. Direct Investment
fa_pi  = get_q(40)  # 2. Portfolio Investment
fa_der = get_q(45)  # 3. Financial Derivatives
fa_oi  = get_q(46)  # 4. Other Investment

# ── Latest period + commentary anchors ───────────────────────────────────────
latest_i = max(i for i, v in enumerate(ca) if v is not None)
latest_p = PERIODS[latest_i]
tail8    = slice(max(0, latest_i - 7), latest_i + 1)

def avg8(series):
    vals = [v for v in series[tail8] if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None

def hi(t): return f'<em>{t}</em>'

def vs_a(v, a):
    diff  = round(v - a, 1)
    above = 'above' if diff >= 0 else 'below'
    return f'{above} its 8Q avg ({a:,.1f}) by <strong>{abs(diff):.1f}</strong>'

ca_now   = ca[latest_i];    ca_avg   = avg8(ca)
kafa_now = ka_fa[latest_i]; kafa_avg = avg8(ka_fa)
bal_now  = balance[latest_i]
res_now  = res[latest_i]
resp_now = res_pos[latest_i]
ca_prev  = ca[latest_i - 1] if latest_i > 0 else None

# ── Auto-commentaries ─────────────────────────────────────────────────────────
def sign_word(now, prev):
    if prev is None: return ''
    return ('improving' if now > prev else 'widening') if now < 0 or prev < 0 else ('rising' if now > prev else 'slowing')

ca_comment = (
    f"<p>CA: <strong>{ca_now:+,.0f} USD mn</strong> in {hi(latest_p)}, "
    f"{sign_word(ca_now, ca_prev)} from {ca_prev:+,.0f} prior quarter.</p>"
    f"<p>Reading is {vs_a(ca_now, ca_avg)} USD mn.</p>"
    f"<p>Goods: <strong>{ca_goods[latest_i]:+,.0f}</strong> · "
    f"Services: <strong>{ca_svcs[latest_i]:+,.0f}</strong> · "
    f"Primary income: <strong>{ca_primary[latest_i]:+,.0f}</strong> · "
    f"Secondary income: <strong>{ca_second[latest_i]:+,.0f}</strong>.</p>"
)

fa_now = fa[latest_i]
fa_comment = (
    f"<p>FA: <strong>{fa_now:+,.0f} USD mn</strong> in {hi(latest_p)} "
    f"({'net inflow' if fa_now >= 0 else 'net outflow'}).</p>"
    f"<p>KA+FA combined: <strong>{kafa_now:+,.0f}</strong>, {vs_a(kafa_now, kafa_avg)} USD mn.</p>"
    f"<p>DI: <strong>{fa_di[latest_i]:+,.0f}</strong> · "
    f"Portfolio: <strong>{fa_pi[latest_i]:+,.0f}</strong> · "
    f"Other: <strong>{fa_oi[latest_i]:+,.0f}</strong> · "
    f"Derivatives: <strong>{fa_der[latest_i]:+,.0f}</strong>.</p>"
)

res_comment = (
    f"<p>Reserve change: <strong>{res_now:+,.0f} USD mn</strong> in {hi(latest_p)}.</p>"
    f"<p>{'Accumulation' if res_now < 0 else 'Draw-down'} "
    f"(negative = reserve build-up, BOP convention).</p>"
    + (f"<p>End-period position: <strong>{resp_now/1000:,.1f} USD bn</strong>.</p>"
       if resp_now is not None else "")
)

# ── Serialize for JS ──────────────────────────────────────────────────────────
data_js = json.dumps({
    'periods':    PERIODS,
    'ca':         ca,    'ka_fa':     ka_fa,
    'errors':     errors,'balance':   balance,
    'res':        res,   'res_pos':   res_pos,
    'ca_goods':   ca_goods,   'ca_svcs':    ca_svcs,
    'ca_primary': ca_primary, 'ca_second':  ca_second,
    'fa':         fa,
    'fa_di':      fa_di, 'fa_pi':     fa_pi,
    'fa_der':     fa_der,'fa_oi':     fa_oi,
})

print(f"Latest period: {latest_p}  |  CA {ca_now:+,.0f}  KA+FA {kafa_now:+,.0f}  Balance {bal_now:+,.0f}")

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Balance of Payments · SEKI Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --ink:#1a1814;--ink-light:#4a4740;--ink-faint:#8a8780;
  --paper:#f5f2ec;--paper-warm:#ede9e0;--paper-card:#faf8f4;
  --rule:#d8d3c8;--accent:#b5460f;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:300;font-size:15px;line-height:1.7;}}

.topnav{{background:#2d2a26;border-bottom:2px solid var(--accent);}}
.topnav-inner{{max-width:1200px;margin:0 auto;padding:.5rem 2rem;display:flex;align-items:center;justify-content:space-between;}}
.topnav-brand{{font-family:'DM Mono',monospace;font-size:11px;color:rgba(245,242,236,.4);letter-spacing:.1em;}}
.topnav-links{{display:flex;gap:3px;}}
.tnav-link{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
            padding:4px 14px;border-radius:2px;text-decoration:none;
            color:rgba(245,242,236,.55);transition:all .15s;}}
.tnav-link:hover{{color:var(--paper);background:rgba(255,255,255,.08);}}
.tnav-link.active{{background:var(--accent);color:var(--paper);}}

header{{background:var(--ink);color:var(--paper);padding:2.5rem 3rem 2rem;}}
.header-label{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
header h1{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:400;line-height:1.2;margin-bottom:1rem;}}
header h1 em{{font-style:italic;color:rgba(245,242,236,.6);}}
.header-meta{{display:flex;gap:2rem;flex-wrap:wrap;}}
.hm{{font-family:'DM Mono',monospace;font-size:11px;color:rgba(245,242,236,.5);letter-spacing:.08em;}}
.hm span{{color:rgba(245,242,236,.9);display:block;font-size:13px;margin-top:2px;}}

.window-bar{{position:sticky;top:0;z-index:50;background:var(--paper-warm);border-bottom:1px solid var(--rule);
             padding:.6rem 2rem;display:flex;align-items:center;gap:1.5rem;}}
.window-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);}}
.window-btns{{display:flex;gap:4px;}}
.wbtn{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;padding:4px 14px;border-radius:2px;cursor:pointer;
       border:1px solid var(--rule);background:var(--paper-card);color:var(--ink-light);transition:all .15s;}}
.wbtn:hover{{background:var(--paper-warm);border-color:var(--ink-faint);color:var(--ink);}}
.wbtn.active{{background:var(--ink);border-color:var(--ink);color:var(--paper);font-weight:500;}}

.container{{max-width:1200px;margin:0 auto;padding:2rem 2rem 5rem;}}

.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);
          border:1px solid var(--rule);border-radius:4px;overflow:hidden;margin-bottom:2.5rem;}}
.kpi{{background:var(--paper-card);padding:1.25rem 1.5rem;}}
.kpi-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.4rem;}}
.kpi-value{{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:400;}}
.kpi-value.pos{{color:#2d5a27;}} .kpi-value.neg{{color:#b5460f;}}
.kpi-sub{{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);margin-top:.3rem;}}
.kpi-delta{{font-family:'DM Mono',monospace;font-size:11px;margin-top:.2rem;}}
.kpi-delta.pos{{color:#2d5a27;}} .kpi-delta.neg{{color:#b5460f;}}

.block{{margin-bottom:3rem;}}
.block-header{{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;padding-bottom:.6rem;border-bottom:2px solid var(--ink);}}
.block-num{{font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.1em;min-width:28px;}}
.block-title{{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:400;}}
.chart-with-comment{{display:flex;gap:1.5rem;align-items:flex-start;}}
.chart-full{{flex:1;min-width:0;background:var(--paper-card);border:1px solid var(--rule);border-radius:4px;padding:1.5rem;}}
.chart-full h3{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:1rem;}}
.chart-note{{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-faint);margin-top:.75rem;}}
.comment-box{{width:240px;flex-shrink:0;background:var(--paper-card);border:1px solid var(--rule);
              border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:1.25rem;}}
.comment-box .cb-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
.comment-box p{{font-size:12.5px;color:var(--ink-light);line-height:1.6;margin-bottom:.5rem;}}
.comment-box p:last-child{{margin-bottom:0;}}
.comment-box strong{{color:var(--ink);font-weight:500;}}
.comment-box em{{font-style:normal;color:var(--ink);font-weight:500;}}

footer{{background:var(--paper-warm);border-top:1px solid var(--rule);padding:1.25rem 3rem;
        font-family:'DM Mono',monospace;font-size:11px;color:var(--ink-faint);
        display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;}}
@media(max-width:900px){{
  .chart-with-comment{{flex-direction:column;}} .comment-box{{width:100%;}}
  .kpi-row{{grid-template-columns:repeat(2,1fr);}} header{{padding:2rem 1.5rem;}}
}}
</style>
</head>
<body>

<div class="topnav">
  <div class="topnav-inner">
    <span class="topnav-brand">Indonesia Macro Dashboards · SEKI April 2026</span>
    <div class="topnav-links">
      <a href="econdashboard.html" class="tnav-link">GDP Growth</a>
      <a href="bop_consistency.html" class="tnav-link active">Balance of Payments</a>
    </div>
  </div>
</div>

<header>
  <div class="header-label">SEKI Table 5.1 · Bank Indonesia</div>
  <h1>Balance of Payments<br><em>Quarterly Flows · USD Million</em></h1>
  <div class="header-meta">
    <div class="hm">Source <span>SEKI April 2026 · Bank Indonesia</span></div>
    <div class="hm">Frequency <span>Quarterly</span></div>
    <div class="hm">Coverage <span>2010 Q1 – {latest_p}</span></div>
    <div class="hm">Unit <span>USD Million</span></div>
  </div>
</header>

<div class="window-bar">
  <span class="window-label">Analytical window</span>
  <div class="window-btns">
    <button class="wbtn active" id="btn2y" onclick="setWindow(8)">Short · 2Y</button>
    <button class="wbtn" id="btn4y" onclick="setWindow(16)">Medium · 4Y</button>
    <button class="wbtn" id="btnAll" onclick="setWindow(0)">All · 2010–{latest_p}</button>
  </div>
</div>

<div class="container">

  <div class="kpi-row" style="margin-top:1.5rem;">
    <div class="kpi">
      <div class="kpi-label">Current Account</div>
      <div class="kpi-value {'pos' if ca_now >= 0 else 'neg'}">{ca_now:+,.0f}</div>
      <div class="kpi-sub">{latest_p} · USD mn</div>
      <div class="kpi-delta {'pos' if ca_now >= ca_avg else 'neg'}">8Q avg {ca_avg:+,.0f}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Capital + Financial Account</div>
      <div class="kpi-value {'pos' if kafa_now >= 0 else 'neg'}">{kafa_now:+,.0f}</div>
      <div class="kpi-sub">{latest_p} · USD mn</div>
      <div class="kpi-delta {'pos' if kafa_now >= kafa_avg else 'neg'}">8Q avg {kafa_avg:+,.0f}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Overall Balance</div>
      <div class="kpi-value {'pos' if bal_now >= 0 else 'neg'}">{bal_now:+,.0f}</div>
      <div class="kpi-sub">{latest_p} · USD mn</div>
      <div class="kpi-sub">VI. Neraca Keseluruhan</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Reserve Position</div>
      <div class="kpi-value">{f'{resp_now/1000:,.1f}' if resp_now else '—'}</div>
      <div class="kpi-sub">{latest_p} · USD bn (end-period)</div>
      <div class="kpi-sub">Change this quarter: {res_now:+,.0f} mn</div>
    </div>
  </div>

  <!-- 01: BOP Overview -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">01</span>
      <h2 class="block-title">BOP Overview — Current Account, Capital+Financial, Overall Balance</h2>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Quarterly flows · USD million</h3>
        <div style="position:relative;height:320px"><canvas id="chartBOP"></canvas></div>
        <div class="chart-note">CA = I. Transaksi Berjalan. KA+FA = II + III combined. Balance = VI. Neraca Keseluruhan. Source: SEKI 5.1.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest · {latest_p}</div>
        {ca_comment}
      </div>
    </div>
  </div>

  <!-- 02: Current Account Components -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">02</span>
      <h2 class="block-title">Current Account — Components</h2>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Stacked quarterly flows · USD million</h3>
        <div style="position:relative;height:320px"><canvas id="chartCA"></canvas></div>
        <div class="chart-note">A. Goods · B. Services · C. Primary Income · D. Secondary Income. Line = CA total. Source: SEKI 5.1.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest · {latest_p}</div>
        {ca_comment}
      </div>
    </div>
  </div>

  <!-- 03: Financial Account Components -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">03</span>
      <h2 class="block-title">Financial Account — Components</h2>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Stacked quarterly flows · USD million (positive = net inflow)</h3>
        <div style="position:relative;height:320px"><canvas id="chartFA"></canvas></div>
        <div class="chart-note">1. Direct Investment · 2. Portfolio · 3. Derivatives · 4. Other Investment. Line = FA total. Source: SEKI 5.1.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest · {latest_p}</div>
        {fa_comment}
      </div>
    </div>
  </div>

  <!-- 04: Reserve Assets -->
  <div class="block">
    <div class="block-header">
      <span class="block-num">04</span>
      <h2 class="block-title">Reserve Assets</h2>
    </div>
    <div class="chart-with-comment">
      <div class="chart-full">
        <h3>Quarterly change (USD mn, left axis) · End-period level (USD mn, right axis)</h3>
        <div style="position:relative;height:300px"><canvas id="chartRes"></canvas></div>
        <div class="chart-note">Negative bar = reserve accumulation (BOP sign convention). Dashed line = end-of-period reserve position (Memorandum). Source: SEKI 5.1.</div>
      </div>
      <div class="comment-box">
        <div class="cb-label">Latest · {latest_p}</div>
        {res_comment}
      </div>
    </div>
  </div>

</div>

<footer>
  <span>Balance of Payments · SEKI April 2026</span>
  <span>Source: Bank Indonesia · Table 5.1</span>
</footer>

<script>
const D = {data_js};

const MONO = "'DM Mono', monospace";
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.color = '#8a8780';

const charts = [];
let winN = 8;  // default: Short · 2Y

function setWindow(n) {{
  winN = n;
  document.getElementById('btn2y').classList.toggle('active', n === 8);
  document.getElementById('btn4y').classList.toggle('active', n === 16);
  document.getElementById('btnAll').classList.toggle('active', n === 0);
  charts.forEach(ch => {{
    const sliced = n === 0 ? D.periods : D.periods.slice(-n);
    ch.data.labels = sliced;
    ch.data.datasets.forEach(ds => {{
      ds.data = n === 0 ? ds._full : ds._full.slice(-n);
    }});
    ch.update();
  }});
}}

function sl(arr) {{ return winN === 0 ? arr : arr.slice(-winN); }}

function xAxis() {{
  return {{ ticks:{{ font:{{ family:MONO, size:10 }}, maxRotation:45, autoSkip:true, maxTicksLimit:12 }},
            grid:{{ color:'rgba(0,0,0,0.05)' }} }};
}}
function yAxis(title) {{
  return {{ title:{{ display:true, text:title, font:{{ family:MONO, size:10 }}, color:'#8a8780' }},
            ticks:{{ font:{{ family:MONO, size:10 }}, callback: v => (v/1000).toFixed(0)+'k' }},
            grid:{{ color:'rgba(0,0,0,0.05)' }} }};
}}
function legendRight() {{
  return {{ position:'right', labels:{{ font:{{ family:MONO, size:10 }}, boxWidth:10, padding:10 }} }};
}}
function legend() {{
  return {{ labels:{{ font:{{ family:MONO, size:10 }}, boxWidth:10, padding:10 }} }};
}}
function tip(suffix) {{
  return {{
    backgroundColor:'rgba(26,24,20,0.92)',
    titleFont:{{ family:MONO, size:11 }}, bodyFont:{{ family:MONO, size:12 }}, padding:12,
    itemSort:(a,b) => b.parsed.y - a.parsed.y,
    callbacks:{{ label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y != null ? ctx.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:0}}) : ''}} ${{suffix}}` }}
  }};
}}

function mkDS(label, full, color, opts={{}}) {{
  return {{ label, data:sl(full), borderColor:color, backgroundColor:color, _full:full, ...opts }};
}}

function addChart(ch) {{ charts.push(ch); }}

/* ── Chart 01: BOP Overview ── */
addChart(new Chart(document.getElementById('chartBOP'), {{
  type: 'bar',
  data: {{
    labels: sl(D.periods),
    datasets: [
      mkDS('Current Account', D.ca, '#2563eb', {{
        backgroundColor: D.ca.map(v => 'rgba(37,99,235,0.72)'),
        borderColor:'#2563eb', borderWidth:0.5, borderRadius:1, order:2
      }}),
      mkDS('Capital + Financial Account', D.ka_fa, '#16a34a', {{
        backgroundColor: D.ka_fa.map(v => 'rgba(22,163,74,0.68)'),
        borderColor:'#16a34a', borderWidth:0.5, borderRadius:1, order:3
      }}),
      mkDS('Net Errors & Omissions', D.errors, '#d4cec6', {{
        backgroundColor:'rgba(139,132,124,0.45)',
        borderColor:'#8a8780', borderWidth:0.5, borderRadius:1, order:4
      }}),
      mkDS('Overall Balance', D.balance, '#1a1814', {{
        type:'line', borderWidth:2, pointRadius:2, pointHoverRadius:5,
        tension:0, fill:false, order:1
      }}),
    ]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    interaction:{{ mode:'index', intersect:false }},
    plugins:{{ legend:legendRight(), tooltip:tip('USD mn') }},
    scales:{{ x:xAxis(), y:yAxis('USD million') }}
  }}
}}));

/* ── Chart 02: Current Account Components ── */
addChart(new Chart(document.getElementById('chartCA'), {{
  type: 'bar',
  data: {{
    labels: sl(D.periods),
    datasets: [
      mkDS('A. Goods',            D.ca_goods,   '#2563eb', {{ backgroundColor:'rgba(37,99,235,0.72)',  borderWidth:0.5, stack:'ca', order:2 }}),
      mkDS('B. Services',         D.ca_svcs,    '#dc2626', {{ backgroundColor:'rgba(220,38,38,0.72)',  borderWidth:0.5, stack:'ca', order:2 }}),
      mkDS('C. Primary Income',   D.ca_primary, '#9333ea', {{ backgroundColor:'rgba(147,51,234,0.72)', borderWidth:0.5, stack:'ca', order:2 }}),
      mkDS('D. Secondary Income', D.ca_second,  '#16a34a', {{ backgroundColor:'rgba(22,163,74,0.72)',  borderWidth:0.5, stack:'ca', order:2 }}),
      mkDS('CA Total', D.ca, '#1a1814', {{
        type:'line', borderWidth:2, pointRadius:2, pointHoverRadius:5,
        tension:0, fill:false, order:1
      }}),
    ]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    interaction:{{ mode:'index', intersect:false }},
    plugins:{{ legend:legendRight(), tooltip:tip('USD mn') }},
    scales:{{ x:xAxis(), y:{{ ...yAxis('USD million'), stacked:true }} }}
  }}
}}));

/* ── Chart 03: Financial Account Components ── */
addChart(new Chart(document.getElementById('chartFA'), {{
  type: 'bar',
  data: {{
    labels: sl(D.periods),
    datasets: [
      mkDS('1. Direct Investment',    D.fa_di,  '#0e7490', {{ backgroundColor:'rgba(14,116,144,0.72)',  borderWidth:0.5, stack:'fa', order:2 }}),
      mkDS('2. Portfolio Investment', D.fa_pi,  '#7c3aed', {{ backgroundColor:'rgba(124,58,237,0.72)',  borderWidth:0.5, stack:'fa', order:2 }}),
      mkDS('3. Derivatives',          D.fa_der, '#ca8a04', {{ backgroundColor:'rgba(202,138,4,0.72)',   borderWidth:0.5, stack:'fa', order:2 }}),
      mkDS('4. Other Investment',     D.fa_oi,  '#b5460f', {{ backgroundColor:'rgba(181,70,15,0.72)',   borderWidth:0.5, stack:'fa', order:2 }}),
      mkDS('FA Total', D.fa, '#1a1814', {{
        type:'line', borderWidth:2, pointRadius:2, pointHoverRadius:5,
        tension:0, fill:false, order:1
      }}),
    ]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    interaction:{{ mode:'index', intersect:false }},
    plugins:{{ legend:legendRight(), tooltip:tip('USD mn') }},
    scales:{{ x:xAxis(), y:{{ ...yAxis('USD million'), stacked:true }} }}
  }}
}}));

/* ── Chart 04: Reserve Assets ── */
addChart(new Chart(document.getElementById('chartRes'), {{
  type: 'bar',
  data: {{
    labels: sl(D.periods),
    datasets: [
      mkDS('Reserve Change (flow)', D.res, '#0e7490', {{
        backgroundColor: D.res.map(v => v === null ? null : v < 0 ? 'rgba(14,116,144,0.72)' : 'rgba(181,70,15,0.72)'),
        borderColor:     D.res.map(v => v === null ? null : v < 0 ? '#0e7490' : '#b5460f'),
        borderWidth:0.5, borderRadius:1, order:2, yAxisID:'y'
      }}),
      mkDS('Reserve Position (level)', D.res_pos, '#ca8a04', {{
        type:'line', borderWidth:1.8, pointRadius:0, pointHoverRadius:4,
        tension:0, fill:false, order:1, yAxisID:'y2', borderDash:[4,3]
      }}),
    ]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    interaction:{{ mode:'index', intersect:false }},
    plugins:{{ legend:legend(), tooltip:{{
      backgroundColor:'rgba(26,24,20,0.92)',
      titleFont:{{ family:MONO, size:11 }}, bodyFont:{{ family:MONO, size:12 }}, padding:12,
      callbacks:{{ label: ctx => {{
        const v = ctx.parsed.y;
        if (v == null) return '';
        return ctx.datasetIndex === 0
          ? ` Change: ${{v.toLocaleString('en-US',{{maximumFractionDigits:0}})}} USD mn`
          : ` Position: ${{(v/1000).toFixed(1)}} USD bn`;
      }} }}
    }} }},
    scales:{{
      x: xAxis(),
      y:  {{ ...yAxis('Change (USD mn)'), position:'left' }},
      y2: {{ ...yAxis('Position (USD mn)'), position:'right', grid:{{ drawOnChartArea:false }},
             ticks:{{ font:{{ family:MONO, size:10 }}, callback: v => (v/1000).toFixed(0)+'k' }} }}
    }}
  }}
}}));
</script>
</body>
</html>
"""

out = os.path.join(HTML, "bop_consistency.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written: {out}  ({os.path.getsize(out)//1024} KB)")
