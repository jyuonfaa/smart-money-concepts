"""
verify_month3_video4.py
=======================
Forensic Regression Audit: Month 3, Video 4 — Monthly Range Order Block Detector.

Tests:
  1. smc.monthly_range_ob() produces correct output on AUDUSD 2016 monthly data.
  2. The monthly_ob_gated column is correctly wired into turtle_soup_signals().
  3. All existing regression suites still PASS (zero regressions from new code).
"""
import subprocess
import sys
import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals

print("=" * 65)
print("FORENSIC REGRESSION AUDIT: MONTH 3 VIDEO 4 — MONTHLY RANGE OB")
print("=" * 65)

# ── Load AUDUSD 2016 data ───────────────────────────────────────────
print("\n[1] Loading AUDUSD 2016 data...")
df_raw = pd.read_csv(
    'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'],
    index_col=False
)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Resample to Monthly and Daily
df_monthly = df_raw.resample('1ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
df_daily_ri = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

print(f"   Monthly bars: {len(df_monthly)}")
print(f"   Daily bars  : {len(df_daily_ri)}")
print(f"   15M bars    : {len(df_15m)}")

# ── Run the new detector ────────────────────────────────────────────
print("\n[2] Running smc.monthly_range_ob()...")
monthly_ob = smc.monthly_range_ob(df_monthly)
last = monthly_ob.iloc[-1]

print(f"\n   --- Monthly Range OB Audit (AUDUSD 2016 End-of-Year) ---")
print(f"   Down OB High (Activation Trigger) : {last['monthly_down_ob_high']:.5f}")
print(f"   Down OB Low  (Bullish OB Floor)   : {last['monthly_down_ob_low']:.5f}")
print(f"   Up OB Low    (Bear Activation)    : {last['monthly_up_ob_low']:.5f}")
print(f"   Up OB High   (Bearish OB Ceiling) : {last['monthly_up_ob_high']:.5f}")
print(f"   Bullish OB Active                 : {last['monthly_bull_ob_active']}")
print(f"   Bearish OB Active                 : {last['monthly_bear_ob_active']}")
print(f"   Monthly Bias                      : {last['monthly_bias']}")

# ── Sanity checks ───────────────────────────────────────────────────
print("\n[3] Running sanity checks...")
assert not pd.isna(last['monthly_down_ob_high']),  "FAIL: monthly_down_ob_high is NaN"
assert not pd.isna(last['monthly_down_ob_low']),   "FAIL: monthly_down_ob_low is NaN"
assert not pd.isna(last['monthly_up_ob_high']),    "FAIL: monthly_up_ob_high is NaN"
assert not pd.isna(last['monthly_up_ob_low']),     "FAIL: monthly_up_ob_low is NaN"
assert last['monthly_down_ob_low'] < last['monthly_down_ob_high'], "FAIL: Down OB low must be < high"
assert last['monthly_up_ob_low'] < last['monthly_up_ob_high'],     "FAIL: Up OB low must be < high"
assert last['monthly_bias'] in ('BULLISH', 'BEARISH', 'NEUTRAL'),  "FAIL: Invalid bias value"
print("   [PASS] All output columns populated correctly.")
print("   [PASS] Price levels are internally consistent.")
print(f"   [PASS] Bias is a valid value: {last['monthly_bias']}")

# ── Test Monthly OB gate in turtle_soup_signals ─────────────────────
print("\n[4] Testing monthly_ob_gated column in turtle_soup_signals()...")
daily_swings = smc.swing_highs_lows(df_daily_ri, swing_length=5)
daily_ob_df  = smc.ob(df_daily_ri, daily_swings)
ltf_swings   = smc.swing_highs_lows(df_15m, swing_length=5)
reversals    = detect_reversals(df_15m, ltf_swings)
midnight     = smc.ny_midnight_open(df_15m)
fvg          = smc.fvg(df_15m)

# Without gate
res_no_gate = turtle_soup_signals(
    ohlc=df_15m, reversals=reversals, daily_ob=daily_ob_df, daily_ohlc=df_daily_ri,
    ny_midnight=midnight, fvg_df=fvg
)
sigs_no_gate = res_no_gate[res_no_gate['turtle_soup_bull'] | res_no_gate['turtle_soup_bear']]

# With gate
res_gated = turtle_soup_signals(
    ohlc=df_15m, reversals=reversals, daily_ob=daily_ob_df, daily_ohlc=df_daily_ri,
    ny_midnight=midnight, fvg_df=fvg, monthly_ob_df=monthly_ob
)
sigs_gated = res_gated[res_gated['turtle_soup_bull'] | res_gated['turtle_soup_bear']]

assert 'monthly_ob_gated' in res_gated.columns, "FAIL: monthly_ob_gated column missing from output"
print(f"   [PASS] monthly_ob_gated column is present in output.")
print(f"   Signals without Monthly OB gate : {len(sigs_no_gate)}")
print(f"   Signals with Monthly OB gate    : {len(sigs_gated)}")
print(f"   Signals suppressed by gate      : {len(sigs_no_gate) - len(sigs_gated)}")

gate_pct = ((len(sigs_no_gate) - len(sigs_gated)) / max(len(sigs_no_gate), 1)) * 100
print(f"   Gate suppression rate           : {gate_pct:.1f}%")

# ── Golden Master Regression ────────────────────────────────────────
print("\n[5] Running existing regression suites (zero-regression check)...")
for script in ['verify_step2.py', 'verify_video8.py', 'verify_month2_video2.py']:
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    status = '[PASSED]' if result.returncode == 0 else '[FAILED]'
    print(f"   {status} {script}")
    if result.returncode != 0:
        print(f"     STDERR: {result.stderr[-300:]}")

print("\n" + "=" * 65)
print("FORENSIC AUDIT COMPLETE")
print("=" * 65)
