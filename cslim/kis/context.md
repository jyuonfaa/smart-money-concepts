# ICT Intelligence Suite — Project Context

## 1. Project Description
A production-ready institutional trading suite designed to encode the ICT Mentorship 2016 curriculum. The suite focuses on identifying Institutional Transposition (Premium/Discount) and Surgical Execution on the 15M timeframe.

## 2. Current Architecture
- **Multi-Timeframe Fractal Engine:** Daily (Anchor) -> 4H (Interbank) -> 15M (Surgical).
- **Institutional Logic:** Smarts Money Concepts (SMC) integration for swing detection.
- **Verification Layer:** "Institutional Sequence Audit" for perfect H-L-H signal alternation.
- **Visuals:** Plotly-based triple-pane dashboards with absolute coordinate anchoring and zero ghost panes.

## 3. Implemented Modules
### Video 1-3 — Foundational State: ✅ COMPLETE
- NY Timezone normalization.
- Power of 3 (Accumulation/Manipulation/Distribution) logic.
- Liquidity Pool identification.

### Video 4 — Equilibrium vs Discount: ✅ COMPLETE
- Automated institutional logic for Bullish OTE.
- Verified signal alternation logic and 8-candle cooldown.

### Video 5 — Equilibrium vs Premium: ✅ COMPLETE
- Mirror of Video 4 for bearish setups.
- Draw on Liquidity targets absolutely anchored to `conf_ts`.

### Video 6 — Institutional Suite (High-Precision Validation): ✅ COMPLETE
- [x] HTF institutional signatures (OBs, FVGs, Voids) with `conf_ts` anchoring.
- [x] 3-pane forensic dashboard (15M, 4H, Daily) with zero ghost panes.
- [x] MTF confluence scoring (SENIOR labels) with temporal deduplication.
- [x] Audited against EURUSD/AUDUSD historical accumulation cases.

### Video 7 — Sovereign Liquidity Engine: ✅ COMPLETE
- [x] Macro-level state machine anchoring LRR/HRR classification to structural boundaries.
- [x] Draw on Liquidity target persistence (locked until mitigated by a true price close).
- [x] Pure historical price-space obstruction counter isolating "Hot Knife Through Butter" environments.
- [x] Institutional 8-candle hysteresis to filter intraday noise into genuine macro shifts.
- [x] 15M Golden Master visualization mapping 1:1 transitions with decoupled label staggering.

### Video 8 — Market Protraction (Temporal Manipulation): ✅ COMPLETE
- [x] Time-sensitive daily clock anchors (20:00, 00:00, 07:00 NY) detecting temporal manipulation swings.
- [x] Standalone mathematical detector classmethod `smc.market_protraction()` returning pure temporal swings with zero conflated logic.
- [x] High-fidelity visualization dashboard `visualize_video8.py` projecting precise color-coded dashed anchor lines and annotated arrows.
- [x] Automated regression suite `verify_video8.py` confirming 100% accurate UTC-NY timezone conversion.
- [x] Forensic UTC anchor verification completed and locked (see table below).

#### Confirmed UTC Anchor Hours (Forensically Verified — EDT/Summer Data)
| Anchor | UTC Firing Hour | NY Time (EDT) | ICT Target | Status |
|---|---|---|---|---|
| `ASIA` | `00:00 UTC` | `20:00 NY` | 8:00 PM NY (Asia Open) | ✅ Correct |
| `MIDNIGHT` | `04:00 UTC` | `00:00 NY` | 12:00 AM NY (Midnight) | ✅ Correct |
| `NY_OPEN` | `11:00 UTC` | `07:00 NY` | 7:00 AM NY (NY Open) | ✅ Correct |

> **Implementation Note:** In winter (EST), `ASIA` will fire at `01:00 UTC` instead of `00:00 UTC`. The `pytz America/New_York` timezone in `market_protraction()` handles this automatically via DST-aware conversion — no code change required.

### Month 2, Video 1 — Growing Small Accounts: ✅ COMPLETE
- [x] Turtle Soup entry logic (break below old low into daily OB) with entry zone body logic (open to high for bull, low to open for bear).
- [x] Pre-entry structural target mapping using equal high/low clusters (`ts_target_near` and `ts_target_far`).
- [x] Complete institutional risk engine `risk_engine.py` with 5-stage exit schedule, 20-pip minimum swing filter, and midpoint OB body stops.
- [x] Precise dual-pane Plotly visualization dashboard `visualize_month2_video1.py` with 48h temporal label spacing.

### Month 2, Video 2 — Framing Low-Risk Trade Setups: ✅ COMPLETE
- [x] Multi-Timeframe stop-loss refinement (1H anchor stop vs 15M/5M refined daily OB bottom stops).
- [x] Implemented `use_daily_ob_stop` parameter in `turtle_soup_signals` to dynamically bind stops to the `Bottom` column of daily OB.
- [x] Added `refinement_level` tracking column to enable multi-timeframe state machine audits.
- [x] Three-pane Plotly dashboard `visualize_month2_video2.py` mapping 1H, 15M, and 5M candlestick charts with direction-correct R-projections.
- [x] Standalone verification suite `verify_month2_video2.py` running Golden Master regression + dynamic stop distance audits.

### Month 3, Video 4 — Anticipatory Skill Development: ✅ COMPLETE
- [x] Implemented Monthly Range institutional anchor (`smc.monthly_range_ob()`) identifying most recent down/up candle pairs.
- [x] Encoded exact OB activation triggers (trading through the high/low of the range candles).
- [x] Implemented hard gate (`monthly_ob_gated`) in `turtle_soup_signals()` to suppress setups forming outside active Monthly OB zones.
- [x] Built precise dual-pane visualization dashboard `visualize_month3_video4.py` mapping Monthly boundaries directly onto the Daily chart.
- [x] Standalone verification suite `verify_month3_video4.py` running automated audits against AUDUSD end-of-year structure.

## 4. Detector Registry
| Function | Video | Purpose | Output Columns |
|---|---|---|---|
| `smc.swing_highs_lows_v4()` | V4 | 4-candle confirmed swing H/L with strict alternation | `ts, conf_ts, type, p` |
| `smc.identify_order_block()` | V4 | Last opposing candle before confirmed swing | `ts, conf_ts, type, high, low` |
| `smc.consolidation()` | V3/V6 | ZigZag pivot consolidation zones with OTE levels | `Consolidation, Top, Bottom, Equilibrium, OTE_High, OTE_Low, BreakLong, BreakShort` |
| `smc.expansion()` | V6 | Body close beyond confirmed consolidation boundary | `Expansion, OB_Top, OB_Bottom` |
| `smc.displacement()` | V6 | Statistical top-decile candle speed/size detector | `Displacement, Range_90p, BodyRatio_80p` |
| `smc.calculate_path_obstruction()` | V7 | Pivot count between current price and target | `int` (count) |
| `smc.market_protraction()` | V8 | Temporal manipulation swings at 3 daily clock anchors | `protraction_anchor, protraction_dir, protraction_mag` |
| `smc.monthly_range_ob()` | M3V4 | Institutional Monthly Range anchor and activation check | `monthly_down_ob_low, monthly_up_ob_high, monthly_bias` |

## 5. Key File Structure
| File | Purpose |
|---|---|
| `smartmoneyconcepts/smc.py` | Single source of all detector classmethods |
| `smartmoneyconcepts/state_machine.py` | Core transition engine: detect_reversals(), turtle_soup_signals() |
| `risk_engine.py` | Capital risk & exits scheduling engine |
| `verify_audusd_sept.py` | Regression audit & verification script |
| `verify_mean_threshold.py` | Regression audit & verification script |
| `verify_month2_video2.py` | Regression audit & verification script |
| `verify_month2_video3.py` | Regression audit & verification script |
| `verify_month2_video4.py` | Regression audit & verification script |
| `verify_month2_video5.py` | Regression audit & verification script |
| `verify_month2_video7.py` | Regression audit & verification script |
| `verify_month2_video8.py` | Regression audit & verification script |
| `verify_month3_video1.py` | Regression audit & verification script |
| `verify_month3_video2.py` | Regression audit & verification script |
| `verify_month3_video3.py` | Regression audit & verification script |
| `verify_month3_video4.py` | Regression audit & verification script |
| `verify_month3_video5.py` | Regression audit & verification script |
| `verify_step2.py` | Regression audit & verification script |
| `verify_video8.py` | Regression audit & verification script |
| `verify_week.py` | Regression audit & verification script |
| `visualize_audit.py` | Plotly visualization dashboard |
| `visualize_audit_plotly.py` | Plotly visualization dashboard |
| `visualize_cascade.py` | Plotly visualization dashboard |
| `visualize_month2_video1.py` | Plotly visualization dashboard |
| `visualize_month2_video2.py` | Plotly visualization dashboard |
| `visualize_month2_video3.py` | Plotly visualization dashboard |
| `visualize_month2_video4.py` | Plotly visualization dashboard |
| `visualize_month2_video5.py` | Plotly visualization dashboard |
| `visualize_month2_video7.py` | Plotly visualization dashboard |
| `visualize_month2_video8.py` | Plotly visualization dashboard |
| `visualize_month3_video1.py` | Plotly visualization dashboard |
| `visualize_month3_video2.py` | Plotly visualization dashboard |
| `visualize_month3_video3.py` | Plotly visualization dashboard |
| `visualize_month3_video4.py` | Plotly visualization dashboard |
| `visualize_smt_2026.py` | Plotly visualization dashboard |
| `visualize_smt_real.py` | Plotly visualization dashboard |
| `visualize_video4.py` | Plotly visualization dashboard |
| `visualize_video5.py` | Plotly visualization dashboard |
| `visualize_video6.py` | Plotly visualization dashboard |
| `visualize_video7.py` | Plotly visualization dashboard |
| `visualize_video8.py` | Plotly visualization dashboard |
| `AUDUSD_SEPT_2016_VALUATION.html` | Locked golden master output |
| `BTC_FORENSIC_AUDIT.html` | Locked golden master output |
| `ICT_CASCADE_MACRO_TARGETS.html` | Locked golden master output |
| `ICT_GOLD_MASTER_0e88d22b.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO1_TURTLE_SOUP.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO2_TURTLE_SOUP.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO3_TURTLE_SOUP.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO4_EXPECTANCY.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO5_MITIGATION.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO7_FALSE_FLAG.html` | Locked golden master output |
| `ICT_MONTH2_VIDEO8_MEASURED_MOVE.html` | Locked golden master output |
| `ICT_MONTH3_VIDEO1_BREAKERS.html` | Locked golden master output |
| `ICT_MONTH3_VIDEO2_TOPDOWN.html` | Locked golden master output |
| `ICT_MONTH3_VIDEO4_MONTHLY_RANGE.html` | Locked golden master output |
| `ICT_MONTH3_VIDEO5_SMT_DIVERGENCE.html` | Locked golden master output |
| `ICT_SMT_REAL_DATA.html` | Locked golden master output |
| `ICT_VIDEO_4_TRIPLE.html` | Locked golden master output |
| `ICT_VIDEO_5_PREMIUM.html` | Locked golden master output |
| `ICT_VIDEO_6_VALUATION.html` | Locked golden master output |
| `ICT_VIDEO_6_VALUATION_v2.html` | Locked golden master output |
| `ICT_VIDEO_8_MARKET_PROTRACTION.html` | Locked golden master output |
| `visualize_month3_video3.html` | Locked golden master output |
| `visualize_video7.html` | Locked golden master output |

## 6. Development Standards [LOCKED]
- **Stable Pathing:** Reports update master files (e.g., `ICT_VIDEO_6_VALUATION.html`, `visualize_video7.html`, `ICT_VIDEO_8_MARKET_PROTRACTION.html`, `ICT_MONTH2_VIDEO2_TURTLE_SOUP.html`).
- **Absolute Anchoring:** All shapes use raw `conf_ts` paired with strict Design Principle 14.
- **Institutional Audit:** Every run must print a `Timestamp | Type | Price | Zone` log for verification.
- **Notes First Policy (Lesson 4):** No architectural discussion on upcoming videos until curriculum notes are fully extracted and documented.
- **One Function, One Job:** Each `smc.*` classmethod does exactly one detection task and returns a plain DataFrame. No side effects, no visualization logic inside detectors.

## 7. Curriculum Lock Status
| Video | Topic | Status |
|---|---|---|
| V1–V3 | Power of 3, Liquidity Pools, NY Time | ✅ Locked |
| V4 | Equilibrium vs Discount (Bullish OTE) | ✅ Locked |
| V5 | Equilibrium vs Premium (Bearish OTE) | ✅ Locked |
| V6 | Institutional Suite (OB, FVG, MTF Confluence) | ✅ Locked |
| V7 | Sovereign Liquidity Engine (LRR/HRR State Machine) | ✅ Locked |
| V8 | Market Protraction (Temporal Manipulation) | ✅ Locked |
| Month 2, Video 1 | Growing Small Accounts | ✅ Locked (Turtle Soup, risk_engine, EXIT_SCHEDULE, MIN_SWING_PIPS guard, pre-entry structural targets) |
| Month 2, Video 2 | Framing Low-Risk Trade Setups | ✅ Locked (LTF fractal refinement, use_daily_ob_stop, refinement_level, direction-correct stops, three-pane dashboard) |
| Month 2, Video 3 | How Traders Make 10% Per Month | ✅ Locked (EXIT_SCHEDULE_V3 doc constant, liq_1h parameter, ts_target_1h column, three-pane dashboard) |
| Month 2, Video 4 | No Fear of Losing | ✅ Locked (Expectancy Matrix, calc_expectancy, calc_position_size, min_rr_for_win_rate) |
| Month 3, Video 3 | Institutional Sponsorship | ✅ Locked (max_session_ob_age_days, ts_target_fvg, ts_entry_price buffer, power3_sponsored, down_candle_violated, is_lethargic) |

## 8. Lessons Learned
- **Historical Lookback Context:** Full history must be loaded and processed before slicing the focus window. Running detectors on a sliced window loses critical lookback context (e.g. for swing highs/lows) and can cause signal detection to fail silently.
- **Float Precision:** Round `monthly_pct` to 2 decimal places in `calc_expectancy()` — Python float multiplication of percentages produces trailing noise (28.000000000000004) that must be explicitly rounded before returning.

## 9. Next Steps
- **Month 2, Video 4:** ✅ Locked. `calc_expectancy()`, `calc_position_size()`, and `min_rr_for_win_rate()` added to `risk_engine.py`. Gaps: `calc_compounded_growth()` remains unbuilt.
- **Next:** Month 2, Video 5 — Extract notes and scope implementation plan.

---
*Last Updated: May 27, 2026*
