"""fetch_financial.py — pull USD/IDR and IHSG from Yahoo Finance.
Run this before build_combined.py to refresh the Financial tab data.
Usage: python fetch_financial.py
"""
import yfinance as yf
import json, os
from datetime import datetime

OUTPUT = r"C:\work\economist\rawdata\financial"
os.makedirs(OUTPUT, exist_ok=True)

TICKERS = {
    "fx":     {"USDIDR": "USDIDR=X"},
    "equity": {"IHSG":   "^JKSE"},
}

WINDOWS = [
    {"key": "3y", "label": "3 Years · Monthly",  "period": "3y",  "interval": "1mo"},
    {"key": "1m", "label": "Last Month · Daily",  "period": "1mo", "interval": "1d"},
    {"key": "1w", "label": "Last Week · Hourly",  "period": "5d",  "interval": "1h"},
]

def fetch_window(window):
    period, interval = window["period"], window["interval"]
    fmt = "%Y-%m-%d %H:%M" if interval == "1h" else "%Y-%m-%d"
    result = {
        "fetched_at": datetime.now().isoformat(),
        "window_key": window["key"],
        "window_label": window["label"],
        "fx": {},
        "equity": {},
    }
    for group, tickers in TICKERS.items():
        for name, ticker in tickers.items():
            try:
                df = yf.download(ticker, period=period, interval=interval,
                                 progress=False, auto_adjust=True)
                if df.empty:
                    print(f"  WARNING: no data for {name} ({ticker})")
                    continue
                col = df["Close"]
                if hasattr(col, "squeeze"):
                    col = col.squeeze()
                closes = col.dropna()
                periods = [t.strftime(fmt) for t in closes.index]
                values  = [round(float(v), 2) for v in closes.to_numpy().flatten()]
                result[group][name] = {
                    "ticker":  ticker,
                    "periods": periods,
                    "values":  values,
                }
                print(f"  {group.upper():6} {name}: {len(values)} pts, latest {values[-1]:>10,.2f}")
            except Exception as e:
                print(f"  ERROR {name}: {e}")
    return result

if __name__ == "__main__":
    for window in WINDOWS:
        print(f"\nFetching {window['label']}...")
        data = fetch_window(window)
        path = os.path.join(OUTPUT, f"financial_{window['key']}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved: {path}")
    print("\nDone. Run build_combined.py to rebuild the dashboard.")
