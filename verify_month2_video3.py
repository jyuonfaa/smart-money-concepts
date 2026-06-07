"""
verify_month2_video3.py — Quality Gate for Month 2 Video 3
"""

import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
from risk_engine import EXIT_SCHEDULE_V3

def test_exit_schedule_v3():
    required_keys = [3, 9, 15]
    for k in required_keys:
        if k not in EXIT_SCHEDULE_V3:
            raise ValueError(f"Missing key {k} in EXIT_SCHEDULE_V3")
    if EXIT_SCHEDULE_V3[15]['action'] != 'close':
        raise ValueError("Key 15 should have action 'close'")
    print("[PASS] EXIT_SCHEDULE_V3 structure is correct")
    
def test_1h_target_ladder():
    CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    
    df_daily_focus = df_daily.loc['2016-01-01':'2016-04-01'].reset_index()
    df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-01-01':'2016-04-01']
    df_1h = df_raw.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-01-01':'2016-04-01']

    daily_swings = smc.swing_highs_lows(df_daily_focus, swing_length=5)
    daily_ob = smc.ob(df_daily_focus, daily_swings)

    swings_15m = smc.swing_highs_lows(df_15m, swing_length=10)
    reversals_15m = detect_reversals(df_15m, swings_15m)
    liq_15m = smc.liquidity(df_15m, swings_15m)
    liq_15m.index = df_15m.index

    swings_1h = smc.swing_highs_lows(df_1h, swing_length=10)
    liq_1h = smc.liquidity(df_1h, swings_1h)
    liq_1h.index = df_1h.index

    ts_15m = turtle_soup_signals(
        ohlc=df_15m, reversals=reversals_15m, daily_ob=daily_ob, daily_ohlc=df_daily_focus,
        liq_df=liq_15m, use_daily_ob_stop=True, refinement_level='15M', liq_1h=liq_1h
    )

    bulls = ts_15m[ts_15m['turtle_soup_bull']]
    bears = ts_15m[ts_15m['turtle_soup_bear']]
    
    print(f"Total bull signals: {len(bulls)}")
    print(f"Total bear signals: {len(bears)}")

    failures = 0
    checked_bulls = 0
    bull_1h_populated = 0
    for ts, row in bulls.iterrows():
        t1 = row['ts_target_near']
        t2 = row['ts_target_far']
        t3 = row['ts_target_1h']
        print(f"Bull at {ts}: t1={t1}, t2={t2}, t3={t3}")
        if not np.isnan(t3):
            bull_1h_populated += 1
        if not np.isnan(t1) and not np.isnan(t2):
            checked_bulls += 1
            if not (t1 <= t2): failures += 1
            if not np.isnan(t3):
                if not (t3 > t2): failures += 1
                
    checked_bears = 0
    bear_1h_populated = 0
    for ts, row in bears.iterrows():
        t1 = row['ts_target_near']
        t2 = row['ts_target_far']
        t3 = row['ts_target_1h']
        print(f"Bear at {ts}: t1={t1}, t2={t2}, t3={t3}")
        if not np.isnan(t3):
            bear_1h_populated += 1
        if not np.isnan(t1) and not np.isnan(t2):
            checked_bears += 1
            if not (t1 >= t2): failures += 1
            if not np.isnan(t3):
                if not (t3 < t2): failures += 1

    print(f"ts_target_1h populated: {bull_1h_populated} of {len(bulls)} bull signals, {bear_1h_populated} of {len(bears)} bear signals")
                
    if failures > 0:
        raise ValueError(f"Ladder order failure in {failures} signals.")
    else:
        print(f"[PASS] Ladders verified. ({checked_bulls} bulls, {checked_bears} bears checked)")

if __name__ == "__main__":
    print("--- Video 3 Verification ---")
    test_exit_schedule_v3()
    test_1h_target_ladder()
    print("All checks PASSED.")
