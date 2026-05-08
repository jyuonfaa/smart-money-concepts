import pandas as pd
import yfinance as yf

def get_killzone(timestamp):
    hour = timestamp.hour + timestamp.minute / 60
    if 19 <= hour:          return "Asian"         # 7:00 PM - 12:00 AM
    elif 2 <= hour < 5:     return "London Open"   # 2:00 AM - 5:00 AM
    elif 7 <= hour < 9:     return "NY Open"       # 7:00 AM - 9:00 AM
    elif 10 <= hour < 11:   return "London Close"  # 10:00 AM - 11:00 AM
    else:                   return "Other"

ohlc = yf.download("EURUSD=X", interval="15m", period="30d", progress=False)
if isinstance(ohlc.columns, pd.MultiIndex):
    ohlc.columns = ohlc.columns.get_level_values(0)
ohlc.columns = [c.lower() for c in ohlc.columns]
ohlc = ohlc[~ohlc.index.duplicated(keep="first")]
if ohlc.index.tz is None:
    ohlc.index = ohlc.index.tz_localize("UTC").tz_convert("America/New_York")
else:
    ohlc.index = ohlc.index.tz_convert("America/New_York")

ohlc["date_str"] = ohlc.index.strftime("%Y-%m-%d")
tagged = set()

print("--- 30-Day Institutional Killzone Audit ---")
print(f"{'Date':<12} {'Type':<5} {'Time (NY)':<12} {'Killzone'}")
print("-"*50)

kz_counts = {"Asian": 0, "London Open": 0, "NY Open": 0, "London Close": 0, "Other": 0}

for date_str, day in ohlc.groupby("date_str"):
    if len(day) < 10:
        continue
    hi_idx = day["high"].idxmax()
    lo_idx = day["low"].idxmin()
    for idx, t in [(hi_idx, "HIGH"), (lo_idx, "LOW")]:
        key = (date_str, t)
        if key not in tagged:
            kz = get_killzone(idx)
            print(f"{date_str:<12} {t:<5} {idx.strftime('%H:%M'):<12} {kz}")
            kz_counts[kz] += 1
            tagged.add(key)

print("-"*50)
print("SUMMARY:")
for kz, count in kz_counts.items():
    print(f"  {kz:<14}: {count} formation(s)")
