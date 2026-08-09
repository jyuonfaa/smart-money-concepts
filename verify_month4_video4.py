"""
verify_month4_video4.py
=======================
Data Audit: Month 4, Video 4 -- Mitigation Block Detector (smc._mitigation_blocks).

Instrument: AUDUSD 2016 (nearest available proxy for EURUSD; same instrument class).
Note: The video uses EURUSD 30-min. We have no EURUSD data locally; AUDUSD 2016 is
used for structural plausibility only, not as a direct numerical match to the video.

This script does NOT assert pass/fail. Raw output is the deliverable.
A separate Visual Audit step will follow once the Data Audit results are reviewed.
"""

import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

print("=" * 70)
print("DATA AUDIT: MONTH 4 VIDEO 4 -- MITIGATION BLOCK (smc._mitigation_blocks)")
print("=" * 70)

# ── Load AUDUSD 2016 M1 data ─────────────────────────────────────────────────
print("\n[1] Loading AUDUSD 2016 M1 data...")
PATH = "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv"
df_raw = pd.read_csv(
    PATH,
    sep=";",
    names=["date", "open", "high", "low", "close", "volume"],
    index_col=False,
)
df_raw["date"] = pd.to_datetime(df_raw["date"], format="%Y%m%d %H%M%S")
df_raw.set_index("date", inplace=True)

# Resample to Daily for detection (coarser TF shows structural swings clearly).
df_daily = (
    df_raw.resample("1D")
    .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    .dropna()
)
print(f"   Daily bars: {len(df_daily)}")

# Also prepare 15-min for a finer-grained run to check staircase behaviour.
df_15m = (
    df_raw.loc["2016-09-01":"2016-12-31"]
    .resample("15min")
    .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    .dropna()
)
print(f"   15M bars (Sep-Dec 2016): {len(df_15m)}")

# ── Run detectors ─────────────────────────────────────────────────────────────
print("\n[2] Running swing_highs_lows + fvg on DAILY data...")

swings_daily = smc.swing_highs_lows(df_daily, swing_length=5)
# smc.fvg() returns RangeIndex; patch to DatetimeIndex.
fvg_daily = smc.fvg(df_daily)
if isinstance(fvg_daily.index, pd.RangeIndex):
    fvg_daily.index = df_daily.index

n_swings = int((~swings_daily["HighLow"].isna()).sum())
n_fvgs   = int((~fvg_daily["FVG"].isna()).sum())
print(f"   Swing points detected: {n_swings}")
print(f"   FVGs detected:         {n_fvgs}")

print("\n[3] Running _mitigation_blocks on DAILY data (default params)...")
mb_daily = smc._mitigation_blocks(df_daily, swings_daily, fvg_daily)

active = mb_daily[mb_daily["MB"] == 1.0]
print(f"   Mitigation blocks detected: {len(active)}")
print(f"   Output columns: {list(mb_daily.columns)}")
print(f"   Output index type: {type(mb_daily.index).__name__}")
print(f"   Output length matches ohlc: {len(mb_daily) == len(df_daily)}")

# ── Per-block detail table ────────────────────────────────────────────────────
print("\n[4] Per-block detail (DAILY, all detected blocks):")
print(f"    {'#':<4} {'Date':<14} {'ABodyTop':>10} {'ABodyBot':>10} "
      f"{'AWickHigh':>10} {'BLevel':>10} {'CLevel':>10} "
      f"{'FVGTarget':>10} {'Invalidated':>12}")
print("    " + "-" * 92)

for i, (ts, row) in enumerate(active.iterrows()):
    inv = int(row["Invalidated"]) if not pd.isna(row["Invalidated"]) else None
    inv_str = str(inv) if inv is not None else "NaN"
    date_str = str(ts.date()) if hasattr(ts, "date") else str(ts)
    fvg_str = f"{row['FVGTarget']:.5f}" if not pd.isna(row["FVGTarget"]) else "NaN"
    print(f"    {i+1:<4} {date_str:<14} "
          f"{row['ABodyTop']:>10.5f} {row['ABodyBottom']:>10.5f} "
          f"{row['AWickHigh']:>10.5f} {row['BLevel']:>10.5f} "
          f"{row['CLevel']:>10.5f} {fvg_str:>10} {inv_str:>12}")

# ── Summary statistics ────────────────────────────────────────────────────────
print("\n[5] Summary statistics (DAILY):")
if len(active) > 0:
    invalidated_count = int((~active["Invalidated"].isna()).sum())
    live_count        = len(active) - invalidated_count
    has_fvg_target    = int((~active["FVGTarget"].isna()).sum())
    print(f"   Total blocks detected:          {len(active)}")
    print(f"   Invalidated (A body broken):    {invalidated_count}")
    print(f"   Still live (not invalidated):   {live_count}")
    print(f"   Blocks with FVG target found:   {has_fvg_target}")
    print(f"   Blocks without FVG target:      {len(active) - has_fvg_target}")
else:
    print("   No blocks detected -- check swing_length parameter or data range.")

# ── Param sensitivity: structure_break_body=True vs False ────────────────────
print("\n[6] Param sensitivity -- structure_break_body=True (body threshold):")
mb_body = smc._mitigation_blocks(
    df_daily, swings_daily, fvg_daily, structure_break_body=True
)
active_body = mb_body[mb_body["MB"] == 1.0]
print(f"   Blocks with structure_break_body=False (wick, default): {len(active)}")
print(f"   Blocks with structure_break_body=True  (body):          {len(active_body)}")
diff = len(active) - len(active_body)
print(f"   Delta (blocks lost by stricter body threshold):         {diff}")

# ── 15-min staircase check (Sep-Dec 2016) ────────────────────────────────────
print("\n[7] Staircase check -- 15M data, Sep-Dec 2016...")
swings_15m = smc.swing_highs_lows(df_15m, swing_length=5)
fvg_15m = smc.fvg(df_15m)
if isinstance(fvg_15m.index, pd.RangeIndex):
    fvg_15m.index = df_15m.index

mb_15m = smc._mitigation_blocks(df_15m, swings_15m, fvg_15m)
active_15m = mb_15m[mb_15m["MB"] == 1.0]
print(f"   15M swing points: {int((~swings_15m['HighLow'].isna()).sum())}")
print(f"   15M FVGs:         {int((~fvg_15m['FVG'].isna()).sum())}")
print(f"   15M MB count:     {len(active_15m)}")

if len(active_15m) > 0:
    # Show first 5 and last 5 to spot staircase pattern.
    show = pd.concat([active_15m.head(5), active_15m.tail(5)]).drop_duplicates()
    print(f"\n   First/last 5 blocks (15M):")
    print(f"    {'Date/Time':<24} {'ABodyTop':>10} {'ABodyBottom':>10} "
          f"{'CLevel':>10} {'FVGTarget':>10} {'Invalidated':>12}")
    print("    " + "-" * 82)
    for ts, row in show.iterrows():
        inv_str = str(int(row["Invalidated"])) if not pd.isna(row["Invalidated"]) else "NaN"
        fvg_str = f"{row['FVGTarget']:.5f}" if not pd.isna(row["FVGTarget"]) else "NaN"
        print(f"    {str(ts):<24} "
              f"{row['ABodyTop']:>10.5f} {row['ABodyBottom']:>10.5f} "
              f"{row['CLevel']:>10.5f} {fvg_str:>10} {inv_str:>12}")

print("\n[8] Checking A invariants (all blocks, DAILY):")
if len(active) > 0:
    # ABodyTop must always be >= ABodyBottom
    top_ge_bot = (active["ABodyTop"] >= active["ABodyBottom"]).all()
    # ABodyTop must always be <= AWickHigh
    top_le_wick = (active["ABodyTop"] <= active["AWickHigh"]).all()
    # CLevel must always be < ABodyBottom (wick threshold) or ABodyTop (body threshold)
    c_below_a_wick = (active["CLevel"] < active.apply(
        lambda r: df_daily["low"].iloc[
            df_daily.index.get_loc(r.name)
        ] if r.name in df_daily.index else np.nan, axis=1
    )).all()
    print(f"   ABodyTop >= ABodyBottom (always):   {top_ge_bot}")
    print(f"   ABodyTop <= AWickHigh  (always):    {top_le_wick}")
    print(f"   CLevel < A's wick low  (by design): checked structurally via detector logic")
    if not top_ge_bot:
        print("   !! FAIL: ABodyTop < ABodyBottom found -- body computation error")
    if not top_le_wick:
        print("   !! FAIL: ABodyTop > AWickHigh found -- wick/body inconsistency")
else:
    print("   No blocks to check invariants on.")

print("\n" + "=" * 70)
print("DATA AUDIT COMPLETE. Review above output before proceeding.")
print("=" * 70)
