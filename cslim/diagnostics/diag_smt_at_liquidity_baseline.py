"""
Baseline capture: smt_at_liquidity = True rows BEFORE liquidity() sweep fix.
Uses same data as verify_month3_video5.py (AUDUSD + DXY 2016 daily)
but explicitly passes liquidity_df to _smt_divergence so the path is exercised.
"""
import pandas as pd
from smartmoneyconcepts.smc import smc, _smt_divergence

# Load same data as verify_month3_video5.py
chunks = []
for chunk in pd.read_csv(
    'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'],
    index_col=False, chunksize=50_000
):
    chunk['date'] = pd.to_datetime(chunk['date'], format='%Y%m%d %H%M%S')
    chunk.set_index('date', inplace=True)
    daily_chunk = chunk.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last'})
    chunks.append(daily_chunk)
aud_daily = pd.concat(chunks).groupby(level=0).agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

dxy_daily = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DXY_Daily_2016.csv', index_col='date', parse_dates=True)

# Build liquidity df (same way verify_month3_video5 would if it passed it)
aud_swings_v1 = smc.swing_highs_lows(aud_daily, swing_length=5)
liq_df = smc.liquidity(aud_daily, aud_swings_v1)

# Get swings for _smt_divergence
aud_swings = smc.swing_highs_lows_v4(aud_daily)

# Call _smt_divergence directly with liquidity_df to exercise the smt_at_liquidity path
smt_df = _smt_divergence(
    ohlc=aud_daily,
    benchmark_ohlc=dxy_daily,
    asset_swings=aud_swings,
    correlation="inverse",
    lookaround_bars=5,
    liquidity_df=liq_df
)

# Print all columns available
print("Columns in smt_df:", list(smt_df.columns))
print()

# Print smt_at_liquidity = True rows
at_liq = smt_df[smt_df['smt_at_liquidity'] == True]
not_at_liq = smt_df[smt_df['smt_at_liquidity'] == False]

print(f"Total rows: {len(smt_df)}")
print(f"smt_at_liquidity = True:  {len(at_liq)} rows")
print(f"smt_at_liquidity = False: {len(not_at_liq)} rows")
print()

# Print the dates
print("=== Dates where smt_at_liquidity = True ===")
for ts in at_liq.index:
    row = smt_df.loc[ts]
    flags = []
    for col in ['smt_bullish_div','smt_bearish_div','smt_bullish_div_bm','smt_bearish_div_bm','smt_trend_confirmed','smt_confirmed']:
        if col in smt_df.columns and row[col]:
            flags.append(col)
    print(f"  {ts.date()} | {', '.join(flags) if flags else 'no signal flags'}")

print()
print("=== Dates where smt_at_liquidity = False ===")
for ts in not_at_liq.index:
    row = smt_df.loc[ts]
    flags = []
    for col in ['smt_bullish_div','smt_bearish_div','smt_bullish_div_bm','smt_bearish_div_bm','smt_trend_confirmed','smt_confirmed']:
        if col in smt_df.columns and row[col]:
            flags.append(col)
    print(f"  {ts.date()} | {', '.join(flags) if flags else 'no signal flags'}")

print()

# Also print the Swept column from liquidity to show what bar indices are currently recorded
print("=== Liquidity Swept values (raw — current wick-based) ===")
swept_rows = liq_df[liq_df['Swept'].notna() & (liq_df['Swept'] > 0)]
print(f"Total pools with Swept != 0: {len(swept_rows)}")
for idx, row in swept_rows.iterrows():
    dir_str = "BULL" if row['Liquidity'] == 1 else "BEAR"
    print(f"  Pool at bar {idx} ({pd.Timestamp(idx).date() if hasattr(idx,'date') else idx})  dir={dir_str}  Level={row['Level']:.5f}  Swept at bar={int(row['Swept'])}")
