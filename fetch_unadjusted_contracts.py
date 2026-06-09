"""
Fetch unadjusted December 2016 futures contracts for ZN and ZB.
These match exactly what ICT used in Month 3 Video 6.

ZNZ16 = 10-Year Note December 2016 contract
ZBZ16 = 30-Year Bond December 2016 contract

yfinance tickers for expired contracts: ZNZ16.CBT and ZBZ16.CBT
We also re-fetch DXY and EURUSD as-is (no adjustment needed for spot/index).
"""
import yfinance as yf
import pandas as pd
import os

OUT_DIR = "tests/test_data/MACRO"
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_and_save(ticker, filename, label):
    print(f"Fetching {label} ({ticker})...")
    data = yf.download(ticker, start="2016-01-01", end="2016-12-31", interval="1d", auto_adjust=False)

    if data.empty:
        print(f"  WARNING: {ticker} returned empty. Trying alternate ticker...")
        return False

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = [c.lower() for c in data.columns]

    data.reset_index(inplace=True)
    data.rename(columns={"date": "date", "open": "open", "high": "high",
                          "low": "low", "close": "close", "volume": "volume"}, inplace=True)

    # Keep only OHLCV
    keep = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in data.columns]
    data = data[keep]
    data["date"] = pd.to_datetime(data["date"]).dt.date.astype(str)

    path = os.path.join(OUT_DIR, filename)
    data.to_csv(path, index=False)
    print(f"  Saved {len(data)} rows -> {path}")
    print(f"  Sample: {data[['date','high','low','close']].head(3).to_string(index=False)}")
    return True

# Attempt expired contract tickers (yfinance supports some via CBT suffix)
ok_zn = fetch_and_save("ZNZ16.CBT", "ZNZ16_Daily_2016.csv", "10-Year Note Dec 2016 (ZNZ16)")
if not ok_zn:
    # Fallback: try without exchange suffix
    ok_zn = fetch_and_save("ZNZ16", "ZNZ16_Daily_2016.csv", "10-Year Note Dec 2016 (ZNZ16)")

ok_zb = fetch_and_save("ZBZ16.CBT", "ZBZ16_Daily_2016.csv", "30-Year Bond Dec 2016 (ZBZ16)")
if not ok_zb:
    ok_zb = fetch_and_save("ZBZ16", "ZBZ16_Daily_2016.csv", "30-Year Bond Dec 2016 (ZBZ16)")

# DXY and EURUSD don't have contract roll issues - refetch cleanly
fetch_and_save("DX-Y.NYB", "DXY_Daily_2016.csv", "Dollar Index (DXY)")
fetch_and_save("EURUSD=X", "EURUSD_Daily_2016.csv", "EURUSD")

print()
print("=== FETCH COMPLETE ===")
print(f"ZNZ16: {'OK' if ok_zn else 'FAILED'}")
print(f"ZBZ16: {'OK' if ok_zb else 'FAILED'}")
