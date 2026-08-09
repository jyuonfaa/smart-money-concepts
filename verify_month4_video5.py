import pandas as pd
import numpy as np
import sys
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts import smc

# 1. Load Data
CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_15m = df_raw.resample('15Min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

def run_verify(name, ohlc, swing_len):
    print(f"\n{'='*95}\n{name} - BREAKER BLOCKS VERIFICATION\n{'='*95}")
    swings = smc.swing_highs_lows(ohlc, swing_length=swing_len)
    bb_df = smc._breaker_blocks(ohlc, swings)
    
    # Count raw triplets with a qualifying candle (before activation check)
    hl = swings['HighLow'].values
    idx = np.where(~np.isnan(hl))[0]
    raw_bear = 0
    raw_bull = 0
    
    _open = ohlc['open'].values
    _high = ohlc['high'].values
    _low = ohlc['low'].values
    _close = ohlc['close'].values
    
    for i in range(2, len(idx)):
        prev = idx[i-2]; mid = idx[i-1]; curr = idx[i]
        
        # Bearish RAW
        if hl[prev]==1 and hl[mid]==-1 and hl[curr]==1 and _high[curr] > _high[prev]:
            has_candle = False
            for j in range(mid, prev, -1):
                if _close[j] < _open[j]: has_candle = True; break
            if has_candle: raw_bear += 1
                
        # Bullish RAW
        elif hl[prev]==-1 and hl[mid]==1 and hl[curr]==-1 and _low[curr] < _low[prev]:
            has_candle = False
            for j in range(mid, prev, -1):
                if _close[j] > _open[j]: has_candle = True; break
            if has_candle: raw_bull += 1
            
    # Get confirmed blocks
    blocks = bb_df[~bb_df['BB'].isna()]
    bearish_blocks = blocks[blocks['BB'] == -1]
    bullish_blocks = blocks[blocks['BB'] == 1]
    
    # Print Summary Stats
    print(f"RAW TRIPLETS (raided + candle found, before activation):")
    print(f"  Bearish: {raw_bear}")
    print(f"  Bullish: {raw_bull}")
    print(f"  Total  : {raw_bear + raw_bull}\n")
    
    print(f"CONFIRMED BLOCKS (after MidSwingLevel activation):")
    print(f"  Bearish: {len(bearish_blocks)}")
    print(f"  Bullish: {len(bullish_blocks)}")
    print(f"  Total  : {len(blocks)}\n")
    
    drop_bear = raw_bear - len(bearish_blocks)
    drop_bull = raw_bull - len(bullish_blocks)
    print(f"DROP RATE (Never Activated):")
    print(f"  Bearish: {drop_bear} dropped")
    print(f"  Bullish: {drop_bull} dropped\n")
    
    invalidated_count = blocks['Invalidated'].notna().sum()
    live_count = blocks['Invalidated'].isna().sum()
    print(f"INVALIDATION STATUS (Confirmed Blocks only):")
    print(f"  Invalidated: {invalidated_count}")
    print(f"  Live       : {live_count}\n")
    
    # Structural Invariants
    print("STRUCTURAL INVARIANTS:")
    top_gte_bot = (blocks['BBBodyTop'] >= blocks['BBBodyBottom']).all() if len(blocks) > 0 else True
    print(f"  BBBodyTop >= BBBodyBottom     : {top_gte_bot}")
    
    if len(bearish_blocks) > 0:
        bear_wick_gte_top = (bearish_blocks['BBWickHigh'] >= bearish_blocks['BBBodyTop']).all()
        print(f"  Bearish BBWickHigh >= BodyTop : {bear_wick_gte_top}")
        bear_low_nan = bearish_blocks['BBWickLow'].isna().all()
        print(f"  Bearish BBWickLow is NaN      : {bear_low_nan}")
    else:
        print("  Bearish invariants            : N/A (no blocks)")
        
    if len(bullish_blocks) > 0:
        bull_wick_lte_bot = (bullish_blocks['BBWickLow'] <= bullish_blocks['BBBodyBottom']).all()
        print(f"  Bullish BBWickLow <= BodyBot  : {bull_wick_lte_bot}")
        bull_high_nan = bullish_blocks['BBWickHigh'].isna().all()
        print(f"  Bullish BBWickHigh is NaN     : {bull_high_nan}")
    else:
        print("  Bullish invariants            : N/A (no blocks)")
        
    print("\nPER-BLOCK DETAIL TABLE (First 15):")
    print(f"{'Date':<18} {'Dir':<4} {'BodyTop':<8} {'BodyBot':<8} {'WickHigh':<8} {'WickLow':<8} {'MidSwing':<8} {'RaidLvl':<8} {'Invalidated'}")
    print("-" * 95)
    
    for date, row in blocks.head(15).iterrows():
        d_str = str(date)
        dir_str = "BEAR" if row['BB'] == -1 else "BULL"
        top = f"{row['BBBodyTop']:.5f}"
        bot = f"{row['BBBodyBottom']:.5f}"
        w_h = f"{row['BBWickHigh']:.5f}" if not pd.isna(row['BBWickHigh']) else "NaN"
        w_l = f"{row['BBWickLow']:.5f}" if not pd.isna(row['BBWickLow']) else "NaN"
        mid = f"{row['MidSwingLevel']:.5f}"
        raid = f"{row['RaidLevel']:.5f}"
        inv = "LIVE" if pd.isna(row['Invalidated']) else str(ohlc.index[int(row['Invalidated'])])
        print(f"{d_str:<18} {dir_str:<4} {top:<8} {bot:<8} {w_h:<8} {w_l:<8} {mid:<8} {raid:<8} {inv}")

run_verify("AUDUSD 2016 DAILY", df_daily, 10)
run_verify("AUDUSD 2016 15M", df_15m, 10)
