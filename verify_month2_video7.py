import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals, false_flag_signals

def run_diagnostic():
    print("--- 1. LOADING DATA ---")
    CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)

    # Daily resample (RangeIndex for smc.ob() compatibility)
    df_daily_dt = df_raw.resample('1D').agg({
        'open':'first','high':'max','low':'min','close':'last','volume':'sum'
    }).dropna()
    df_daily_ri = df_daily_dt.reset_index()

    # Focus window for daily
    df_daily_ri_focus = df_daily_ri[
        (df_daily_ri['date'] >= '2016-08-01') & (df_daily_ri['date'] <= '2016-10-01')
    ].reset_index(drop=True)

    # Standard 15M resample
    df_15m = df_raw.resample('15min').agg({
        'open':'first','high':'max','low':'min','close':'last','volume':'sum'
    }).dropna()

    # 4H Data
    df_4h = df_raw.resample('4h').agg({
        'open':'first','high':'max','low':'min','close':'last','volume':'sum'
    }).dropna()

    print("--- 2. RUNNING DETECTION ---")
    # Detect daily OBs and Retracements
    daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
    daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)
    daily_retracements = smc.retracements(df_daily_ri_focus, daily_swings)

    # Convert daily_ohlc focus window to DateTime index for time mapping
    daily_ohlc_time = df_daily_ri_focus.copy()
    daily_ohlc_time.set_index('date', inplace=True)

    # 15M signals
    swings_15m    = smc.swing_highs_lows(df_15m, swing_length=10)
    reversals_15m = detect_reversals(df_15m, swings_15m)
    consolidation_15m = smc.consolidation(df_15m, prd=10, conslen=5)

    ts_15m = turtle_soup_signals(
        df_15m, reversals_15m, daily_ob, df_daily_ri_focus,
        use_daily_ob_stop=False, refinement_level='15M'
    )

    swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
    ob_4h = smc.ob(df_4h, swings_4h)
    disp_4h = smc.displacement(df_4h)

    ff_15m = false_flag_signals(
        ohlc_daily=df_daily_ri_focus.set_index('date'),
        ohlc_ltf=df_15m,
        ohlc_4h=df_4h,
        daily_consolidation=consolidation_15m, # the old signature passed this as daily? Actually, the new signature needs daily consolidation.
        daily_retracements=daily_retracements,
        daily_turtle_soup=ts_15m,
        ob_4h=ob_4h,
        disp_4h=disp_4h
    )

    bull_flags = ff_15m[ff_15m['false_bull_flag'] == True]
    bear_flags = ff_15m[ff_15m['false_bear_flag'] == True]

    print(f"- Total false_bull_flag signals: {len(bull_flags)}")
    print(f"- Total false_bear_flag signals: {len(bear_flags)}")

    print("\n- First 5 rows where false_bull_flag == True:")
    if not bull_flags.empty:
        for idx, row in bull_flags.head(5).iterrows():
            print(f"  Time: {idx}, trap_entry: {row['trap_entry']}, trap_stop_loss: {row['trap_stop_loss']}")
    else:
        print("  None found.")

    print("\n- First 5 rows where false_bear_flag == True:")
    if not bear_flags.empty:
        for idx, row in bear_flags.head(5).iterrows():
            print(f"  Time: {idx}, trap_entry: {row['trap_entry']}, trap_stop_loss: {row['trap_stop_loss']}")
    else:
        print("  None found.")

    print("\n--- 3. VERIFYING STOP LOSS LOGIC ---")
    all_bull_correct = True
    for idx, row in bull_flags.iterrows():
        # false_bull_flag means Bearish Execution. We sell at entry, stop loss should be ABOVE entry
        if row['trap_stop_loss'] <= row['trap_entry']:
            print(f"FAILED: false_bull_flag at {idx} has stop loss {row['trap_stop_loss']} <= entry {row['trap_entry']}")
            all_bull_correct = False
    
    if all_bull_correct:
        print("PASS: trap_stop_loss > trap_entry for ALL false_bull_flag rows.")

    all_bear_correct = True
    for idx, row in bear_flags.iterrows():
        # false_bear_flag means Bullish Execution. We buy at entry, stop loss should be BELOW entry
        if row['trap_stop_loss'] >= row['trap_entry']:
            print(f"FAILED: false_bear_flag at {idx} has stop loss {row['trap_stop_loss']} >= entry {row['trap_entry']}")
            all_bear_correct = False
            
    if all_bear_correct:
        print("PASS: trap_stop_loss < trap_entry for ALL false_bear_flag rows.")

if __name__ == '__main__':
    run_diagnostic()
