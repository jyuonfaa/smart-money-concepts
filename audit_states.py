import yfinance as yf
import pandas as pd
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine
from smartmoneyconcepts import smc

# 1. Get Data
timeframe = '15m'
ohlc = yf.download('USDCHF=X', interval=timeframe, period='1wk', progress=False)
if isinstance(ohlc.columns, pd.MultiIndex): ohlc.columns = ohlc.columns.get_level_values(0)
ohlc.columns = [c.lower() for c in ohlc.columns]
ohlc.index = pd.to_datetime(ohlc.index).tz_localize(None)

# 2. Indicators
swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
fvg = smc.fvg(ohlc)
cons = smc.consolidation(ohlc)
exp = smc.expansion(ohlc, cons)
rev = detect_reversals(ohlc, swing_hl)

# 3. State Machine
pdsm = PriceDeliveryStateMachine()
res = pdsm.process(ohlc, cons, exp, fvg=fvg, reversals=rev)
res.index = ohlc.index

# 4. Audit Logic
res['NY_Time'] = res.index.tz_localize('UTC').tz_convert('America/New_York')
res['Hour'] = res['NY_Time'].dt.hour
res['Min'] = res['NY_Time'].dt.minute

days = res['NY_Time'].dt.date.unique()[-3:-1]
for day in days:
    print(f"\n--- AUDIT FOR {day} (New York Time) ---")
    day_data = res[res['NY_Time'].dt.date == day]
    
    manip = day_data[(day_data['Hour'] >= 0) & (day_data['Hour'] < 5)]
    pre_ny = day_data[(day_data['Hour'] >= 5) & (day_data['Hour'] < 8)]
    retr = day_data[(day_data['Hour'] == 8) & (day_data['Min'] <= 30)]
    lcr = day_data[(day_data['Hour'] >= 10) & (day_data['Hour'] <= 11)]

    print(f"00:00-05:00 (Manipulation Window):  {manip['State'].unique()}")
    print(f"05:00-08:00 (Consolidation Window): {pre_ny['State'].unique()}")
    print(f"08:00-08:30 (Retracement Window):  {retr['State'].unique()}")
    print(f"10:00-11:00 (London Close Window):  {lcr['State'].unique()}")
