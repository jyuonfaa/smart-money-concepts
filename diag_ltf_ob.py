import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')

df_15m = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
swings_15m = smc.swing_highs_lows(df_15m, swing_length=5)
ob_15m     = smc.ob(df_15m, swings_15m)

ob_15m_times = df_15m.index.values

episodes = [
    ('2016-04-14', 'bear', 0.76539), # False Bull Flag (Bearish Trap)
    ('2016-06-21', 'bear', 0.74680),
    ('2016-10-19', 'bear', 0.76970),
    ('2016-11-08', 'bear', 0.76800),
]

for ep_date_str, ep_type, ctop in episodes:
    ep_ts = pd.Timestamp(ep_date_str)
    
    # 1. Find the LTF OB formed during/after the sweep.
    # Start searching from the episode day.
    start_idx = int(np.searchsorted(ob_15m_times, np.datetime64(ep_ts)))
    
    ob_top, ob_bot = np.nan, np.nan
    ob_time = None
    
    # Look ahead up to 2 days for the structural break / OB
    for k in range(start_idx, min(start_idx + 192, len(df_15m))):
        if ep_type == 'bear' and ob_15m['OB'].iloc[k] == -1.0:
            ob_top = ob_15m['Top'].iloc[k]
            ob_bot = ob_15m['Bottom'].iloc[k]
            ob_time = df_15m.index[k]
            break
        elif ep_type == 'bull' and ob_15m['OB'].iloc[k] == 1.0:
            ob_top = ob_15m['Top'].iloc[k]
            ob_bot = ob_15m['Bottom'].iloc[k]
            ob_time = df_15m.index[k]
            break
            
    print(f"\n=== Episode {ep_date_str} ({ep_type}) ===")
    if pd.isna(ob_bot):
        print("  -> No LTF OB found within 2 days.")
        continue
        
    print(f"  -> First LTF OB found at {ob_time}: Zone {ob_bot:.5f} - {ob_top:.5f}")
    
    # 2. Find the entry return to this OB
    entry_found = False
    for j in range(k + 1, min(k + 192, len(df_15m))):
        h = df_15m['high'].iloc[j]
        l = df_15m['low'].iloc[j]
        c = df_15m['close'].iloc[j]
        
        if ep_type == 'bear':
            if h >= ob_bot and h <= ob_top: # Touch the OB zone
                print(f"  -> ENTRY at {df_15m.index[j]} (High {h:.5f} hit zone)")
                entry_found = True
                break
        else:
            if l <= ob_top and l >= ob_bot:
                print(f"  -> ENTRY at {df_15m.index[j]} (Low {l:.5f} hit zone)")
                entry_found = True
                break
                
    if not entry_found:
        print("  -> No return to OB zone.")
