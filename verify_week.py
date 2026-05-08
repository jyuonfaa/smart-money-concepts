import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine
from mtf_engine import MTFEngine

def verify_latest_week():
    symbol = "EURUSD=X"
    # Download enough for 15m to cover this week
    ohlc = yf.download(symbol, interval="15m", period="7d", progress=False)
    if isinstance(ohlc.columns, pd.MultiIndex):
        ohlc.columns = ohlc.columns.get_level_values(0)
    ohlc.columns = [c.lower() for c in ohlc.columns]
    ohlc.index = ohlc.index.tz_localize(None)
    
    # We don't even need the full engine just for this, but let's be consistent
    cons = smc.consolidation(ohlc, prd=10, conslen=5)
    exp = smc.expansion(ohlc, cons)
    pdsm = PriceDeliveryStateMachine()
    results = pdsm.process(ohlc, cons, exp)
    results.index = ohlc.index
    
    # Find the high and low of the latest week
    ohlc["week"] = ohlc.index.isocalendar().week
    latest_week = ohlc["week"].max()
    this_week = ohlc[ohlc["week"] == latest_week]
    
    high_time = this_week["high"].idxmax()
    low_time = this_week["low"].idxmin()
    
    print(f"Week Number: {latest_week}")
    print(f"Weekly High: {high_time} ({high_time.day_name()}) at {this_week['high'].max()}")
    print(f"Weekly Low:  {low_time} ({low_time.day_name()}) at {this_week['low'].min()}")

if __name__ == "__main__":
    verify_latest_week()
