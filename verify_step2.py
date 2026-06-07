import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

def verify_step2():
    print("VERIFICATION STEP 2: AUDUSD Sept 2016 (Sep 11-18)")
    
    # Load HistData
    path = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S').dt.tz_localize(None)
    df_raw.set_index('date', inplace=True)
    
    # Resample to 15m
    df_15m_full = df_raw.loc['2016-08-01':'2016-10-31'].resample('15min').agg({
        'open':'first','high':'max','low':'min','close':'last'
    }).dropna()
    df_15m_full.index = df_15m_full.index.tz_localize(None)

    # Run Scanners
    swings = smc.swing_highs_lows_v4(df_15m_full)
    if 'type' in swings.columns:
        swings['HighLow'] = swings['type'].map({'HIGH': 1, 'LOW': -1})
        swings['Level'] = swings['p']

    fvgs = smc.fvg(df_15m_full)
    if isinstance(fvgs.index, pd.RangeIndex): fvgs.index = df_15m_full.index
    else: fvgs.index = fvgs.index.tz_localize(None)
    
    liq = smc.liquidity(df_15m_full, swings)
    if isinstance(liq.index, pd.RangeIndex): liq.index = df_15m_full.index
    else: liq.index = liq.index.tz_localize(None)
    
    swept_ts = []
    for s in liq['Swept']:
        if pd.isna(s) or s == 0:
            swept_ts.append(pd.NaT)
        else:
            swept_ts.append(df_15m_full.index[int(s)])
    liq['Swept_Time'] = swept_ts
    
    # Select target range
    df_15m = df_15m_full.loc['2016-09-01':'2016-09-30']
    
    # Filter scanners - USE NAN FOR EMPTY
    exp = fvgs.reindex(df_15m.index)
    if 'FVG' in exp.columns:
        exp.rename(columns={'FVG': 'Expansion'}, inplace=True)
    
    print(f"DEBUG: Expansion non-NaN count: {exp['Expansion'].count()}")
    
    cons = smc.consolidation(df_15m_full, prd=10, conslen=5)
    cons_a = cons.reindex(df_15m.index)
    
    swings_a = swings[swings['ts'] <= df_15m.index[-1]]
    liq_a = liq.reindex(df_15m.index)
    
    # Run State Machine
    sm = PriceDeliveryStateMachine()
    audit = sm.process(
        ohlc=df_15m,
        consolidation=cons_a,
        expansion=exp,
        liquidity=liq_a,
        swing_hl=swings_a
    )
    
    print("\nTOTAL ENVIRONMENT COUNTS (September):")
    print(audit["SovereignEnv"].value_counts())
    
    target_range = audit.loc["2016-09-11":"2016-09-18"]
    print("\nENVIRONMENT COUNTS (Sep 11-18):")
    print(target_range["SovereignEnv"].value_counts())

    print("\n--- TRANSITION AUDIT ---")
    transitions = audit['SovereignEnv'][audit['SovereignEnv'] != audit['SovereignEnv'].shift()]
    print(f"Total genuine transitions: {len(transitions)}")
    
    # Show average duration of each LRR and HRR block in candles
    lrr_blocks = []
    hrr_blocks = []
    current_start = audit.index[0]
    current_env = audit['SovereignEnv'].iloc[0]
    for ts, row in audit.iterrows():
        if row['SovereignEnv'] != current_env:
            duration = (ts - current_start).total_seconds() / (15 * 60)
            if current_env == 'LRR':
                lrr_blocks.append(duration)
            else:
                hrr_blocks.append(duration)
            current_start = ts
            current_env = row['SovereignEnv']
            
    if len(lrr_blocks) > 0:
        print(f"Avg LRR block: {sum(lrr_blocks)/len(lrr_blocks):.1f} candles")
    if len(hrr_blocks) > 0:
        print(f"Avg HRR block: {sum(hrr_blocks)/len(hrr_blocks):.1f} candles")

if __name__ == "__main__":
    verify_step2()
