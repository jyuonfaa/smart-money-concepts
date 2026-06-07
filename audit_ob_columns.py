"""
PRE-STEP (fixed): Verify smc.ob() column names, types, and values on Daily AUDUSD data.
OB DataFrame uses RangeIndex — must iloc into daily OHLC to cross-reference.
"""
import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

# Load AUDUSD 1M data
path = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(path, sep=';',
    names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Build Daily OHLCV
df_daily = df_raw.resample('1D').agg({
    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
}).dropna()
df_daily = df_daily.reset_index()  # make RangeIndex to match ob() output

print(f"Daily bars: {len(df_daily)}")
print()

# Swings
swing_hl = smc.swing_highs_lows(df_daily, swing_length=5)

# OB
ob_df = smc.ob(df_daily, swing_hl)

print("=== smc.ob() CONFIRMED OUTPUT ===")
print(f"Columns : {list(ob_df.columns)}")
print(f"Dtypes  :\n{ob_df.dtypes}")
print()

# OB hits by integer index
ob_hits_idx = ob_df[ob_df['OB'].notna()].index.tolist()
print(f"OB signals: {len(ob_hits_idx)}")
print()

print("=== Full Cross-Reference: OB vs Daily Bar ===")
print(f"{'Idx':>4} {'Date':<12} {'OB':>5} {'OB_Top':>9} {'OB_Bot':>9} {'Open':>9} {'Close':>9} {'BodyMid':>9} {'Stop(Mid)':>10}")
for idx in ob_hits_idx:
    row = ob_df.iloc[idx]
    bar = df_daily.iloc[idx]
    body_mid = (bar['open'] + bar['close']) / 2.0
    print(f"{idx:>4} {str(bar['date'])[:10]:<12} {row['OB']:>5.0f} "
          f"{row['Top']:>9.5f} {row['Bottom']:>9.5f} "
          f"{bar['open']:>9.5f} {bar['close']:>9.5f} "
          f"{body_mid:>9.5f} {body_mid:>10.5f}")

print()
print("=== KEY FINDINGS FOR IMPLEMENTATION ===")
print(f"  OB direction column : 'OB'     (float64, values: 1.0=bullish / -1.0=bearish)")
print(f"  OB high column      : 'Top'    (float32)")
print(f"  OB low column       : 'Bottom' (float32)")
print(f"  ICT stop level      : midpoint of BODY = (open + close) / 2  [NOT Top/Bottom]")
print(f"  OB index type       : RangeIndex (integer) — must iloc, NOT loc by date")
