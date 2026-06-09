import yfinance as yf
import pandas as pd
import os

def fetch_data(ticker, filename):
    print(f"Fetching {ticker}...")
    data = yf.download(ticker, start="2016-01-01", end="2017-01-01", interval="1d")
    
    if data.empty:
        print(f"Failed to fetch {ticker} - DataFrame is empty!")
        return False
        
    # flatten multi-index columns if present (yfinance sometimes returns them)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
        
    # Normalize column names for our engine
    data.reset_index(inplace=True)
    data.columns = [c.lower() for c in data.columns]
    
    out_dir = "tests/test_data/MACRO"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    data.to_csv(out_path, index=False)
    print(f"Saved {ticker} to {out_path} ({len(data)} rows)")
    return True

if __name__ == "__main__":
    fetch_data("ZN=F", "ZN_Daily_2016.csv")
    fetch_data("ZB=F", "ZB_Daily_2016.csv")
    fetch_data("ZF=F", "ZF_Daily_2016.csv")
    fetch_data("DX-Y.NYB", "DXY_Daily_2016.csv")
    fetch_data("EURUSD=X", "EURUSD_Daily_2016.csv")
