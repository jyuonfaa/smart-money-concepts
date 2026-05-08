import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

def check_logs():
    symbol = "EURUSD=X"
    ohlc = yf.download(symbol, interval="15m", period="7d", progress=False)
    if isinstance(ohlc.columns, pd.MultiIndex):
        ohlc.columns = ohlc.columns.get_level_values(0)
    ohlc.columns = [c.lower() for c in ohlc.columns]
    
    # Handle NY Time
    if ohlc.index.tz is None:
        ohlc.index = ohlc.index.tz_localize("UTC").tz_convert("America/New_York")
    else:
        ohlc.index = ohlc.index.tz_convert("America/New_York")
        
    cons = smc.consolidation(ohlc)
    exp = smc.expansion(ohlc, cons)
    pdsm = PriceDeliveryStateMachine()
    
    results = pdsm.process(ohlc, cons, exp)
    results.index = ohlc.index
    
    print("\n--- RAW INSTITUTIONAL WEEKLY LOG ---")
    # Show the last few entries where WeeklyHigh or WeeklyLow are updated
    relevant = results[(results['WeeklyHigh'].notna()) | (results['WeeklyLow'].notna())]
    print(relevant[['WeeklyHigh', 'WeeklyLow']].tail(10))

if __name__ == "__main__":
    check_logs()
