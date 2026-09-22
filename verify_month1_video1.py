"""
verify_month1_video1.py - M1V1 (Elements To A Trade Setup) conformance checks on SYNTHETIC fixtures.

Each fixture is built from what M1V1's text and slides describe, so no external data is needed.
Print-only: writes no files. Each check is labelled EXPECT-PASS or EXPECT-FAIL (a documented, known
conflict between the code and M1V1). Exit code 1 only if a result is UNEXPECTED (an EXPECT-PASS check
fails, or an EXPECT-FAIL check passes - which would mean our reading of the code is wrong).
OBSERVE checks print values and never affect the exit code.
"""
import sys
import numpy as np
import pandas as pd
from smartmoneyconcepts import smc as _smc
smc = getattr(_smc, "smc", _smc)  # package exports the class; fall back to the module's class
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine

RESULTS = []  # (id, expectation, passed, detail)


def record(cid, expectation, passed, detail):
    RESULTS.append((cid, expectation, bool(passed), detail))


def frame(o, h, l, c, start="2016-01-04", freq="1h"):
    idx = pd.date_range(start, periods=len(o), freq=freq)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 0.0}, index=idx)


# ---------------------------------------------------------------- C1 / C2: range bounded by BODIES
def flat_range(n=80, spike_at=None):
    o, h, l, c = [], [], [], []
    for i in range(n):
        up = (i % 2 == 0)
        op, cl = (100.30, 100.70) if up else (100.70, 100.30)
        hi, lo = max(op, cl) + 0.10, min(op, cl) - 0.10      # wicks poke 0.10 beyond the bodies
        if spike_at is not None and i == spike_at:
            hi, lo = 101.50, 100.30                          # one long upper wick; body unchanged
        o.append(op); h.append(hi); l.append(lo); c.append(cl)
    return frame(o, h, l, c)


df = flat_range()
cons = smc.consolidation(df, prd=10, conslen=5)
boxed = cons[cons["Consolidation"] == 1.0]
if boxed.empty:
    record("C1", "EXPECT-PASS", False, "no consolidation box produced on a flat body-range fixture")
else:
    last = boxed.iloc[-1]
    ok = (abs(last["Top"] - 100.70) < 1e-9 and abs(last["Bottom"] - 100.30) < 1e-9
          and abs(last["Equilibrium"] - 100.50) < 1e-9)
    record("C1", "EXPECT-PASS", ok,
           f"Top={last['Top']:.4f} Bottom={last['Bottom']:.4f} Eq={last['Equilibrium']:.4f} "
           f"(bodies 100.30-100.70, wicks 100.20-100.80; expect 100.70 / 100.30 / 100.50)")

SPIKE = 50
dfs = flat_range(spike_at=SPIKE)
cons_s = smc.consolidation(dfs, prd=10, conslen=5)
window = cons_s["Consolidation"].iloc[SPIKE - 1: SPIKE + 4]
still_boxed = bool(window.notna().all())
record("C2", "EXPECT-FAIL", still_boxed,
       f"V1 p.6: range is defined by bodies, so a wick-only spike (body unchanged) should not end the box. "
       f"Consolidation flags bars {SPIKE - 1}..{SPIKE + 3}: {window.notna().astype(int).tolist()} (1 = still boxed)")


# ---------------------------------------------------------------- C3 / C4: expansion OB near/at equilibrium
def expansion_fixture(ob_open, ob_high, ob_low, ob_close, eq_at_break=True):
    top, bot = 1.2891, 1.2864
    eq = (top + bot) / 2.0                                   # 1.28775
    o, h, l, c = [], [], [], []
    for i in range(22):                                      # all-bullish fillers inside the box
        op = 1.2866 + (i % 5) * 0.0004
        o.append(op); c.append(op + 0.0003); h.append(op + 0.0005); l.append(op - 0.0002)
    o.append(ob_open); h.append(ob_high); l.append(ob_low); c.append(ob_close)    # bar 22: the OB candle
    o.append(1.28775); h.append(1.28800); l.append(1.28770); c.append(1.28790)    # bar 23: small up candle
    o.append(1.28790); h.append(1.29000); l.append(1.28780); c.append(1.28980)    # bar 24: breakout close > top
    d = frame(o, h, l, c)
    cs = pd.DataFrame({"Consolidation": 1.0, "Top": top, "Bottom": bot, "Equilibrium": eq,
                       "OTE_High": np.nan, "OTE_Low": np.nan, "BreakLong": np.nan, "BreakShort": np.nan},
                      index=d.index)
    if not eq_at_break:
        cs.iloc[24, cs.columns.get_loc("Equilibrium")] = np.nan
        cs.iloc[24, cs.columns.get_loc("Consolidation")] = np.nan
    return d, cs


# V1 p.3 shape: down candle whose CLOSE sits on equilibrium (1.28775) and whose OPEN is ~6 pips above it
d3, c3 = expansion_fixture(1.28833, 1.28845, 1.28765, 1.28775)
e3 = smc.expansion(d3, c3)
found = not np.isnan(e3["OB_Top"].iloc[24])
same = found and abs(e3["OB_Top"].iloc[24] - 1.28845) < 1e-9 and abs(e3["OB_Bottom"].iloc[24] - 1.28765) < 1e-9
record("C3", "EXPECT-FAIL", same,
       f"V1 p.3: the OB is the down candle right before the up move, near or at equilibrium. "
       f"Expansion[24]={e3['Expansion'].iloc[24]}, OB_Top={e3['OB_Top'].iloc[24]}, OB_Bottom={e3['OB_Bottom'].iloc[24]} "
       f"(V1-shaped candle 22: high 1.28845, low 1.28765, eq 1.28775)")

# OBSERVE: a candle entirely below equilibrium is accepted; and the same case when the box clears on the breakout bar
d4, c4a = expansion_fixture(1.28760, 1.28770, 1.28690, 1.28700, eq_at_break=True)
e4a = smc.expansion(d4, c4a)
d4, c4b = expansion_fixture(1.28760, 1.28770, 1.28690, 1.28700, eq_at_break=False)
e4b = smc.expansion(d4, c4b)
print(f"[OBSERVE C4a] discount OB (high <= eq), box present on breakout bar: OB_Top={e4a['OB_Top'].iloc[24]} "
      f"OB_Bottom={e4a['OB_Bottom'].iloc[24]}")
print(f"[OBSERVE C4b] same candle, box cleared on the breakout bar (Equilibrium NaN at i): "
      f"Expansion={e4b['Expansion'].iloc[24]} OB_Top={e4b['OB_Top'].iloc[24]} (NaN = OB skipped)")

# ---------------------------------------------------------------- C5: four conditions, exactly one at a time
sm = PriceDeliveryStateMachine()
exp_df = pd.DataFrame({"Expansion": e4b["Expansion"].values}, index=d4.index)
audit = sm.process(ohlc=d4, consolidation=c4b, expansion=exp_df)      # box on bars 0-23, expansion on bar 24
states = set(audit["State"].unique())
four = {"consolidation", "expansion", "retracement", "reversal"}
record("C5", "EXPECT-FAIL", four.issubset(states),
       f"V1 pp.1-3: price is always in exactly one of four conditions. process() produced {sorted(states)} "
       f"(RETRACEMENT and REVERSAL are never assigned)")

# ---------------------------------------------------------------- C6: V1 p.5 reversal with multi-candle closes beyond
n = 45
o = [0.9880] * n; h = [0.9890] * n; l = [0.9870] * n; c = [0.9880] * n
h[10] = 0.9910; c[10] = 0.9895; o[10] = 0.9885             # old swing high, level 0.9910
for i, (op, hi, lo, cl) in zip(range(30, 36), [(0.9880, 0.9930, 0.9878, 0.9925), (0.9925, 0.9935, 0.9918, 0.9930),
                                              (0.9930, 0.9942, 0.9922, 0.9928), (0.9928, 0.9945, 0.9920, 0.9940),
                                              (0.9940, 0.9950, 0.9930, 0.9935), (0.9935, 0.9948, 0.9925, 0.9932)]):
    o[i], h[i], l[i], c[i] = op, hi, lo, cl                  # six candles with CLOSES above 0.9910
o[36], h[36], l[36], c[36] = 0.9932, 0.9940, 0.9890, 0.9895   # big black candle back below the level
d6 = frame(o, h, l, c)
shl = pd.DataFrame({"HighLow": np.full(n, np.nan), "Level": np.full(n, np.nan)}, index=d6.index)
shl.iloc[10, 0] = 1.0; shl.iloc[10, 1] = 0.9910
rev = detect_reversals(d6, shl)
flagged = rev["Reversal"].iloc[30:41].notna().any()
record("C6", "EXPECT-FAIL", flagged,
       f"V1 p.5 slide: price spends several candles beyond the old high, then reverses. "
       f"Reversal flags in bars 30..40: {rev['Reversal'].iloc[30:41].dropna().tolist()}")

# ---------------------------------------------------------------- report
print("\nM1V1 CONFORMANCE CHECKS (synthetic fixtures)")
unexpected = 0
for cid, exp, passed, detail in RESULTS:
    result = "PASS" if passed else "FAIL"
    ok = (exp == "EXPECT-PASS" and passed) or (exp == "EXPECT-FAIL" and not passed)
    if not ok:
        unexpected += 1
    print(f"{cid} | {exp} | {result} | {'as expected' if ok else 'UNEXPECTED'} | {detail}")
print(f"\nUnexpected results: {unexpected}")
sys.exit(1 if unexpected else 0)
