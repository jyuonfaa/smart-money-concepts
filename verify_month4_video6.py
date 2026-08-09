"""
verify_month4_video6.py
Month 4, Video 6 — Rejection Blocks verification script.
Runs on AUDUSD 2016 Daily and 15M; prints per-block detail, summary stats,
and structural invariant checks.
"""
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')

# Import _rejection_blocks by running the impl module (wires smc._rejection_blocks)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rb_impl",
    r"C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3\scratch\rb_impl.py"
)
rb_mod = importlib.util.load_from_spec(spec) if hasattr(importlib.util, 'load_from_spec') else None

from smartmoneyconcepts.smc import smc

# Ensure _rejection_blocks is available — it was appended to smc.py as a module-level
# function and wired via smc._rejection_blocks = staticmethod(_rejection_blocks).
# If not yet present (e.g. first run before append), exec the impl file.
import os as _os
if not hasattr(smc, '_rejection_blocks'):
    _impl_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3\scratch\rb_impl.py'
    with open(_impl_path, 'r', encoding='utf-8') as _f:
        exec(compile(_f.read(), _impl_path, 'exec'), globals())


# ─── Load AUDUSD 2016 1M → resample ──────────────────────────────────────────
CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'

print("Loading AUDUSD 2016 1M data...")
df_raw = pd.read_csv(CSV_PATH, sep=';',
                     names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

print("Resampling to Daily...")
daily = df_raw.resample('D').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

print("Resampling to 15M...")
m15 = df_raw.resample('15Min').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()


def run_verification(ohlc, label, swing_length=5):
    print(f"\n{'='*70}")
    print(f"  {label}  (rows={len(ohlc)}, swing_length={swing_length})")
    print(f"{'='*70}")

    print(f"  DatetimeIndex dtype: {ohlc.index.dtype}")

    swings = smc.swing_highs_lows(ohlc, swing_length=swing_length)
    rbs    = smc._rejection_blocks(ohlc, swings)

    detected = rbs[rbs['RB'].notna()].copy()
    bearish  = detected[detected['RB'] == -1]
    bullish  = detected[detected['RB'] ==  1]

    # ── Per-block detail table ─────────────────────────────────────────────
    print(f"\n  PER-BLOCK DETAIL ({len(detected)} total blocks):")
    print(f"  {'Date':<22} {'Dir':>5} {'RBTop':>10} {'RBBottom':>10} "
          f"{'RBWickLevel':>12} {'RBBodyLevel':>12} {'Invalidated':<24}")
    print(f"  {'-'*22} {'-'*5} {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*24}")

    for idx, row in detected.iterrows():
        direction = "BEAR" if row['RB'] == -1 else "BULL"
        inv_str   = str(row['Invalidated'])[:19] if pd.notna(row['Invalidated']) else "live"
        print(f"  {str(idx)[:22]:<22} {direction:>5} "
              f"{row['RBTop']:>10.5f} {row['RBBottom']:>10.5f} "
              f"{row['RBWickLevel']:>12.5f} {row['RBBodyLevel']:>12.5f} "
              f"{inv_str:<24}")

    # ── Summary stats ──────────────────────────────────────────────────────
    n_inv_bear = bearish['Invalidated'].notna().sum()
    n_inv_bull = bullish['Invalidated'].notna().sum()
    print(f"\n  SUMMARY:")
    print(f"    Bearish RBs : {len(bearish):>4}  |  invalidated: {n_inv_bear}  live: {len(bearish)-n_inv_bear}")
    print(f"    Bullish RBs : {len(bullish):>4}  |  invalidated: {n_inv_bull}  live: {len(bullish)-n_inv_bull}")
    print(f"    Total       : {len(detected):>4}  |  invalidated: {n_inv_bear+n_inv_bull}  live: {len(detected)-n_inv_bear-n_inv_bull}")

    # ── Structural invariant checks ────────────────────────────────────────
    print(f"\n  INVARIANT CHECKS:")
    fails = 0

    # 1. RBTop >= RBBottom always
    bad_bounds = detected[detected['RBTop'] < detected['RBBottom']]
    if bad_bounds.empty:
        print(f"    [PASS] RBTop >= RBBottom for all {len(detected)} blocks")
    else:
        print(f"    [FAIL] RBTop < RBBottom in {len(bad_bounds)} blocks:")
        print(bad_bounds[['RBTop','RBBottom']].to_string())
        fails += len(bad_bounds)

    # 2. Bearish blocks: RBWickLevel == RBTop, RBBodyLevel == RBBottom
    bad_bear_wick = bearish[bearish['RBWickLevel'] != bearish['RBTop']]
    bad_bear_body = bearish[bearish['RBBodyLevel'] != bearish['RBBottom']]
    if bad_bear_wick.empty and bad_bear_body.empty:
        print(f"    [PASS] All {len(bearish)} bearish blocks: WickLevel==RBTop, BodyLevel==RBBottom")
    else:
        print(f"    [FAIL] {len(bad_bear_wick)} bearish WickLevel!=RBTop, {len(bad_bear_body)} BodyLevel!=RBBottom")
        fails += len(bad_bear_wick) + len(bad_bear_body)

    # 3. Bullish blocks: RBWickLevel == RBBottom, RBBodyLevel == RBTop
    bad_bull_wick = bullish[bullish['RBWickLevel'] != bullish['RBBottom']]
    bad_bull_body = bullish[bullish['RBBodyLevel'] != bullish['RBTop']]
    if bad_bull_wick.empty and bad_bull_body.empty:
        print(f"    [PASS] All {len(bullish)} bullish blocks: WickLevel==RBBottom, BodyLevel==RBTop")
    else:
        print(f"    [FAIL] {len(bad_bull_wick)} bullish WickLevel!=RBBottom, {len(bad_bull_body)} BodyLevel!=RBTop")
        fails += len(bad_bull_wick) + len(bad_bull_body)

    # 4. No NaN in RBTop/RBBottom/RBWickLevel/RBBodyLevel for detected rows
    for col in ['RBTop','RBBottom','RBWickLevel','RBBodyLevel']:
        n_nan = detected[col].isna().sum()
        if n_nan == 0:
            print(f"    [PASS] No NaN in {col} for detected rows")
        else:
            print(f"    [FAIL] {n_nan} NaN values in {col}")
            fails += n_nan

    if fails == 0:
        print(f"\n    All invariants PASSED.")
    else:
        print(f"\n    {fails} invariant failure(s) total.")


# ── Run both timeframes ────────────────────────────────────────────────────────
run_verification(daily, "AUDUSD 2016 DAILY", swing_length=5)
run_verification(m15,   "AUDUSD 2016 15M",   swing_length=5)

print("\n\nDone.")
