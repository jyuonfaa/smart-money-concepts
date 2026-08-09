import re
import datetime

with open('cslim/project_forensics.md', 'r', encoding='utf-8') as f:
    text = f.read()

new_content = """## 1. VIDEO STATUS UPDATES

**Month 3, Video 2** — status: LOCKED (this session)
- Fixed: smc.liquidity() sweep detection was wick-based (ohlc_high/ohlc_low), contradicting M3V2's explicit notes instruction ("PRICE GOES THROUGH THE BODIES OF THE CANDLES... NOT THE WICKS"). Changed to close-based (ohlc_close) for both bullish and bearish sweep conditions.
- Verified: verify_month3_video2.py now passes both synthetic tests cleanly (Swept=6, close-based). Blast radius checked — only live downstream consumer is _smt_divergence's smt_at_liquidity, confirmed unaffected (0 True rows before and after, on 2016 AUDUSD daily). Golden Master reconfirmed unchanged (HRR=471, LRR=37, 11 transitions).
- Correction: master context previously mislabeled this function's origin as "Month 2, Video 3" — corrected to Month 3, Video 2 ("Institutional Order Flow - What Makes It Easy To Know").

**Month 4, Video 1** — status: LOCKED (this session)
- Verified correct and notes-sourced: triad composition (ZB/ZN/ZF), one-of-three-legs failure swing logic ("you just need one to break that pattern," page 263), directional labeling, neutral-tolerance concept, POI gate (confirmed genuinely functional via direct rejection test, not dead code).
- Visual Audit completed: POI zone rendering bugs found and fixed (wall-to-wall anchoring, corrupted date range from index-loss defect — see Tier 4 below). Single-leg case (2016-05-03) verified via exact internal computation path: DXY made lower low, ZB failed to confirm (flagged correctly), ZN/ZF confirmed normally (correctly not flagged).
- Golden Master reconfirmed unchanged after all M4V1 work.
- Caveat, not blocking: MODE 3 ("Chained SMT") in verify_month4_video1.py is NOT part of the certified build — pulls in Month 3 Video 5 logic with no textual basis in M4V1's own notes (page 261-270 searched specifically, no SMT-chaining reference found). Left in place as exploratory code, not counted as verified.
- Caveat, not blocking: ICT demonstrated this on 90-minute charts (pages 265-266); current testing uses Daily data as an acknowledged approximation.

**Month 3, Video 8** — status: NOT LOCKED (provisionally unblocked only)
- Fixed and verified: POI dead-code bug in _hns_signals (poi_t/poi_b fetched but never compared) — now correctly checks poi_b <= trigger_price <= poi_t. Sourced from M3V8's own notes ("we traded down into it," page 258).
- Known limitation, NOT fixed: bearish-signal validation currently reuses a stale bullish order block instead of a genuine breaker zone. M3V8's own notes require a breaker for the bearish case specifically ("we're inside of a breaker and that's a bearish environment," page 258). Blocked on Tier 2 breaker_blocks() below.
- Declined by explicit decision: body-close confirmation on the neckline sweep trigger (wick-only currently) — not sourced from M3V8's own notes; the general project-wide body-close principle was judged out of scope for this video specifically.
- Correction: master context's "Video 1: Breakers" label is wrong — Month 3 Video 1's real title is "Timeframe Selection & Defining Setups"; breaker content appears within it but isn't the video's subject.

## 2. KNOWN CORE LIBRARY DEFICIENCIES (new section, four tiers)

TIER 1 — Never built, no code exists anywhere in repo history:
- smc.macro_swing_grading()
- smc.measured_moves()
- smc.monthly_range_ob()

TIER 2 — Real implementation exists but orphaned/unmerged/unverified:
- smc.breaker_blocks() — in scratch_breaker.py, runs cleanly, NOT verified against its canonical source (Month 4 Video 5), deliberately held pending that video
- smc.ny_midnight_open() — in append_to_smc.py, never reviewed against notes at all

TIER 3 — Hallucinated, never existed, do not attempt to locate:
- smc.sequence_void() / smc.void_scanner() — confirmed via git log -S across full history, zero results ever

TIER 4 — Existing function with a confirmed defect:
- smc.ob() — missing 'MeanThreshold' output column (KeyError in verify_mean_threshold.py)
- smc.ob() / smc.fvg() / smc.liquidity() — all three silently return integer RangeIndex instead of preserving the original DatetimeIndex. Worked around ad hoc in state_machine.py (lockstep .iloc), verify_step2.py (manual hot-patch), generate_gif.py (manual remapping). NOT fixed at source — deliberately deferred, high ripple risk. Warning comments added directly above each function in smc.py this session.

## 3. VERIFY SCRIPT INTEGRITY

- verify_month3_video2.py — confirmed clean, no exit-code gap remaining.
- audit_month3_video1.py — sys.exit(1) added when fail count > 0 (previously exited 0 despite 4 failed checks).
- verify_month3_video1.py — still crashes on smc.macro_swing_grading() before completion (Tier 1 gap, unresolved).
- verify_month3_video5.py — cosmetic UnicodeEncodeError on '<-' character fixed (replaced with ASCII '->'). No logic changed.
- Confirmed NOT silent-fail (crash outright instead, safer failure mode): verify_mean_threshold.py, verify_month2_video8.py, verify_month3_video3.py.

## 4. HOUSEKEEPING
- Session diagnostic scripts moved to cslim/diagnostics/: diag_smt_at_liquidity_baseline.py, diag_triad_pois.py, run_audit.py, temp_zoom.py, visualize_month4_video1_zoomed.py (this last one has a known unfixed bug — shared_xaxes binding prevents xaxis_range override — left broken intentionally, not a functioning tool).

"""

# Remove old Section 1.
text = re.sub(r'## 1\. VIDEO-BY-VIDEO STATUS.*?(?=## 2\. FULL FUNCTION INVENTORY)', '', text, flags=re.DOTALL)

# Bump the numbering of the remaining sections:
for old, new in [(9, 12), (8, 11), (7, 10), (6, 9), (5, 8), (4, 7), (3, 6), (2, 5)]:
    text = text.replace(f'## {old}.', f'## {new}.')

# Add the new content right after '# Project Forensics\n' or '# Project Forensics\r\n'
text = re.sub(r'(# Project Forensics\r?\n)', r'\1\n' + new_content + '\n', text)

# Append footer date if not exists or replace it
today = datetime.datetime.now().strftime('%Y-%m-%d')
footer = f'---\n*Last Updated: {today}*'
if '*Last Updated:*' in text or '*Last Updated:' in text:
    text = re.sub(r'---\r?\n\*Last Updated:.*?(\*|$)', footer, text)
else:
    text += f'\n\n{footer}\n'

with open('cslim/project_forensics.md', 'w', encoding='utf-8') as f:
    f.write(text)
