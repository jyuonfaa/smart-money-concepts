import sys
import pandas as pd
import numpy as np
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts.smc import smc

# Suppress pandas chained assignment warnings
pd.options.mode.chained_assignment = None

def verify_propulsion(df, timeframe_name):
    print(f"\n{'='*50}")
    print(f"Propulsion Blocks Verification: {timeframe_name}")
    print(f"{'='*50}")
    
    # Run dependencies
    # swing_length=5 matches all other M4 verify scripts (M4V4/V5/V6 all use swing_length=5).
    # Default of 50 on daily data yields only 4 swings (1 OB) -- not a representative test.
    swing_hl = smc.swing_highs_lows(df, swing_length=5)
    ob_df = smc.ob(df, swing_hl)
    
    # Count skipped vs valid anchors manually
    valid_ob_idx = np.where(ob_df['OB'].notna())[0]
    bull_skipped = 0
    bear_skipped = 0
    for idx in valid_ob_idx:
        direction = ob_df['OB'].iloc[idx]
        op = df['open'].iloc[idx]
        cl = df['close'].iloc[idx]
        if direction == 1 and cl > op:
            bull_skipped += 1
        elif direction == -1 and cl < op:
            bear_skipped += 1
            
    # Run detector
    pb_df = smc._propulsion_blocks(df, ob_df)
    
    pb_valid = pb_df[pb_df['PB'].notna()]
    total_pb = len(pb_valid)
    bull_pb = len(pb_valid[pb_valid['PB'] == 1])
    bear_pb = len(pb_valid[pb_valid['PB'] == -1])
    invalidated_pb = len(pb_valid[pb_valid['Invalidated'].notna()])
    live_pb = total_pb - invalidated_pb
    
    # Print summary
    print(f"\nSUMMARY STATS:")
    print(f"Total OB Anchors Evaluated: {len(valid_ob_idx)}")
    print(f"Anchors Skipped (Color Guard): {bull_skipped} Bullish, {bear_skipped} Bearish")
    print(f"Total Propulsion Blocks: {total_pb}")
    print(f"Bullish PBs: {bull_pb}")
    print(f"Bearish PBs: {bear_pb}")
    print(f"Invalidated PBs: {invalidated_pb}")
    print(f"Live/Active PBs: {live_pb}")
    
    # Check Invariants
    invariant_geom = True
    invariant_time = True
    for i, row in pb_valid.iterrows():
        # PBTop >= PBBottom
        if row['PBTop'] < row['PBBottom']:
            invariant_geom = False
            
        # MT Violated <= Invalidated (if both exist)
        mtv = row['MeanThresholdViolated']
        inv = row['Invalidated']
        if pd.notna(mtv) and pd.notna(inv):
            if mtv > inv:
                invariant_time = False
                
    print(f"\nSTRUCTURAL INVARIANTS:")
    print(f"PBTop >= PBBottom always: {'PASSED' if invariant_geom else 'FAILED'}")
    print(f"MeanThresholdViolated <= Invalidated (when both present): {'PASSED' if invariant_time else 'FAILED'}")
    
    # Print detail table
    print(f"\nDETAIL TABLE:")
    if total_pb > 0:
        print(f"{'Date':<20} | {'Dir':<4} | {'PBTop':<9} | {'PBBottom':<9} | {'AnchorOB_Index':<20} | {'MT_Violated':<20} | {'Invalidated':<20}")
        print("-" * 115)
        for ts, row in pb_valid.iterrows():
            d_str = "BULL" if row['PB'] == 1 else "BEAR"
            anch_str = str(row['AnchorOB_Index'])
            mtv_str = str(row['MeanThresholdViolated']) if pd.notna(row['MeanThresholdViolated']) else "NaN"
            inv_str = str(row['Invalidated']) if pd.notna(row['Invalidated']) else "NaN"
            print(f"{str(ts):<20} | {d_str:<4} | {row['PBTop']:<9.5f} | {row['PBBottom']:<9.5f} | {anch_str:<20} | {mtv_str:<20} | {inv_str:<20}")
    else:
        print("No Propulsion Blocks detected.")

# Load Data
print("Loading AUDUSD 2016...")
CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily = df_raw.resample('D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

verify_propulsion(df_daily, "Daily")
verify_propulsion(df_15m, "15M")
