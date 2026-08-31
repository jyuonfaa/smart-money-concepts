# Project Forensics

## 1. VIDEO STATUS UPDATES

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

**Month 3, Video 8** — status: LOCKED (this session, previously "provisionally unblocked")
- Original two fixes from earlier this session (POI dead-code bug, sourced to "we traded down into it," page 258) remain in place, unchanged.
- Root cause resolved: bearish-path validation previously reused a stale, never-updating bullish order block instead of a genuine bearish structural zone, because no real breaker-block detector existed in the codebase at the time. Root cause traced back to Month 3, Video 1's mislabeled/incomplete status (see Tier 1/2 catalogue) and resolved properly once Month 4, Video 5's smc._breaker_blocks() was built and verified from source.
- verify_video8.py's bearish flip logic rewired: when daily bias flips bearish, the POI now comes from the nearest confirmed bearish breaker block (BB == -1, BBBodyTop/BBBodyBottom) at or before the flip point, replacing the old stale-OB reuse. Bullish path left untouched (already validated correctly earlier this session).
- Verified via synthetic test: a controlled dataset with two independently-detectable bearish breaker blocks confirmed the flip logic selects the correct (most recent, chronologically prior) block and pulls its exact BBBodyTop/BBBodyBottom values -- confirmed bit-for-bit against an independent smc._breaker_blocks() call on the same data.
- Verified via real data: original Gatekeeper baseline (EURUSD Oct-Nov 2022) re-run with the fix in place. Execution count changed from the historical 3 (1 buy, 2 sells) to 1 (1 buy, 0 sells). This is confirmed to be the fix working correctly, not a regression -- the 2 removed sells were the exact ghost signals validated against the stale bullish OB, identified and root-caused earlier this session. The new 0-sell result reflects that no real bearish breaker existed in this short (24-day) dataset window before the flip -- an honest data limitation, not a code defect.
- Full-history diagnostic variant preserved separately as verify_video8_full_history.py -- confirmed the locked Gatekeeper dataset (verify_video8.py) was NOT permanently altered.
- Golden Master reconfirmed unaffected throughout all changes (HRR=471, LRR=37, 11 transitions).

**Month 4, Video 2** — status: Reviewed — no new detector function required; one actionable risk-filter parameter identified for Layer 6 (pip-range minimum for trade validity)
- Core content: External Range Liquidity vs. Internal Range Liquidity, and MTF cascade (Monthly -> Weekly -> Daily -> 4H -> 15M) for framing entries at internal range liquidity (order blocks) with exits at external range liquidity (old highs/lows). No new smc.py function required — uses only existing FVG, OB, and liquidity detectors.
- Sourced quote (pages 288-289): "...if the high in between the range low and the high that retraced from, if it's only 20 pips, is that a trade that would be viewed as something that you would take? In my opinion, no, because the range is only 20 pips... But the precursor is you want to look at price swings that offer about 40 pips. If you can see anything at 40 pips or higher in looking for a retracement to go long on that, that gives you a reasonable first profit objective... So if you're looking for say you're a trader, you want to have nothing less than 50 pips, okay, well that's great... So what you do is you want to look for ranges that have 50 pips or more, preferably about 75 to 80 pips is perfect, because even if it doesn't even break the range and go up above this old high, it still gives you the opportunity to get that 50 pips."
- Note: ICT's own guidance isn't a single fixed number — ranges from "reasonable" at 40 pips up to "perfect" at 75-80 pips. Any implementation should treat this as a preference range, not one hard threshold.
- Proposed (NOT implemented): risk_engine.py function validate_liquidity_run(entry_price, target_price, min_pips=40.0, optimal_pips=75.0, pip_size=0.0001) — rejects trades where the entry-to-target range falls below min_pips. Pending your decision on whether to build this now or defer.

**Month 4, Video 3** — status: Partial — MeanThreshold defect fixed and verified; core "Selection & Avoiding" HTF-alignment concept not yet implemented (Layer 4 dependency)
- Fixed: smc.ob() computed MeanThreshold ((open+close)/2 at OB candle index) but never included it in the returned DataFrame. Added to output. Verified against a test candle where body midpoint and wick midpoint genuinely diverge (0.98 vs 1.06) — confirms implementation is body-based, not wick-based, per M4V3's explicit instruction ("Do not use the wicks... measure the open to the close," page 294).
- New Tier 4 catalogue item: smc.ob()'s Top/Bottom fields are wick-based (_high/_low), contradicting M4V3's explicit body-focus teaching and this project's Design Principle 2. state_machine.py (line 1161-1162) already independently overrides Top to candle open — an undiscussed hot-patch for the same defect, discovered this session. NOT fixed — deliberately deferred, high blast radius (affects visualizers, verify_month3_video1.py's Top>Bottom assertion, and the existing state_machine.py workaround).
- Not yet implemented: the video's actual title concept, "Selection & Avoiding" — only trading order blocks aligned with Monthly/Weekly/Daily bias, using counter-trend OBs solely as profit-taking targets. This is a Layer 4 (MTF Alignment) concern; Layer 4 does not exist yet.
- Not yet implemented: "Displacement Multiple" rule — requiring a 2-3x rally relative to the OB's own body height before treating a subsequent retracement as a valid setup (page 303).
- Not sourced from this video, do not build: any fixed-pip target filter — that's M4V2's separate rule, do not conflate the two.

**Month 4, Video 4** — status: LOCKED (this session)
- New detector built: smc._mitigation_blocks(ohlc, swing_highs_lows, fvg_df, close_mitigation=True, structure_break_body=False). Detects bearish mitigation blocks — a candle (point A) where trapped long positions from a failed A->B rally seek to liquidate on retest, after price confirms a lower structure at point C.
- Sourced model (pages 308-316): A = last down-body candle before a rally; B = the rally's swing high; C = a subsequent lower low breaking below A, confirming bearish structure shift. Exact source (p.310 caption): "When Price Action Returns To The 'A' Point Of Reference -- The Long Positions Taken From 'A' To 'B' Price Swing Will Have An Opportunity To Liquidate Or 'Mitigate' The Net Loss That Occurred When Price Dropped From 'B' To 'C'."
- Model verification caught and corrected a real error mid-session: an initial re-read incorrectly merged points A and C into one point; re-verified against the exact page 310 caption and corrected before any code was written.
- Staircase/cascading behavior confirmed in scope and implemented (not deferred) -- multiple independent A/B/C legs detected across a downtrend, per pages 312-313 ("Every rally that sees lower prices needs to be mitigated," and two separate "Buyers Remorse" labels on successive legs in the source diagram).
- Two parameters, honesty-flagged per source status: close_mitigation (sourced, p.315 -- "the body of the candle is not violated") and structure_break_body (engineering assumption, explicitly NOT sourced, defaults to wick-based for consistency with existing swing_highs_lows conventions).
- Data Audit: 4 blocks on AUDUSD 2016 daily (EURUSD unavailable locally, substituted), 231 blocks on 15M staircase check, confirming cascading behavior works at scale. All structural invariants (ABodyTop >= ABodyBottom, ABodyTop <= AWickHigh) hold across every detected block.
- Visual Audit: confirmed correct zone anchoring (not wall-to-wall) against real chart data; compared a clean block against a known edge case.
- Known limitation, NOT fixed (no notes basis for a fix): the "last down candle" rule can select a near-doji candle as point A when one exists in the search range (example: 2016-10-28, body spread of 0.00001), producing a structurally thin/weak zone. No minimum body-size filter added -- not sourced, would be scope invention. Documented as an accepted edge case.
- Index-loss defect avoided at the source: unlike smc.ob()/fvg()/liquidity() (deferred Tier 4 defect, high blast radius), this is brand-new code with zero existing callers, so the DatetimeIndex was fixed correctly from the start rather than patched around downstream. Confirmed zero behavioral change (identical block detections before/after) and Golden Master unaffected.
- Deferred, logged separately: bullish mitigation block (symmetrical case, not demonstrated in M4V4 -- not built); smc.fvg() missing a native MeanThreshold/equilibrium column (same defect class as smc.ob()'s pre-fix gap -- computed locally inside _mitigation_blocks instead).

**Month 4, Video 5** — status: LOCKED (this session)
- New detector built: `smc._breaker_blocks(ohlc, swing_highs_lows, confirm_break_close=True, close_break=True, zone_body_based=True, stop_wick_based=True)`. Detects bullish and bearish breaker blocks -- a 3-swing raid-then-reversal structure where a swept old high/low reverses back through the swing zone that preceded it, flipping that zone's polarity.
- Sourced model (pages 317-323, corrected from an initial 317-326 estimate after direct page-boundary verification). Exact citations: Bearish (p.318) -- "a bearish range or Down Close Candle in the most recent Swing Low prior to an Old High being violated. The Buyers that buy this Low and later see this same Swing Low violated -- will look to mitigate the loss." Bullish (p.320), exact mirror.
- Model verification caught and corrected two real errors before code was written: (1) an initial claim that "Breaker Blocks require a swept extreme while Mitigation Blocks feature a failed sweep" was checked against M4V4's actual text and found unsourced -- retracted; (2) initial page-range estimate (317-326) was off by three pages, corrected to 317-323 via direct page-number verification.
- Explicit decision NOT to reuse `scratch_breaker.py`: cross-reference confirmed its topology matching (3-swing raid structure) was correct, but its candle-selection was "accidentally correct for the wrong reason" (worked only because swing-point index and last-qualifying-candle index usually coincide, not by correct construction), its zone geometry was unsourced wick-based, and it conflated detection with first-retest into one step. Built fresh instead.
- Four parameters, all explicitly honesty-flagged as ENGINEERING ASSUMPTIONS (none sourced from M4V5's text): `confirm_break_close` (activation threshold basis), `close_break` (retest invalidation basis, analogical carry-over from M4V4 p.315), `zone_body_based` (Design Principle 2 + M4V4 precedent), `stop_wick_based` (analogical carry-over from M4V4 p.315 -- M4V5's own "Stops" labels refer only to raided liquidity pools, not trade stop placement).
- Real implementation bug caught and fixed before verification: the original invalidation scan started immediately at the raid candle (`curr_swing`), which is structurally on the same side of the zone as the invalidation condition -- this caused near-instant false invalidation on every block (confirmed via diagnostic: all 6 initial bearish blocks invalidated exactly 1 candle after the raid). Fixed with a two-phase scan: Phase 1 (activation) tests against `MidSwingLevel` per p.317/p.320's explicit "wait for price to break through/come back down into" language; Phase 2 (invalidation) only begins after activation succeeds, testing against the BB candle's own zone. Re-verified with real numbers showing plausible multi-week/month gaps between raid, activation, and invalidation.
- Confirmed-only recording: `BB` is populated only when Phase 1 activation succeeds (unconfirmed raids are dropped, not recorded as partial/candidate blocks), matching the source's own framing ("As price moves away, that confirms the breaker," p.317) and matching `_mitigation_blocks`' precedent of dropping unconfirmed A/B setups.
- Data Audit (AUDUSD 2016): Daily -- 11 raw raid+candle triplets, 6 confirmed after activation (5 bearish, 1 bullish), 3 invalidated / 3 live. 15M -- 691 raw, 662 confirmed, 644 invalidated / 18 live. Activation-gap distribution checked directly (median 73.5 candles on 15M, only 1.8% activating within 1-2 candles) to rule out a too-loose confirmation threshold as an explanation for the high 15M confirmation rate.
- Visual Audit: zone anchoring, raid/activation/invalidation markers, and DatetimeIndex preservation (confirmed via explicit dtype check, built correctly from the start this time) all verified against real chart data for one bearish and the only available bullish example, cross-checked directly against the Data Audit table's numeric values.
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).
- Not sourced, deliberately omitted: FVG target (M4V5's text contains no reference to FVG-based targets for breaker entries, unlike M4V4).
- Not sourced, deliberately not built: staircase/cascading carry-forward logic (confirmed absent from M4V5's text, unlike M4V4's explicit cascading language) -- each triplet is evaluated independently; natural repeating patterns are still detected without enforced continuity.

**Month 4, Video 6** — status: LOCKED (this session)
- New detector built: smc._rejection_blocks(ohlc, swing_highs_lows, close_invalidation=True). Detects bullish and bearish rejection blocks -- zones defined by the extremal spread between a swing cluster's wick extreme and its body extreme (highest/lowest open-or-close), not a single-candle selection or multi-swing structure.
- Sourced model (pages 324-333). Exact citations: Bearish (p.327) -- "a Price High has formed with long wicks on the high(s) of the candlestick(s) and Price reaches up above the body of the candle(s) to run Buy Side Liquidity out before Price Declines." Bullish (p.332), exact mirror.
- Architecturally distinct from _mitigation_blocks (2-swing A/B/C) and _breaker_blocks (3-swing raid+reversal): _rejection_blocks requires only a single swing cluster, with no structural confirmation/activation phase. Confirmed via citation check that an initially-proposed "activation" requirement (mirroring Breaker Block's two-phase structure) was NOT sourced -- retracted before implementation. p.330-331 confirms the zone is fully formed and immediately treated as a POI the moment the swing completes.
- Cluster boundary: bounded to [prior_opposite_swing + 1, current_swing] inclusive, reusing the same zone-bounding pattern as _breaker_blocks' candle selection. Explicitly flagged as ENGINEERING ASSUMPTION -- M4V6 leaves "swing high"/"swing low" undefined beyond the conceptual level; disjointness between adjacent clusters proven by the same interval-based argument used for _breaker_blocks.
- close_invalidation parameter flagged as ENGINEERING ASSUMPTION (analogical carry-over from M4V4/M4V5 order-block-style invalidation), though with somewhat more textual support than prior carry-overs since M4V6 explicitly states "we treat this as a bearish order block."
- Output columns include RBTop/RBBottom (zone rendering) plus explicitly direction-gated RBWickLevel (stop reference) and RBBodyLevel (trade trigger, sourced to p.331: "when price trades back up to the low of that range, that is your trigger") -- avoiding the single-ambiguous-column risk flagged and corrected during M4V5's design.
- Implementation review caught and fixed an interface mismatch before first execution: initial draft accepted swing_highs_lows as a bare Series and used label-based indexing, inconsistent with the established integer-position array pattern in _mitigation_blocks/_breaker_blocks. Corrected before any code ran.
- Data Audit (AUDUSD 2016): Daily -- 30 blocks (15 bearish, 15 bullish), 17 invalidated / 13 live. 15M -- 2795 blocks, 2738 invalidated / 57 live. All structural invariants passed (RBTop >= RBBottom, correct direction-gating on RBWickLevel/RBBodyLevel).
- Distribution diagnostics run (same standard as M4V5's activation-gap check): 15M zone widths span 0.1-38.1 pips (median 2.9); ~14% of blocks under 1 pip satisfy the sourced definition but don't match the qualitative "long wick" framing -- documented as a known characteristic, NOT filtered, since M4V6 gives no quantitative minimum and adding one would be unsourced scope invention (consistent with the M4V4 doji precedent). Time-to-invalidation on 15M: min 6 candles, median 30 -- confirms no instant-death false-invalidation pattern (the specific bug class caught and fixed in _breaker_blocks).
- Manual geometry verification: two daily blocks (2016-02-04 BEAR, 2016-02-09 BULL) hand-inspected against raw OHLC rows, confirming genuine single-candle spike-wick geometry, not artifacts.
- Visual Audit: both hand-verified blocks cross-checked directly against rendered charts -- exact zone boundaries, correct invalidation timing, and correct live-block rendering (extends to last real data point, not the M4V1-style hardcoded/lost-index wall-to-wall pattern).
- Golden Master reconfirmed unaffected (HRR=471, LRR=37, 11 transitions).

**Month 4, Video 7** — status: Reviewed — no new detector function required; blocked on Layer 4 (MTF Alignment) for a "major swing" significance definition
- Core content: "Reclaimed Order Block" -- ordinary bullish/bearish order blocks (standard smc.ob() geometry, no new zone construction) formed on the approach leg toward a major swing extreme ("Market Maker Buy Model" = V-shape decline-then-rally; "Market Maker Sell Model" = mirrored inverted-V), later retested as valid entries once price is on the departure leg of that same cycle.
- Sourced definitions (pages 334-341). Exact citations: Bullish (p.336) -- "a candle or bar that was previously used to Buy Price and a short term bounce confirms minor displacement. In the Buy Side Of Curve -- these 'old' blocks will be reclaimed longs." Bearish (p.338), exact mirror.
- Model correction caught before build plan: an initial proposal modeled this as a strict 3-swing raid-then-reversal topology, directly mirroring _breaker_blocks' structure. Retracted after citation check -- p.336's "Every time there was a bullish order block... every new buying opportunity is going to be matched up to the previous down candle" describes ALL qualifying OBs along the entire approach leg, not one specific swing adjacent to a climax. Confirmed visually: pages 337 and 339-340 each show TWO separate reclaimed OBs from two different points along the same leg, not a single fixed-position anchor.
- No new smc.py function required: the underlying zone geometry is standard smc.ob() output. What's genuinely new is purely contextual -- classifying which detected OBs sit on the approach to a "major"/"climax" swing, as opposed to a minor one -- and M4V7's text never operationally defines "major" or "climax" beyond narrative description. This is the same class of gap already identified in M4V2 (External/Internal Range Liquidity selection) and M4V3 (Selection & Avoiding / HTF-alignment): a Layer 4 (MTF Alignment) dependency, not a Layer 2 detection problem. Recursive-scale ambiguity noted explicitly: the same "down-candle-then-bounce" pattern exists at every timeframe scale, so without an external significance judgment, any implementation either over-detects every swing as a candidate curve or requires the HTF context Layer 4 would provide.
- Zone geometry note: charts (p.337, p.339-340) show simple single horizontal reference lines at the OB candle's own extremes, consistent with reusing standard smc.ob() Top/Bottom output directly -- NOT the two-boundary wick/body cluster geometry used in _rejection_blocks. No new geometric logic needed once the "major swing" classification problem is solved.
- Deferred: full implementation pending Layer 4 definition of HTF/major-swing significance, same dependency blocking M4V2's risk parameter context and M4V3's core HTF-alignment concept.

**Month 4, Video 8** — status: LOCKED (this session)
- New detector built: smc._propulsion_blocks(ohlc, ob_df). Detects propulsion blocks -- a same-direction order block that trades back into (retests) a prior, already-confirmed order block, becoming a new, higher-sensitivity zone in its own right.
- Sourced model (pages 342-346, final video in the document). Exact citation (p.342): "A propulsion block is a candle or bar that has previously traded down into a down candle or bullish order block and takes over the role of price support for higher price movement."
- Six explicitly honesty-flagged engineering assumptions, more than any prior detector this session, reflecting genuine source silence on several mechanics: (1) color guard for smc.ob()'s anomalous candle selection, (2) body-based zone recomputation overriding smc.ob()'s wick-based Tier 4 defect, (3) wick-vs-body overlap definition, (4) staircase/chaining permitted, (5) close-based violation mechanics (consistency with _breaker_blocks/_rejection_blocks precedent, not M4V8-sourced), (6) conservative anchor-reset-on-any-color-mismatch rule.
- Corrected a false claim during planning: initial proposal equated mean-threshold violation with formal stop-loss placement. Retracted after citation check -- text describes mean-threshold violation as a discretionary WARNING SIGNAL ("chances are it's probably not a good trade"), not a stated stop-loss rule. Resolved with a separate, purely observational MeanThresholdViolated column, leaving structural Invalidated at the standard wick-extreme convention.
- New characterization of existing Tier 4 defect: quantified smc.ob() candle-selection anomaly (selecting opposite-colored candles when they hold the extreme wick) at 4/12 bullish and 3/8 bearish on AUDUSD 2016 15M -- a substantial, not marginal, rate. On daily data this eliminated 6 of 7 OB anchors, reducing to zero detectable propulsion blocks for the full year.
- Real implementation bug found and fixed post-implementation, not caught in initial review: stale anchor pairing across large gaps. A color-guard-skipped OB failed to clear the tracked anchor, allowing a bearish propulsion block to pair against an anchor 91 calendar days and ~1000 pips away (trivially passing the overlap check). Found via targeted diagnostic on a suspicious outlier flagged during Data Audit, not caught during code review -- confirmed with raw numbers before fixing.
- Fix produces an explicit, quantified design tradeoff (documented as Assumption 6, not silently accepted): resetting the anchor to None on ANY color-guard skip, rather than a price-proximity-aware reset, was chosen to avoid introducing an unsourced numerical threshold (same category of scope invention already caught in M4V7). Confirmed cost: 15M detections dropped from 10 (including the confirmed false positive) to 4 (some potentially-genuine pairings also eliminated by the conservative rule). Explicitly logged as erring toward false negatives over false positives.
- File-integrity incident during implementation: initial code injection into smc.py required two corrective passes (de-indentation, removal of stray @staticmethod artifacts). Verified clean afterward via full-file structural review and re-running verify_month4_video4.py, verify_month4_video5.py, and verify_month4_video6.py to confirm no collateral damage to previously-locked detectors.
- Data Audit: Daily -- 7 OB anchors, 6 skipped by color guard, 0 propulsion blocks (correctly reflects the Tier 4 defect's severity at this timeframe). 15M -- 40 anchors, 14 skipped, 4 propulsion blocks post-fix (3 bullish, 1 bearish), structural invariants passed (PBTop >= PBBottom, MeanThresholdViolated always at or before Invalidated).
- Visual Audit: two blocks (2016-11-10 BULL, 2016-12-16 BEAR) cross-checked directly against the audited table -- zone geometry, anchor placement, and MT/Invalidated markers all confirmed correct; Dec-16 example shows a ~500-pip decline following the propulsion candle, a strong visual match to the source's "propels price quickly and suddenly" description.
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions), including after both direct file edits.
- This is the final video in the ICT Mentorship 2016 document (page 346 of 346).

**Month 4, Video 9** — status: LOCKED (this session)
- New detector built: smc._vacuum_blocks(ohlc, ob_df, close_fill=True, close_invalidation=True). Detects vacuum blocks — breakaway gaps up or down representing a vacuum of liquidity driven by a volatility event.
- Sourced model (pages 347-354): "A bullish vacuum block is a gap that's created in price action as a result of a volatility event." Zone geometry strictly uses the open/close boundaries of the gap (no wick component), bounding the literal empty space.
- Wiring pattern identical to the prior four detectors (module-level function, monkey-patched via smc._vacuum_blocks = staticmethod(_vacuum_blocks)).
- Three explicitly honesty-flagged engineering assumptions due to source silence: (1) close_fill=True (gap fill confirmed by candle close reaching the zone boundary, rather than wick penetration), (2) close_invalidation=True (post-fill invalidation confirmed by candle close breaking back beyond the origin level), (3) VBOverlapsOB uses a strict position-aware scan against ob_df['MitigatedIndex'] to ensure it only considers OBs that are live/unmitigated as of the VB's formation candle.
- Dataset-suitability finding: Data Audit revealed 99.3% of detected VBs on 15M continuous 24h data (and ~80% on Daily) were sub-1-pip gaps caused by tick-level rounding across resampling boundaries (consecutive 23:59 and 00:00 M1 bars). The detector logic is mathematically correct and accurately detected a genuine 11.4 pip weekly open gap on Sep 18, but M1-resampled data is fundamentally unsuitable for this concept without true intrabar trading halts.
- Visual Audit: Sep 18 17:00 (UTC) weekly open bearish block rendered via custom date-axis chart. Clearly demonstrated the Friday close / Sunday open physical gap, bounding the zone at [0.74776, 0.74890]. Accurately showed consecutive FILLED (18:45) and INVALIDATED (19:00) markers as price blew straight through the zone without stalling, verifying the close-based condition logic.
- Golden Master reconfirmed unaffected (HRR=471, LRR=37, 11 transitions).

**Month 4, Video 10** — status: LOCKED (this session)
- New detector built: smc._liquidity_voids(ohlc, consolidation_df, swing_highs_lows, fvg_df, close_fill=True). Detects aggressive displacement runs (liquidity voids) departing from a consolidation zone through to the first terminating opposing swing.
- Sourced model (pages 355-362): "A liquidity void is a range in price delivery where one side of the market liquidity is shown in wide or long one-sided ranges or candles. Price typically will want to revisit this porous range or void of contrarian liquidity." Direction named for the missing liquidity side: bearish displacement is 'buy-side' void; bullish displacement is 'sell-side' void (p.357).
- Differentiated from smc.fvg(): Verified that smc.fvg() only captures individual wick gaps (~41-47% of a run's range), whereas the liquidity void spans the ENTIRE displacement move from consolidation exit (LVStart) to swing termination (LVEnd).
- Zone geometry & Fill tracking: LVLow and LVHigh bound the full extremes of the run. LVFilled marks the timestamp when price covers back across the origin cap level (LVHigh for buy-side void, LVLow for sell-side void). No timeout logic applied, honoring p.356 ("They can stay open for months").
- LVCommonGapRef: Contextual pointer into existing fvg_df for entries occurring near the cap level post-fill (pp.360-361); confirmed in diagnostic to locate true adjacent FVGs independent of the fill bar.
- Three explicitly honesty-flagged engineering assumptions: (1) No minimum size or candle count threshold (every consolidation-exit-to-next-swing is flagged), (2) close_fill=True (close past cap level confirms fill), (3) 'at or near' cap level for common gap defined as within 20% of the void range.
- Fixes applied during implementation: Resolved RangeIndex/positional-integer defect inside the function to ensure timestamps are returned for LVFilled/LVCommonGapRef/LVStart regardless of upstream index resets. Added explicit LVStart column to resolve formation vs. termination indexing ambiguity.
- Data Audit: Daily (2 voids, both buy-side, 0 filled — including a 4.5-month span from Jan 14 to May 24); 15M Sep 11-18 (7 voids, 3 buy-side, 4 sell-side, 4 filled, 4 common gap refs).
- Visual Audit: Rendered Chart 1 (AUDUSD 15M Sep 11-13 full lifecycle: LVStart, LVEnd, LVFilled at Sep 13 10:45, and distinct LVCommonGapRef at Sep 13 11:00) and Chart 2 (AUDUSD Daily Jan-Jun 2016 multi-month anchoring check spanning Jan 14 to May 24 without wall-to-wall defects).
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).



## 2. KNOWN CORE LIBRARY DEFICIENCIES (new section, four tiers)

TIER 1 — Never built, no code exists anywhere in repo history:
- smc.macro_swing_grading()
- smc.measured_moves()
- smc.monthly_range_ob()

TIER 2 — Real implementation exists but orphaned/unmerged/unverified:
- smc.ny_midnight_open() — in append_to_smc.py, never reviewed against notes at all

TIER 3 — Hallucinated, never existed, do not attempt to locate:
- smc.sequence_void() / smc.void_scanner() — confirmed via git log -S across full history, zero results ever

TIER 4 — Existing function with a confirmed defect:
- smc.ob() — ~~missing 'MeanThreshold' output column (KeyError in verify_mean_threshold.py)~~ **FIXED this session**: column now included in returned DataFrame; verified body-based formula (open+close)/2 against a discriminating test candle (body mid=0.98 ≠ wick mid=1.06).
- smc.ob() — Top/Bottom fields are wick-based (_high/_low at the OB candidate candle), contradicting M4V3's explicit body-focus teaching ("Do not use the wicks... measure the open to the close," page 294). state_machine.py already independently overrides Top to candle open (line 1161-1162) as a hot-patch for the same defect. NOT fixed — deliberately deferred; high blast radius (visualizers, verify_month3_video1.py's Top>Bottom geometry assertion, state_machine.py workaround).
- smc.ob() — Anchor candidate selection occasionally picks opposite-colored candles (e.g., an up-close candle selected as a bullish down-candle OB) if they hold the extreme wick of the swing. Confirmed on AUDUSD 2016 15M (4/12 bullish, 3/8 bearish anomalous). Contradicts strict consecutive-candle structural rules (M4V8). Workaround applied: downstream caller (_propulsion_blocks) filters by color guard. NOT fixed at source — deferred due to blast radius.
- smc.ob() / smc.fvg() / smc.liquidity() — all three silently return integer RangeIndex instead of preserving the original DatetimeIndex. Worked around ad hoc in state_machine.py (lockstep .iloc), verify_step2.py (manual hot-patch), generate_gif.py (manual remapping). NOT fixed at source — deliberately deferred, high ripple risk. Warning comments added directly above each function in smc.py this session.
- smc.fvg() -- missing MeanThreshold/equilibrium output column, same pattern as smc.ob()'s pre-fix defect. Computed locally inside _mitigation_blocks instead. Deferred.

## 3. VERIFY SCRIPT INTEGRITY

- verify_month3_video2.py — confirmed clean, no exit-code gap remaining.
- audit_month3_video1.py — sys.exit(1) added when fail count > 0 (previously exited 0 despite 4 failed checks).
- verify_month3_video1.py — still crashes on smc.macro_swing_grading() before completion (Tier 1 gap, unresolved).
- verify_month3_video5.py — cosmetic UnicodeEncodeError on '<-' character fixed (replaced with ASCII '->'). No logic changed.
- Confirmed NOT silent-fail (crash outright instead, safer failure mode): verify_mean_threshold.py, verify_month2_video8.py, verify_month3_video3.py.

## 4. HOUSEKEEPING
- Session diagnostic scripts moved to cslim/diagnostics/: diag_smt_at_liquidity_baseline.py, diag_triad_pois.py, run_audit.py, temp_zoom.py, visualize_month4_video1_zoomed.py (this last one has a known unfixed bug — shared_xaxes binding prevents xaxis_range override — left broken intentionally, not a functioning tool).



## 5. FULL FUNCTION INVENTORY — smc.py
- **`inputvalidator(input_)`** | Decorator. Internal utility. | Built: UNKNOWN | Status: Original
- **`apply(decorator)`** | Decorator. Internal utility. | Built: UNKNOWN | Status: Original
- **`fvg(cls, ohlc, join_consecutive)`** | Detects Fair Value Gaps. | Built: Month 2 | Status: Original
- **`swing_highs_lows(cls, ohlc, swing_length)`** | Detects Swing Highs and Lows. | Built: Month 2 | Status: Original
- **`bos_choch(cls, ohlc, swing_highs_lows, close_break)`** | Detects Break of Structure and Change of Character. | Built: Month 2 | Status: Original
- **`ob(cls, ohlc, swing_highs_lows, close_mitigation)`** | Detects Order Blocks. | Built: Month 2 | Status: Modified (Added MeanThreshold output, M4V3)
- **`liquidity(cls, ohlc, swing_highs_lows, range_percent)`** | Detects Liquidity pools. | Built: Month 2 Video 3 | Status: Modified (Added `is_too_clean` flag, fixed wick-based sweep bug to close-based, M3V2)
- **`previous_high_low(cls, ohlc, time_frame)`** | Detects Previous High Low. | Built: UNKNOWN | Status: Original
- **`sessions(cls, ohlc, session, start_time, end_time, time_zone)`** | Detects sessions. | Built: UNKNOWN | Status: Original
- **`retracements(cls, ohlc, swing_highs_lows)`** | Detects percentage of retracement. | Built: UNKNOWN | Status: Original
- **`consolidation(cls, ohlc, prd, conslen)`** | Detects Consolidation Zones - Live. | Built: UNKNOWN | Status: Modified
- **`expansion(cls, ohlc, consolidation)`** | Detects when price body closes beyond the consolidation boundary. | Built: UNKNOWN | Status: Built from scratch
- **`displacement(cls, ohlc, lookback, range_p, body_p)`** | Uses statistical percentiles to identify "Real Big Candles". | Built: UNKNOWN | Status: Built from scratch
- **`swing_highs_lows_v4(cls, ohlc)`** | Religious 4-Candle confirmation with Strict Alternation. | Built: Month 2 Video 4 | Status: Built from scratch
- **`identify_order_block(cls, ohlc, confirmed_swings)`** | Basic order block identifier. | Built: UNKNOWN | Status: Built from scratch
- **`_smt_divergence(ohlc, benchmark_ohlc, asset_swings, correlation, lookaround_bars, fvg_df, liquidity_df)`** | Institutional Market Structure (SMT Divergence). | Built: Month 3 Video 5 | Status: Built from scratch
- **`triad_divergence(usdx_ohlc, triad_ohlcs, usdx_swings, lookaround_bars, usdx_pois, neutral_tolerance_pct)`** | Interest Rate Triad Divergence. | Built: Month 4 Video 1 | Status: Built from scratch
- **`_smt_apply_bias_filter(signal_df, smt_df, signal_type)`** | Execution Layer Bias Wiring. | Built: Month 3 Video 5 | Status: Built from scratch
- **`_market_protraction(ohlc, threshold_pips)`** | Temporal Manipulation Swing Detector. | Built: Month 3 Video 8 | Status: Built from scratch (Renamed to private `_market_protraction`)
- **`_filter_quarterly_swings(swings_df, min_days)`** | Enforce the ICT Quarterly Shift Constraint. | Built: UNKNOWN | Status: Built from scratch
- **`_macro_bond_bias(zn_df, zb_df, dxy_df)`** | Macro Economic To Micro Technical (Bond SMT). | Built: Month 3 Video 6 | Status: Built from scratch
- **`_macro_pair_bias(macro_bias_series, pair_name)`** | GAP 1: Currency Pair Classification Engine. | Built: UNKNOWN | Status: Built from scratch
- **`_macro_ob_alignment(zb_df, dxy_df, swing_length)`** | Detects the 'Prime Setup' confluence. | Built: Month 3 Video 6 | Status: Built from scratch
- **`_trendline_phantoms(ohlc, swings)`** | Detects False Trendline (Phantom) Traps. | Built: Month 3 Video 7 | Status: Built from scratch
- **`_phantom_signals(ohlc, phantoms, ob_df, htf_bias)`** | Full 3-Phase Market Maker Trap Execution Engine. | Built: Month 3 Video 7 | Status: Built from scratch
- **`_false_hns_patterns(ohlc, swings, max_neckline_slope_pct)`** | Detects False Head and Shoulders Traps. | Built: Month 3 Video 8 | Status: Built from scratch
- **`_hns_signals(ohlc, patterns, htf_bias, htf_poi_top, htf_poi_btm)`** | Executes trades on the diagonal neckline sweep. | Built: Month 3 Video 8 | Status: Built from scratch
- **`_mitigation_blocks(ohlc, swing_highs_lows, fvg_df, close_mitigation=True, structure_break_body=False)`** | Detects bearish mitigation blocks. | Built: Month 4 Video 4 | Status: Built from scratch
- **`_breaker_blocks(ohlc, swing_highs_lows, confirm_break_close=True, close_break=True, zone_body_based=True, stop_wick_based=True)`** | Detects bullish and bearish breaker blocks. | Built: Month 4 Video 5 | Status: Built from scratch
- **`_rejection_blocks(ohlc, swing_highs_lows, close_invalidation=True)`** | Detects bullish and bearish rejection blocks. | Built: Month 4 Video 6 | Status: Built from scratch
- **`_propulsion_blocks(ohlc, ob_df)`** | Detects propulsion blocks. | Built: Month 4 Video 8 | Status: Built from scratch

## 6. FULL FUNCTION INVENTORY — state_machine.py
- **`PriceDeliveryState`** | Data class for logging state. | Built: UNKNOWN | Status: Built from scratch
- **`PriceDeliveryStateMachine.process(self, ohlc, consolidation, expansion, displacement, liquidity, reversals, htf_context, swing_hl)`** | Institutional Logging Engine (transitioned from a predictive state machine to a passive logging system). | Built: Month 2 Video 3 | Status: Built from scratch

## 7. KNOWN BUGS AND REGRESSIONS — CURRENT STATUS
- **AttributeError**: `type object 'smc' has no attribute 'sequence_void'`
  - **File**: `verify_audusd_sept.py` (Line 47).
  - **Status**: OPEN — LOW PRIORITY. Not gating anything. `verify_audusd_sept.py` is not the canonical Golden Master (see Section 5).
  - **Root Cause (confirmed)**: `sequence_void` was never defined anywhere in this repo's history. Confirmed via `git log --all -S "def sequence_void"` returning zero results. The function call was written in commit `22d1c4f` (Jun 7, 2026) referencing a function that did not exist at the time. This is a hallucinated API call, not a rename or removal.
- **AttributeError**: `type object 'smc' has no attribute 'market_protraction'`
  - **File**: Formerly `verify_video8.py`.
  - **Status**: Resolved via `verify_market_protraction.py`. `market_protraction` was renamed to `_market_protraction` (module-level private) in `smc.py` on Jun 7. `verify_video8.py` was overwritten on Jun 8 to test Multi-Timeframe logic instead. The original regression coverage has been restored as `verify_market_protraction.py`, which calls `_market_protraction` directly via module import.
- **Other Regressions**: UNKNOWN.

## 8. GOLDEN MASTER STATUS

### Canonical Golden Master — CONFIRMED PASSING
- **Script**: `verify_step2.py`
- **Dataset**: AUDUSD September 2016 (15M), window Sep 11–18
- **Last run**: 2026-08-07 (local) / 2026-08-08T04:18 UTC
- **Status**: ✅ CONFIRMED PASSING
- **Exact output**:
```
VERIFICATION STEP 2: AUDUSD Sept 2016 (Sep 11-18)
VERIFICATION: DEDUPLICATION [date]
Total raw signals before dedup: 1321
Total signals after strict alternation: 859
Signals discarded: 462
DEBUG: Expansion non-NaN count: 421

TOTAL ENVIRONMENT COUNTS (September):
SovereignEnv
HRR    2000
LRR      84
Name: count, dtype: int64

ENVIRONMENT COUNTS (Sep 11-18):
SovereignEnv
HRR    471
LRR     37
Name: count, dtype: int64

--- TRANSITION AUDIT ---
Total genuine transitions: 11
Avg LRR block: 16.8 candles
Avg HRR block: 325.4 candles
```
- **Gate**: HRR=471, LRR=37, 11 genuine transitions. All three must match exactly before any milestone is declared locked.

---

### Non-Canonical / Known-Broken Scripts

**`verify_audusd_sept.py`** — BROKEN, NON-CANONICAL
- Crashes at line 47 on `smc.sequence_void(df_4h)`.
- `sequence_void` has never existed in this repo's history (zero results in `git log --all -S "def sequence_void"`).
- This script was written against a hallucinated API. It is not the Golden Master and has never successfully produced the HRR/LRR output.
- Priority: LOW. Not gating any milestone. Do not use for regression checks.

**`verify_market_protraction.py`** — UNVALIDATED (first-run data only)
- Restored from git commit `af4ae258` (Jun 7, 2026), updated to call `_market_protraction` via direct module import.
- Current output (2026-08-08): ASIA: 25, NY_OPEN: 19, MIDNIGHT: 17, Total: 61 protraction swings (last 3000 candles of `EURUSD_15M.csv`).
- No prior recorded baseline exists anywhere in session logs or git history. The original script was overwritten on Jun 8 before any output was ever committed or logged.
- Status: UNVALIDATED. Treat current output as first-run observation only. Requires Data Audit + Visual Verification before it can be used as a reference.

## 9. FILE STRUCTURE — FULL TREE
- `smartmoneyconcepts/smc.py` - Core ICT pattern detection library.
- `smartmoneyconcepts/state_machine.py` - Institutional logging engine.
- `verify_month2_video*.py` - Month 2 concept unit tests.
- `verify_month3_video*.py` - Month 3 concept unit tests.
- `verify_month4_video1.py` - Month 4 Video 1 audit script.
- `verify_video8.py` - Multi-timeframe execution logic test for M3V8.
- `verify_step2.py` - **Canonical Golden Master regression script** (HRR=471, LRR=37, 11 transitions).
- `verify_audusd_sept.py` - BROKEN, NON-CANONICAL. Crashes on `smc.sequence_void` which never existed. Low priority.
- `verify_market_protraction.py` - Restored market protraction regression. UNVALIDATED — first-run only, no prior baseline.
- `visualize_*.py` - Plotly HTML generation scripts for various videos.
- `diag_*.py`, `patch_*.py`, `rewrite_*.py`, `extract_*.py`, `debug_*.py` - Orphaned experimental/patch scripts (Over 80+ files not directly referenced in main flows).
- `mtf_engine.py` - Layer 4 scaffolding.
- `risk_engine.py` - Layer 6 scaffolding.
- `cslim/sync_manager.py` - CSLIM internal sync.

*(Note: There are ~240 files in the root; listing every single one explicitly is truncated here to focus on functional structure, but there are over 100 scratch scripts like `scratch_breaker.py`, `nuclear_fix_video4.py`, etc., that appear to be orphans).*

## 10. LAYER STATUS
- **Layer 1 (Data)**: Implemented. Raw CSVs are stored in `tests/test_data/MACRO/` and `tests/test_data/EURUSD/`.
- **Layer 2 (Detection)**: Heavily implemented in `smc.py`.
- **Layer 3 (Level Registry)**: Not started. No scaffolding exists.
- **Layer 4 (MTF Alignment)**: Scaffolding exists (`mtf_engine.py`, `mtf_demo.py`).
- **Layer 5 (Rule Engine)**: Scaffolding exists (`state_machine.py`).
- **Layer 6 (Risk Management)**: Scaffolding exists (`risk_engine.py`).
- **Layer 7 (Execution)**: Not started / Minimal (some logic exists inside `_hns_signals` and `_phantom_signals`, but no standalone execution module).

## 11. RECENT SESSION HISTORY
1. **Aug 7, 2026**: Add all PDFs, HTMLs, and images (except 308MB docx) to Git. Outcome: Completed.
2. **Aug 7, 2026**: Add month4 resources, MACRO test data, verify script, and update extract_pdf_images. Outcome: Completed.
3. **Jun 9, 2026**: fix: Implemented Gaps 3, 4, 5 — Neutral bond tolerance, comprehensive POI gate, and Triad+SMT chaining. Outcome: Completed.
4. **Jun 9, 2026**: fix: Triad divergence gap fixes — resolution-agnostic docstring + POI gate (M4V1). Outcome: Completed.
5. **Jun 9, 2026**: feat: Add missing 5-Year Note (ZF) data and integrate into Triad analysis. Outcome: Completed.

## 12. ANYTHING FLAGGED AS UNCERTAIN
- **Golden Master Test Integrity**: RESOLVED. `verify_step2.py` confirmed passing (HRR=471, LRR=37, 11 transitions) as of 2026-08-07. `verify_audusd_sept.py` is confirmed non-canonical — it called a function that never existed in the repo.
- **Video 8 Market Protraction Audit**: Partially resolved. `verify_market_protraction.py` restores the original script structure and runs clean (61 signals, EURUSD 15M last 3000 candles). However, the output is UNVALIDATED — no prior baseline exists. `verify_video8.py` (Multi-Timeframe) is untouched and continues to pass.
- **Orphan Scripts**: There are over 100+ scripts (`patch_*.py`, `rewrite_*.py`, `debug_*.py`, `diag_*.py`) in the root directory. It is completely UNCERTAIN which of these are still relevant and which are dead code.
- **Exact Gatekeeper Lock Dates**: UNKNOWN. The exact timestamps for when videos 1-3 were "locked" by the gatekeeper are not tracked in easily accessible `.md` logs in the root.


---
*Last Updated: 2026-08-08*
