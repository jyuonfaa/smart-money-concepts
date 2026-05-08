import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

ohlc = yf.download('USDJPY=X', interval='1d', period='2y', progress=False)
if isinstance(ohlc.columns, pd.MultiIndex):
    ohlc.columns = ohlc.columns.get_level_values(0)
ohlc.columns = [c.lower() for c in ohlc.columns]
ohlc = ohlc[['open', 'high', 'low', 'close', 'volume']]
ohlc.index = pd.to_datetime(ohlc.index).tz_localize(None)

swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
swing_hl.index = ohlc.index
fvg_data = smc.fvg(ohlc, join_consecutive=False)
fvg_data.index = ohlc.index
liq = smc.liquidity(ohlc, swing_hl, range_percent=0.03)
liq.index = ohlc.index
cons = smc.consolidation(ohlc, prd=10, conslen=5)
cons.index = ohlc.index
exp = smc.expansion(ohlc, cons)
exp.index = ohlc.index

pdsm = PriceDeliveryStateMachine()
sr = pdsm.process(ohlc, cons, exp, fvg=fvg_data, liquidity=liq, swing_hl=swing_hl)
sr.index = ohlc.index

print("=== STATE DISTRIBUTION ===")
print(sr["State"].value_counts())

print("\n=== TP CHECK ===")
tp1_segs = sr["TP1"].notna().astype(int).diff().fillna(0)
print(f"TP1 started: {(tp1_segs == 1).sum()}, terminated: {(tp1_segs == -1).sum()}")
# Check if any TP persists to the last bar
if not pd.isna(sr["TP1"].iloc[-1]):
    print("WARNING: TP1 still active at last bar")
if not pd.isna(sr["TP2"].iloc[-1]):
    print("WARNING: TP2 still active at last bar")

print("\n=== TRANSITIONS ===")
prev = None
for i, row in sr.iterrows():
    if row["State"] != prev:
        print(f"  {i.strftime('%Y-%m-%d')}: {prev} -> {row['State']}")
        prev = row["State"]
