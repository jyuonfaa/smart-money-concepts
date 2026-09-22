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

**Month 4, Video 11** — status: LOCKED (this session)
- New detector: smc._liquidity_raids(ohlc, swing_highs_lows, sweep_expected_min_pips=10.0, sweep_expected_max_pips=20.0, sweep_reject_threshold_pips=25.0, pip_size=0.0001, close_revert=True), wired via staticmethod.
- Scope deliberately split at planning stage: this video's own text (p.364) requires HTF bias for trade direction and profit target selection -- logged as a Layer 4 dependency, same class as M4V2/M4V7. The 30-50 pip stop-placement rule is a Layer 6 (risk_engine.py) concern, not built here. This detector answers only "was a swing level violated, and by how much."
- Violation detection is sourced as wick-based (p.366's stop-order mechanic), not an engineering assumption.
- Two engineering assumptions: close_revert mechanic/window (10-bar forward scan, unsourced), and the "elevated" classification tier (20-25 pips) filling a gap the source's own 10-20/>25 numbers don't name.
- Real correction during build: initial classification logic silently absorbed the unsourced 20-25 pip zone into "expected," diluting the sourced 10-20 pip range's meaning. Caught against real data -- both daily 2016 examples (20.2 and 22.1 pips) fell exactly in that undefined gap -- and fixed with the properly-flagged "elevated" tier before lock.
- Data Audit: Daily AUDUSD 2016 -- 2 raids detected (both "elevated," 1 reverted). 15M Sep 11-18 -- 3 raids (2 shallow, 1 expected; 2 reverted). Sparse daily detection consistent with established swing/consolidation-dependent pattern at that timeframe.
- Visual Audit: passed on a single clean 15M example (2016-09-15 08:30, 10.9 pip sweep, expected classification, reverted to close 0.74695 below the 0.74956 swing level).
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).

**Month 4, Video 12** — status: REVIEWED — no new detector required
- Verified via real data (AUDUSD 15M Golden Master example) and against ICT's own worked numbers (EURUSD daily, pages 376-377) that the fair value gap boundary taught in this video is arithmetically identical to smc.fvg()'s existing Top/Bottom output (Candle 1 Low, Candle 3 High for a bearish FVG).
- The "exclusion" language in the source (pages 376-377) is pedagogical explanation of WHY the boundary sits at the wick extreme, not a distinct narrower geometric rule -- an initial misreading of this was tested against real data, found to invert/destroy the gap mathematically, and correctly retracted before being accepted.
- Two findings worth logging even without new code:
  1. Body-based fill/mitigation reconfirmed a third time (page 384: "the wick trades through the body, but the bodies of the candle completely close in here") -- consistent with M4V9's vacuum block and M4V10's liquidity void close-based fill conventions.
  2. Reusable-level behavior observed (pages 385-386): the same reference level gets hit and reacted to multiple times ("does it twice"), described as a "full block of delivery deficiency" addressed across both sides of price delivery. No current M4 detector (mitigation, breaker, rejection, propulsion, vacuum, liquidity void, liquidity raid) models a level being revisited/re-tradeable after first fill/invalidation -- all are single-formation, single-resolution. Flag this as a known simplification across the full detector set, relevant when Layer 3 (Level Registry) is eventually designed.

**Month 4, Video 13** — status: REVIEWED — no new detector required
- Two citation corrections caught and properly resolved before acceptance:
  1. "20-30 pips" was an ungrounded figure -- source only states "30 pips or so" (p.391). Corrected.
  2. "PD array" terminology does not appear anywhere in pages 387-396 and was retracted as an out-of-scope import from other ICT material, per the New Notes Protocol's rule against borrowing language from adjacent sources. Restated using only this video's own vocabulary.
- Disposition rationale: this video teaches a discretionary confluence heuristic -- classic (Type 1) divergence identifies where retail is positioned wrong; price then sweeps nearby liquidity (equal lows / old highs) and retests an existing bullish order block's mean threshold before reversing, often confirmed by hidden (Type 2) divergence on the reversal leg. No new price geometry is introduced. All structural elements (order blocks, mean threshold, liquidity pools, swing highs/lows) are already implemented. The source explicitly states indicators should only be used as a "contrasting view" of retail sentiment, never as a trade-entry basis (p.396) -- building a stochastic/momentum detector into smc.py would contradict this video's own stated premise.

**Month 4, Video 14** — status: LOCKED (this session)
- New detector: smc._measured_moves(ohlc, swing_highs_lows, max_peak_diff_pips=20.0, pip_size=0.0001, breakout_close=True, target_hit_close=True), wired via staticmethod. Fills the Tier 1 gap already logged ("smc.measured_moves() never built").
- Detects double top/bottom patterns and projects a 1:1 CONTINUATION target (not reversal) once price breaks out past the second peak. Confirmed against source's own worked example (target 0.7445, actual 0.7446, p.401).
- Real correction during build: initial implementation had no proximity/equality check between the two peaks, pairing arbitrary far-apart swings (285-572 pips on daily data). Fixed with max_peak_diff_pips=20.0, sourced to M4V14's own explicit 10-20 pip stop-run range (p.402: "usually we expect a 20 pip, 10-20 pip range run above an old high or 10-20 pip run below an old low for stop runs") and aligned to M4V11's established sweep_expected_max_pips=20.0 threshold.
- Two engineering assumptions documented in-code: (1) max_peak_diff_pips -- no numerical "relatively equal" threshold in source (p.397-398 uses qualitative language only); (2) outer-extreme anchor choice for MeasuredRange/ProjectedTarget -- source doesn't specify which near-equal peak to anchor to; max(Peak1, Peak2) for tops and min(Peak1, Peak2) for bottoms chosen because the outermost extreme is where the full liquidity cluster sits and only its breach unlocks the complete 1:1 projection.
- Validated specifically on 1H data (the timeframe M4V14 itself predominantly demonstrates on, p.402 explicitly contrasts hourly framework against 15M): full-year AUDUSD 2016 1H sample of 261 patterns detected, 245 confirmed breakouts, 217 target hits (88.6% hit rate).
- Visual Audit passed on a clean 1H double-bottom example (AUDUSD Sep 12-13 2016, 74.0 pip measured range, target 0.74198, target hit ~4 hours after breakout at 2016-09-13 13:00).
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).

**Month 4 Batch Summary (Videos 9-14)** — all six resolved this session:
- M4V9: LOCKED — smc._vacuum_blocks() built
- M4V10: LOCKED — smc._liquidity_voids() built
- M4V11: LOCKED — smc._liquidity_raids() built
- M4V12: REVIEWED — no new code; FVG boundary arithmetically identical to existing smc.fvg()
- M4V13: REVIEWED — no new code; discretionary confluence heuristic, no new price geometry
- M4V14: LOCKED — smc._measured_moves() built; fills the last Tier 1 gap in this batch

**Month 5, Video 1** — status: REVIEWED — no Layer 2 detector required
- **Part 1 (Accumulation/Distribution):** The four underlying/benchmark non-confirmation scenarios (pp.407-410) are already implemented by `smc._smt_divergence()`. Verified via literal code check. The video provides application context (daily-timeframe restriction, "program" framing as multi-day sequences), not new detection logic.
- **Part 2 (IPDA Data Ranges):** Genuine gap confirmed via repo-wide grep and `git log -S` (zero hits for IPDA, quarterly_shift, cast_forward, lookback_20, trading_days). This is a Layer 4 (MTF Alignment) temporal calibration utility, NOT a Layer 2 detector, as it computes anchor dates and trading-day windows, not price geometry.
- **Layer 4 Deferred Requirement Logged:** IPDA Look Back / Cast Forward windowing. Anchor = first trading day of most recently closed calendar month; look back 60/40/20 trading days to identify order flow + reference points; cast forward 20/40/60 mirroring the asymmetric day-count (p.420).
- **Explicit Build Flag (ENGINEERING ASSUMPTION):** When this gap is eventually built in Layer 4, "trading days" (p.413) must explicitly exclude exchange holidays (Christmas, etc.), not just weekends, since naive weekend-only exclusion will shift a 60-day window by a day or more. This must be an explicit engineering assumption, not silently absorbed.

**Month 5, Video 2** — status: LOCKED (this session)
- New detector: smc._swing_structure_hierarchy(ohlc, swing_highs_lows), wired via staticmethod.
- Detects intermediate-term highs/lows: a short-term swing (from swing_highs_lows) that is strictly greater (for highs) or strictly less (for lows) than both its immediately preceding and immediately following short-term swing -- sourced to page 443's "head and shoulders" framing. Deliberately stops at one level; does not recurse to a "long-term" tier, since the source only explicitly defines one level up from short-term.
- Real correction during build: an initial implementation plan wrongly claimed this detector filled the smc.macro_swing_grading() Tier 1 gap, based on surface name-pattern similarity ("swing grading" / "swing hierarchy"). Retracted after checking git log -S against the actual historical test target (verify_month3_video1.py), which confirmed macro_swing_grading() is an unrelated 5-quadrant Fibonacci retracement tool from Month 3. This is a genuinely new, separately named Tier 1 gap, now filled.
- Data Audit verified via explicit prev/curr/next arithmetic checks against real swing points (not just calendar-adjacent OHLC context) -- all 5 spot-checked examples confirmed correct on AUDUSD 2016 daily. Sparse detection (6 intermediate-term swings across the full year) consistent with the established pattern for swing-dependent detectors at daily timeframe.
- Two pieces of sourced content explicitly logged but NOT built: the directional-bias heuristic from pages 442-443 (watching whether intermediate-term highs/lows keep advancing or declining) is left as caller-side interpretation, not computed by the detector; the 3/6/12-month rolling high/low reference points from pages 433-434 are trivial caller-side .rolling().max()/.min() calls, not dignified with a dedicated function.
- Visual Audit passed: full-year AUDUSD 2016 daily chart with all 6 intermediate-term swings shown against their flanking short-term swings via structure brackets, confirming the "head and shoulders" relationship visually, not just arithmetically.
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).

**Month 5, Video 3** — status: REVIEWED (this session) -- no new Layer 2 detector, no code changes this video.
- (a) IPDA 60-Day Look Back Refinement: When all reference points inside the 60-day look-back are already swept, price is expected to reach outside that 60-day window for the next high/low (source pages 453-454). Appended to the existing M5V1 Layer 4 gap.
- (b) Open Interest Accumulation/Distribution: Rising open interest during a decline = central bank still providing liquidity to sellers; falling open interest during consolidation/decline = central bank reducing short exposure, a bullish signal (pages 460-465, sourced to Larry Williams). Logged under a NEW "data-infrastructure-blocked" category because it requires futures-contract data with an open-interest field (not derivable from standard forex OHLCV). Sourcing this data is a firm pending dependency, blocked on data infrastructure, not optional.
- (c) Buy Side / Sell Side of Curve: Reconfirms M4V7's Market Maker Buy/Sell Model concept (pages 466-467). No new information, no change to M4V7's existing Layer 4 blocked status.

**Month 5, Video 4** — status: REVIEWED (this session) -- no new Layer 2 detector, no code changes this video.
- Open Float [min_low, max_high] Output: The 20/40/60 trading-day rolling min/max is folded into the EXISTING M5V1 Layer 4 IPDA windowing gap as its concrete output definition, not a new gap entry. The video confirms this box mechanic visually across six consecutive worked months (Aug-Jan 2016/17), with real price action reaching the identified extremes during each cast-forward window.
- Concrete Reuse Confirmation: The worked USDCAD daily example (pages 480-483) explicitly labels a "Mitigation Block (Bearish)" on-chart. This corresponds directly to `smc._mitigation_blocks()` (M4V4), providing direct evidence that this video's application layer uses already-built detectors rather than just inferred reuse.
- Naming Disambiguation: Explicitly flagged to avoid future confusion: M5V2's "intermediate-term high/low" is swing-based (a short-term swing flanked by other short-term swings). M5V4's "intermediate-term open float" is a fixed 60 trading-day rolling min/max with no swing detection. They share terminology but are computed entirely differently and answer different questions.
- Open Interest: Reconfirms the existing TIER 5 (data-infrastructure-blocked) entry from M5V3 — no change needed to that entry.
- Directional Bias Heuristic: The heuristic of determining bias by tracking whether rolling highs or rolling lows are being breached is left as caller-side interpretation (same treatment as M5V2's bias heuristic) and is not built into any detector.

**Month 5, Video 5** — status: LOCKED (this session)
- New detector: smc._failure_swings(ohlc, swing_highs_lows, confirm_break_close=True, close_break=True), wired via staticmethod.
- Structural mirror-image counterpart to smc._breaker_blocks() (M4V5): same High-Low-High / Low-High-Low swing triplet scan, opposite comparison direction (High2 < High1 for bearish, Low2 > Low1 for bullish, vs. breaker's High2 > High1 / Low2 < Low1). Covers exactly the half of the triplet space that _breaker_blocks()'s own "continue" statement correctly discards per its M4V5 sourced definition -- that discard behavior is confirmed correct, not a bug, and was not changed.
- Does NOT modify _breaker_blocks() or _mitigation_blocks(). Both confirmed correct against their own original sourced definitions and left untouched.
- Output columns: FS (-1.0 bearish / 1.0 bullish), MidSwingLevel (the valley/peak retest trigger), StopLevel (wick extreme of the failed second swing), Invalidated.
- Three engineering assumptions flagged in-code and in the docstring: StopLevel anchor (inferred by symmetry with the breaker's stop logic on page 491 -- not separately sourced for this specific pattern), confirm_break_close, close_break (neither specified in source).
- Two real corrections caught during build, both logged for the record: (1) an initial diagram reading of the breaker's retest-trigger level (page 485) was wrong -- corrected via actual pixel measurement of the reference diagram, not re-argument; the retest trigger is the valley/short-term-low, not the originally-approached level. (2) A claimed "literal" code paste for _mitigation_blocks() was fabricated -- contained an impossible artifact inside a supposed AST extraction, and contradicted this project's own M4V4 lock record. Caught, root-caused (terminal output truncation during the original extraction, not deception), and re-extracted properly before being accepted.
- Mutual exclusivity with _breaker_blocks() verified at the correct granularity (triplet identity: same prev_swing/mid_swing/curr_swing tuple), after an initial test at output-row-position gave a false-positive overlap. Confirmed 0 overlap across AUDUSD 2016 daily (25 H-L-H + 25 L-H-L triplets) and Sep 11-18 2016 15M (50 + 50 triplets).
- Visual Audit passed: AUDUSD daily, bearish example (Aug 26 2016, MidSwing=0.75836, Stop=0.76920) -- High1/Low/High2 triplet points, activation, and invalidation all correctly and distinctly marked.
- Golden Master reconfirmed unaffected throughout (HRR=471, LRR=37, 11 transitions).

**Month 5, Video 6** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Macro-level environment classification (Trending vs. Consolidation) using directional correlation between 10-Year Treasury Note futures (ZN) and the Dollar Index (DXY).
- Sourced model (pages 499, 501): If ZN and DXY move in tandem (same direction), the market is in long-term consolidation/range-bound (across forex too). If they move inversely, the market is in a long-term directional trend.
- Disposition: Layer 4 (MTF Alignment / Macro Context) classification rule, not a Layer 2 price-geometry detector. Governs trade style (short-term/day trades vs. long-term position trades), not entry/exit geometry.
- Source-text anomaly logged, NOT resolved: p.501 narration reads "...creating a short-term low in December, and finally making its high in the first portion of December of this year" — self-contradictory as transcribed (a "first portion" event cannot follow a same-month low described as later). Visual check of the DXH17 chart (p.501) shows the described low positioned near the "Dec" axis label and a subsequent higher peak positioned nearer the "Jan 17" label — consistent with, but not proof of, a transcription slip (December/January). No correction applied to the source quote. Flagged as an unresolved source-text artifact for the record, not inferred or fixed.
- Logged as Layer 4 deferred requirement: Macro Trend Classification based on ZN/DXY sustained directional correlation over multi-week/month windows. No numeric threshold sourced for "tandem" vs. "inverse" — any mechanization requires an explicit ENGINEERING ASSUMPTION.
- Cross-video contradiction flagged in M5V9 regarding DXY/bond-price direction — see M5V9 entry.

**Month 5, Video 7** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Operationalizes the M5V6 macro classification by adding a TWO-instrument qualifying checklist: (1) ZN (10-Year Note futures) price making seasonal lows/highs consistent with the seasonal tendency, (2) DXY (Dollar Index) price cracking the tandem/consolidation correlation by moving inversely at that same moment. When both align, the condition is "qualifying" — an underlying positional trade is unfolding.
- The yield chart (TNX) is presented as a third visual confirmation in the video but is NOT an independent data source: by definitional inversion (M5V6 p.494: "Treasury Prices are inverted to its Yield"), a declining yield is the same information as a rising ZN futures price, viewed through its inverse representation. It is a redundant visual restatement of the ZN leg, not a third independent confirming instrument.
- Three historical examples worked: June 2015 (ZN lower lows / DXY lower highs → qualifying), June 2016 (ZN equal lows / DXY higher highs → qualifying), Nov 2016 pre-election (ZN lower high / DXY lower low instead of expected higher high → broken symmetry → confirmed the two-month dollar trending environment).
- Disposition: Layer 4 extension — the two-instrument ZN/DXY qualifying checklist (with yield as a visual restatement) is appended as an operational sub-rule to the existing M5V6 Layer 4 deferred gap. No new Layer 2 function warranted.
- Explicit sourced reuse confirmed (p.509): smc._smt_divergence() (M3V5) and triad_divergence() (M4V1) are called out verbatim by ICT as downstream qualification tools for this checklist. Both are already built and correctly wired.
- Open Interest (p.508): reinforces existing M5V3 TIER 5 deferred entry — no change to that entry.
- Source-text anomaly 1 (p.506) — Contextually resolved (inferred from M5V6 framework, not explicit in this video's own text): The narration applies the word "correlation" with two different implied reference points in the same paragraph without explicit signal. Exact quotes: "This is a cracking correlation." — then two sentences later — "That's a correct correlation there; therefore, it is a qualifying condition." Reading supported by context: "cracking" refers to the tandem/consolidation relationship breaking; "correct" refers to the inverse relationship (ZN down / DXY up) now being present. Both describe the same observable state. However, the word "correlation" shifts reference mid-paragraph without any marker, and a reader who does not carry the M5V6 tandem-vs-inverse framework forward will read this as self-contradictory. The resolution is plausible and well-reasoned but requires importing vocabulary from M5V6 that M5V7's own text never explicitly signals — it is an inference bridging a real gap, not a textual resolution.
- Source-text anomaly 2 (p.508) — NOT resolved: The narration states "In fact, we see a lower low" about the DXY in early November 2016. The DXH17 daily chart (p.508) shows DXY in a broad uptrend from August through January — making higher highs overall. The "lower low" must refer to a specific pre-election short-term swing dip relative to an October local reference, not the broad trend direction. However, the chart is too zoomed out at the printed resolution to pinpoint which prior candlestick swing is the stated reference point, and the text does not name it explicitly. Cannot confirm or refute from the static image alone. Logged as an unresolved reference ambiguity — same treatment as M5V6's December/January artifact.

**Month 5, Video 8** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Macro-level fundamental bias generation using Central Bank Interest Rate Differentials. The model pairs a high-yielding currency against a low-yielding currency to anticipate long-term institutional capital flows (funds seeking yield).
- Application checklist: (1) Select high-yield vs low-yield pair, (2) identify higher-timeframe (HTF) support/resistance, (3) look for smart money clues like seasonal tendencies or massive Open Interest reduction (short covering), and (4) USDX directional confirmation qualifies the setup.
- Checklist inference logic: The text simply states "USDX directional confirmation qualifies the setup." In the worked AUD example, this is visually demonstrated as DXY making higher highs while AUD fails to make lower lows. I am logging the linkage to SMT Divergence (M5V7) as a reasonable inference drawn from this worked example, not as an explicit textual claim made in M5V8 itself.
- Two historical examples provided: 
  - AUD/USD (Dec 2016): High-yield AUD vs low-yield USD. HTF support hit at 0.7150, Open Interest dropped sharply, and DXY made higher highs while AUD failed to make lower lows.
  - USD/JPY (late 2016): Higher-yield USD vs negative-yield JPY. JPY cash price hit a HTF bearish order block at 0.9800 and sold off, resulting in a massive USD/JPY rally.
- Disposition: Fundamental data layer / Macro Context. Does not define any new Layer 2 price geometry. It uses existing technical concepts (`smc.ob()`) to execute trades based on external fundamental bias.
- Source-text anomaly logged, NOT resolved: Numeric inconsistency in the source material regarding the Bank of Japan rate. The slide on p.516 explicitly states "US .75% vs. Japan -.15%", whereas the reference tables on both p.510 and p.511 state "BANK OF JAPAN -0.1 %". Logged as an unresolved source-text contradiction; no assumption made as to which figure is correct.
- TIER 5 deferred requirement logged: Central Bank Policy Interest Rate Data. Mechanizing this bias model requires an external data feed for global central bank interest rates. Direct search of the project (`fetch_macro_data.py` and the data directory) confirms this data is currently absent in any form. This is logged as a new, distinct Tier 5 infrastructure blockage (cross-referenced with, but separate from, the existing M5V3 Open Interest blockage).

**Month 5, Video 9** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Macro-level Intermarket Analysis. Uses the directional correlation between four major asset classes (Bonds, Commodities, Stocks, Currencies) to establish or confirm a long-term directional bias, explicitly replacing the need to parse traditional fundamental economic data.
- Key relationships defined:
  - Bonds vs Stocks: Positive correlation (move together).
  - Bonds vs Commodities: Inverse correlation (move opposite).
  - US Dollar vs Commodities: Inverse correlation (move opposite).
  - Asset-specific pairings: DXY inverse to Gold; Gold positive to AUD/NZD; Oil inverse to USDCAD; Dow positive to Nikkei; Nikkei positive to USDJPY.
- Disposition: Layer 4 (Macro Context) / Layer 5 (Fundamental Data). Entirely conceptual. Does not define any new Layer 2 price geometry. 
- CROSS-VIDEO SOURCED CONTRADICTION — logged, NOT resolved: A direct contradiction exists between this video and M5V6 regarding the relationship between the US Dollar and bond prices, confirmed in the explicit slide text of both videos.
  - M5V6, p.494: "US Dollar Can Rally When Yields Increase – Treasuries prices drop." (DXY UP = Treasury prices DOWN)
  - M5V9, p.522: "3. USDX UP = Stocks & Bonds UP" and narration (p.523) states "US dollar Index, if it's going higher or rallying, this is also seen with stocks and bonds moving up..." (DXY UP = Bond prices UP)
  - Open Hypotheses: (a) M5V6's claim is anchored specifically to the 10-Year-Note/DXY interest-rate-differential mechanism, whereas M5V9 presents a high-level, non-instrument-specific framework. They may not be describing the exact same functional relationship, but this is unconfirmed textually. (b) Because of this contradiction, M5V9's framework cannot automatically be treated as compatible confirmation alongside the M5V6-M5V8 framework. It must be resolved against real historical data at Layer 4 build time.
- Logged as Layer 4/5 deferred requirement: The framework states these macro correlations can have a lead/lag time of "6 to 12 months." Mechanizing this would require expanding the TIER 5 data blockage to include widespread external index/commodity data (Gold, Oil, CRB Index, Nikkei, Dow, Goldman Sachs indices) and requires explicit engineering assumptions to quantify what constitutes "alignment" across mismatched multi-month lead/lag windows.

**Month 5, Video 10** — status: REVIEWED — no new Layer 2 detector required
- Core concept: 40-year Seasonal Tendency charts as an additional macro confluence layer. Charts compile futures contract price action across all delivery months (data 1976–2015; blue line = 40-year avg; red line = 15-year avg) to produce a calendar-quarter roadmap of historical bullish/bearish tendency.
- Structural rule (sourced): Seasonal tendency charts are built on Futures contract prices. For dollar-paired FX currencies (e.g. USDCAD), the Futures seasonal signal must be explicitly inverted before applying to the FX pair. A bearish Futures seasonal for CAD dollar = bullish seasonal for USDCAD.
- Generalizable rule, logged for the first time in this project: For any USD-base currency pair (USDCAD, USDJPY, USDCHF — USD is first in the pair name), a bullish/bearish call on the non-USD instrument's own futures/spot price must be INVERTED before applying it to the forex pair direction. For USD-quote pairs (EURUSD, GBPUSD, AUDUSD), no inversion applies. Confirmed via direct search that this rule has never been named or generalized anywhere in smc.py or project_forensics.md prior to this entry. M5V8's USDJPY worked example (JPY futures bearish → USDJPY bullish, p.517) applied this same mechanism implicitly without stating it as a general rule — this is the first explicit, named statement of it.
- Integration with existing framework: Seasonal tendencies answer the "buy or sell" directional question for a given quarter and layer on top of the existing quarterly-shift framework (M4 curriculum). Together they constitute a "loaded deal" — quarterly shift timing + seasonal direction bias.
- Two worked examples provided:
  - USDCAD weekly (2008–2016): Sep–Dec seasonal for CAD Futures bearishness inverted to USDCAD bullishness. Strong tendency confirmed across most years; two weak years (2009–2010) explicitly noted by ICT as due to overriding bearish macro structure — sourced caveat in the text itself.
  - Crude Oil WTI weekly (2014–2016): Mar–Jun bullish seasonal visible even inside a long-term bear market (collapse from ~105). ICT notes the seasonal rally appeared all three years but adds "we do not force the trades."
- Explicit sourced caveat (p.529): "Seasonal tendencies are merely a proverbial roadmap of past performance, and they are not to be viewed as a panacea or be-all-end-all concept." ICT explicitly states seasonal tendency alone is insufficient when macro structure is opposed.
- Disposition: Layer 4 (Macro Calendar Overlay). No new Layer 2 price geometry. Does not require any new smc.py function.
- TIER 5 deferred requirement (a) — Seasonal Tendency chart data: The 40-year compiled Futures delivery-month price tendency files are a specialized multi-decade statistical product, external to this project and confirmed absent from the codebase via direct directory search. ICT references them as templates he "made available over the years" and states he will share all currency seasonal tendency charts in M5V11. Closing this gap requires sourcing or replicating the multi-decade compiled seasonal tendency dataset — it cannot be substituted with raw OHLCV data alone.
- TIER 5 deferred requirement (b) — Standard OHLCV data for USDCAD and Crude Oil (CL/WTI): Ordinary daily/weekly OHLCV price data for USDCAD and CL is confirmed absent from the project via direct search of fetch_macro_data.py and tests/test_data/. This is a standard data-infrastructure gap (same class as the ZN/ZB/DXY data already fetched in fetch_macro_data.py) and is distinct from the specialized seasonal tendency dataset in (a) — fetching OHLCV data would not substitute for (a).
- No source-text anomalies detected across pp.528–536.
- Cross-Video Confirmation: M5V11 p.537 slide states this rule directly and explicitly in ICT's own words ('The underlying currency market may move in tandem in a Forex pair or it may be inverted – based on the pairing with another currency'), upgrading it from an inference generalized from worked examples to a directly sourced general principle. See M5V11 entry.

**Month 5, Video 11** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Utilizing bearish seasonal tendencies to anticipate HTF bullish quarterly shifts. A bearish seasonal decline is framed as the mechanism that drops price into HTF discount arrays (e.g. bullish order blocks) to form the quarterly low.
- Asset of study: New Zealand Dollar (NZD / Kiwi). 
- Quote-inversion contrast (sourced): ICT explicitly reinforces the M5V10 inversion rule by contrasting NZD with CAD. Because NZDUSD is a USD-quote pair, the NZD Futures seasonal tendency applies directly to the forex pair in tandem, without inversion.
- Identified NZD Seasonal Windows: 
  - Bearish tendency: Mid-Feb to Mid-March; May; Mid-August.
  - Bullish tendency (Quarterly shift lows): March/April; June/July; Sept/Oct.
- Explicit sourced caveat (p.546): ICT uses the 2008 financial crisis to explicitly state that "larger big picture macro events are going to take precedence" over seasonal tendencies. Seasonal tendencies are overridden by macro wild-card events.
- Disposition: Layer 4 (Macro Calendar Overlay). No new Layer 2 price geometry. Does not require any new smc.py function.
- TIER 5 deferred requirement: Reinforces the exact same TIER 5(a) blockage logged in M5V10 (External Seasonal Tendency compiled data). No new infrastructure gap introduced.
- Minor sourced-completeness gap: p.542 narration mentions "a typical sell-off in the first week or so of January that goes down into February" — this window appears nowhere in the official p.543 recap list and is not marked on ICT's own annotated arrow chart (p.542-543), suggesting ICT himself treats it as secondary rather than a core window. Logged as mentioned-but-not-formalized, not as a core taught bearish window, so it isn't lost but also isn't overweighted.
- Minor window-precision inconsistency: p.543 restates the bearish windows twice in adjacent paragraphs with different extents: "...May is going to be an amazing sell-off, and you have August can create a nice sell-off as well..." vs., a few lines later, "...May into June for sell-offs and in August into September, giving us weak points to sell on." Logged as unresolved precision ambiguity, relevant to any future Layer 4 mechanization of exact window boundaries.

**Month 5, Video 12** — status: REVIEWED — no new Layer 2 detector required
- Core concept: "Ideal Seasonal Tendencies." This introduces a confluence technique for Layer 4 macro overlay: comparing the seasonal tendency of a foreign currency's futures contract directly against the seasonal tendency of the US Dollar Index (DXY) futures. An "ideal" setup occurs when the two tendencies are diametrically opposed (e.g., currency tendency is bullish while DXY tendency is bearish at the exact same time of year).
- Structural rule (sourced): ICT explicitly states that for an ideal setup to be tradable, both underlying instruments do *not* need to be in strong primary trends. "You only really need one" (p.561). For example, if CAD is in a primary uptrend but DXY is merely in long-term consolidation, the opposed seasonal tendencies are still sufficient to trigger a high-probability trade in the direction of the CAD trend.
- Exhaustive pairings provided: The video defines diametrically opposed seasonal windows for AUD/USD (Mar-May), NZD/USD (Mar-May), EUR/USD (Jun-Jul), GBP/USD (Mar-May), USD/CHF (Jun-Jul), USD/JPY (Mar-Apr), and USD/CAD (Mar-May).
- Disposition: Layer 4 (Macro Calendar Overlay). No new Layer 2 price geometry. Does not require any new smc.py function.
- Slide Orientation & Inversion Rule (Structural Support): The visual slide orientation itself (currency chart on left / DXY on right for AUD, NZD, EUR, GBP; DXY on left / currency on right for USDCHF, USDJPY, USDCAD) is visually consistent with the already-logged M5V10/M5V11 quote-inversion rule, confirmed via direct image inspection. This serves as circumstantial structural support for the rule's application, though it is not a direct sourced textual statement of the rule being applied here.
- TIER 5 deferred requirement: Expands the existing TIER 5(a) blockage (Specialized Seasonal Tendency chart data) to explicitly include the US Dollar Index (DXY) 15-year/40-year compiled seasonal tendency dataset.
- USDCHF trade-direction gap: Unlike the other six pairs, ICT never states the explicit trade conclusion for USDCHF (no "sell this pair" or "this pair should rally" statement — only the chart contrast description). He states: "So, we have a strong tendency for that to make a major turning point in the summer months for this particular pair, and again this would be an ideal scenario where the dollar is in a bearish market, primary downtrend, or if we are in a primary uptrend for the Swiss franc, this will be a good scenario to trade this as well" (p.559). Logged as mentioned-but-incomplete, not given equal explicit treatment to the other six pairs.
- GBP phrasing ambiguity (p.558): "For the British pound, we have the strongest tendency to make a low in March with a high forming in May, and if this is true, we would be seeing a high form between March and April with a low forming in May, and we do see that here". The second clause switches subject from GBP's own chart to DXY's chart without ever naming DXY/dollar index explicitly — the switch is only inferable from the paired chart layout and context. Logged as a genuine source-text articulation gap, not fully resolved by inference alone.

**Month 5, Video 13** — status: REVIEWED — no new Layer 2 detector required
- Core concept: Money Management and Risk Structuring for long-term position trading. The goal is extremely low drawdown to attract/manage investor funds, prioritizing steady annual growth (18-25%) over rapid compounding.
- Stop-loss management: Tolerates wide stops (e.g., 200 pips) targeting minimum 3:1 reward-to-risk. Explicitly instructs not to move stops to break-even early.
- Scale-out/Re-load: Take partial profits (halves/thirds/quarters) at logical resistance, then re-add position size on the next structural retracement.
- Hedging mechanic (sourced): To manage the psychological and P&L impact of deep open-profit drawdowns inherent to long-term trading, ICT advises trading closely correlated or inversely correlated pairs on lower time frames in the opposite direction of the primary trend retracement.
- Disposition: Review of existing Layer 6 (`risk_engine.py`) scaffolding against M5V13's sourced figures.
  - Match: The codebase's existing `RR_MIN = 3.0` directly agrees with M5V13's sourced 3:1 minimum reward:risk, cross-validating the figure rather than logging it as new.
  - CONFLICT (Unresolved): The codebase's `RISK_PCT_DEFAULT` (1.5%) and `RISK_PCT_MAX` (2%) represent risk-per-trade as a fraction of TOTAL account equity. M5V13 sources a materially different rule: risking 1% of only the 30%-allocated trading subset, which equals 0.3% of total account equity — roughly 5-6x smaller than what is currently coded. Logged as an unresolved conflict between existing code and this video's sourced figures.
  - Genuine new gap: No equity allocation cap (the 30% rule) exists anywhere in `risk_engine.py`.
  - Genuine new gap: No drawdown tracking or limit logic exists in the codebase.
  - Disambiguation: The `MIN_SWING_PIPS = 20` constant in code is a structural floor on OB-based stop swing size, completely unrelated to M5V13's 200-pip HTF stop-loss figure. They are distinct concepts and should not be conflated.
  - Prior Proposal Status: The `validate_liquidity_run()` function (proposed under M4V2) remains unbuilt. The `filter_rr()` function's 20-pip floor is the closest existing equivalent but is structurally distinct from the 40/75-pip liquidity-range proposal.
- No source-text anomalies detected across pp.562–571.

**Month 5, Video 14** — status: REVIEWED — no new Layer 2 detector required; new Layer 3 coordination gap logged
- Core concept: HTF PD Array Hierarchy. Introduces a priority-ordered lookup system for all ICT PD arrays relative to the equilibrium midpoint of a trading range on monthly, weekly, and daily charts. Does not introduce any new array type; explicitly reframes previously taught arrays as a ranked decision system.
- Sourced canonical hierarchy (confirmed verbatim from p.588 slide and image inspection):
  - Premium Arrays (above equilibrium, high-to-low rank): Old High\Low → Rejection Block → Bearish Orderblock → Fair Value Gap → Liquidity Void → Bearish Breaker → Mitigation Block
  - Discount Arrays (below equilibrium, low-to-high rank): Mitigation Block → Bullish Breaker → Liquidity Void → Fair Value Gap → Bullish Orderblock → Rejection Block → Old Low\High
- Traversal rule (sourced): When price is below equilibrium moving higher, search the premium list from the bottom (Mitigation Block) upward. When price is above equilibrium moving lower, search the discount list from the top (Mitigation Block) downward.
- Breaker Precedence Rule (sourced, p.589-590): A bearish or bullish breaker "takes precedence over everything on this list." Presence of a breaker below a void or gap means those higher arrays will likely remain unvisited. Strongest hierarchy constraint in the video.
- Time-frame applicability (sourced, pp.595-596): The identical hierarchy applies unchanged to monthly, weekly, and daily charts.
- M5V15 dependency: ICT explicitly defers the sole worked example to the next lesson — "In 6.2, that lesson will actually give a real practical example" (p.596), referencing a USDJPY position-trade example. M5V14 is the framework-only lesson; M5V15 is its application.
- Disposition: New Layer 3 coordination gap. Verified against smc.py directly:
  - Six of seven array types confirmed matched to existing smc.py functions: Rejection Block (`_rejection_blocks`), Order Block (`ob`), Fair Value Gap (`fvg`), Liquidity Void (`_liquidity_voids`), Breaker (`_breaker_blocks`), Mitigation Block (`_mitigation_blocks`).
  - "Old High/Low" as defined in M5V14 (pp.586-587: the most recent swing-range extremes that bound the current premium/discount trading range) has NO existing match. `smc.previous_high_low()` was checked directly and confirmed semantically different — it resamples to a fixed calendar period (e.g. prior day's high/low) and tracks breaks of it, not the swing-range-boundary concept M5V14 uses. No function in the codebase implements this range-bounding definition.
  - Layer 3 gap is two-part, not one: (a) a new primitive defining the current premium/discount range boundary (the "Old High/Low" swing-range framing) — structurally prior to everything else, since the hierarchy has no reference frame without it; and (b) the traversal/gating logic that walks the ranked list from that boundary inward. Both are unbuilt.
- No source-text anomalies detected across pp.572–596.

**Month 5, Video 15** — status: REVIEWED — no new Layer 2 detector required; new Layer 4 rule sourced; two implementation conflicts/gaps logged
- Core concept: Applied lesson (6.2) — the M5V14 hierarchy applied top-down to the Nov 2016 USDJPY ~1200-pip rally. Monthly → Weekly → Daily chart analysis. No new array types introduced; this is entirely an application of previously taught structures.
- Cascade Fallback Rule (sourced, pp.607-609 — first explicit statement in curriculum): If a daily PD array fails to hold price, expect price to travel to the weekly PD array equivalent. If the weekly fails, expect the monthly. "If you lose a level on a daily, don't be concerned. Just go out to a weekly chart and you'll see what they're reaching for." Confirmed via direct project-wide search: no cross-timeframe fallback logic exists anywhere in the codebase — not in smc.py, mtf_engine.py, state_machine.py, or any other file. Logged as a new sourced Layer 4 decision rule, completely absent from project.
- Quote-inversion restatement (sourced, p.601): ICT explicitly re-applies the USD-base pair inversion rule: "if Japanese Yen cash price is dropping, that means dollar prices are rallying, and if the dollar is the first in the name of the pair, Dollar Yen, that means when you're watching Dollar Yen price action, you're watching the advancement of dollar versus decline of the Japanese Yen." Direct sourced application of the M5V10 generalizable rule and M5V11 explicit statement. No new rule logged; cross-reference only.
- CONFLICT (Unresolved) — Multi-candle OB blending: M5V15 sources two distinct multi-candle OB rules: (a) two-candle blend example (p.603): "two consecutive down candles… that is a bullish order block when you blend both of the bodies together"; (b) highest-open selection from a cluster (pp.606-607): "the order block really begins at this candle's opening… the highest open of the three consecutive candles." `ob()` was checked directly and confirmed to select a SINGLE candle by segment extreme within the swing-to-break zone — bullish: `min_val = segment.min()` / `candidate_index = start + candidates[-1]`; bearish: `max_val = segment.max()` / `candidate_index = start + candidates[-1]`. It does not detect or blend clusters of consecutive same-colored candles and does not select the highest open from a multi-candle run. Logged as an unresolved conflict between sourced teaching and existing implementation.
- OB body vs. wick selection rule (sourced, p.604): When price has already passed through an OB area twice and no clean gap exists, the OB level is anchored to the candle's open, not the wick. "The reason why I'm using the open on this candle, not the wick, is because there's an absence of a gap… it's been passed through twice there."
- Genuine new gap — Breaker mid-body retest level: M5V15 (p.603) describes the breaker retest trigger as "middle of the body of the candle (the breaker), extend out in time, it would give you a level." `_breaker_blocks()` was checked directly: `BBBodyTop` = max(open, close), `BBBodyBottom` = min(open, close), `MidSwingLevel` = the swing-low between the two highs (a different structural concept per p.318, not a candle midpoint). No `(open+close)/2` midpoint field exists for breaker blocks. Note: `ob()` has `mean_threshold = (open+close)/2` for order blocks, but `_breaker_blocks()` has no equivalent. The mid-body retest level is unimplemented.
- USDJPY worked hierarchy (applied): Monthly rejection block / bullish OB (~99.00) as entry; weekly bullish OB (point 16) as re-entry; weekly bearish OB (point 13, open 118.61) as premium target; fair value gap (points 14-15) as intermediate target; daily OBs at 113.28 and 111.39 for scaling entries.
- Disposition: Layer 4 — Cascade Fallback Rule is new sourced logic, completely absent from project. Layer 2 — two implementation gaps logged against existing ob() and _breaker_blocks() detectors. No new detector function required.
- No source-text anomalies detected across pp.597–609.

**Month 5, Video 16** — status: REVIEWED — no new Layer 2 detector required; new Layer 5 (Rule Engine) logic logged
- Core concept: Stop Entry Techniques for Long-Term Traders. Introduces a mechanical entry trigger (Layer 5) for position trading, utilizing pending stop orders placed at the opening price of daily counter-trend candles to enter in the direction of the Monthly/Weekly trend.
- Buy Stop Entry Rule (sourced, p.610): When HTF order flow is bullish, wait for a daily down-close candle. Place a buy stop order exactly at the opening price of that down candle. 
- Sell Stop Entry Rule (sourced, p.612): When HTF order flow is bearish, wait for a daily up-close candle. Place a sell stop order exactly at the opening price of that up candle.
- Continuous Scaling (sourced, p.611): The pending order is rolled forward to the opening price of every new successive counter-trend candle until triggered.
- DISTINCT Concept vs Order Block Theory: M5V16's "every down candle promotes new buying opportunity" mechanic is a confirmed distinct concept from the formal `ob()` detector. Verification confirms `ob()` selects a single anchor candle per structural swing break (via `min_val`/`max_val` on the swing-to-break zone) and does NOT flag every successive down candle as a separate order block. This is a standalone, repeatable daily-execution technique, not a restatement of the formal Layer 2 OB detector.
- Stop-Loss Dependency (sourced, pp.616-617): ICT explicitly defers the stop-loss placement rules for these entries to the next lesson ("lesson eight"). Confirmed via direct search that M5V17 is currently unreviewed and correctly matches this dependency.
- Disposition: New Layer 5 (Rule Engine) gap. The raw candle Open is confirmed trivially accessible project-wide (`ohlc["open"]` / the `_open` array) — there is no data gap. However, the rule logic itself is entirely missing. Confirmed via direct search that Layer 5 (`state_machine.py`) and Layer 6 (`risk_engine.py`) both have zero existing entry-trigger, order-placement, or stop-order logic.
- No source-text anomalies detected across pp.610–622.

> `[CORRECTION ADDENDUM 1]: A prior verification check correctly confirmed M5V17 was unreviewed, but never checked whether M5V17's content would match the deferred "lesson eight" (stop-loss placement) topic. It does not — M5V17 is "lesson 7.2" (Limit Order Entries), a sibling technique, not the stop-loss lesson. "Lesson eight" remains pending in a later, still-unreviewed video.`

> `[CORRECTION ADDENDUM 2]: In M5V17, ICT issues a retroactive self-correction to the stop-entry rules logged here: "I should have mentioned this as well when we talked about the stop orders, but you're not just simply going in based on the candle itself by itself... You have to blend the PD arrays on the daily chart as well" (p.624). The M5V16 rule is under-qualified as originally stated — not every counter-trend candle is a valid trigger, only ones aligned with an actual daily PD array.`

> `[DEPENDENCY CLOSED]: The deferred stop-loss methodology for these long-term entry techniques was delivered in Month 5, Video 18 (Lesson 8). See the M5V18 entry for the IPDA 20/40-day trailing stop rules.`

**Month 5, Video 17** — status: REVIEWED — no new Layer 2 detector required; new Layer 5 logic logged; one terminology artifact resolved
- Core concept: Limit Order Entry Techniques for Long-Term Traders. Introduces a deep-discount/premium limit entry mechanic for position trading (Lesson 7.2), utilizing pending limit orders placed at the closing price of daily counter-trend candles.
- Buy Limit Entry Rule (sourced, p.623): When HTF order flow is bullish, wait for a daily down-close candle. Place a buy limit order exactly at the closing price of that down candle. 
- Sell Limit Entry Rule (sourced, p.624): When HTF order flow is bearish, wait for a daily up-close candle. Place a sell limit order exactly at the closing price of that up candle.
- RETROACTIVE SELF-CORRECTION — Layer 3 PD Array Gating Rule (sourced, p.624): ICT explicitly retroactively corrects the M5V16 stop-entry rules and applies the same gating to these limit entries: "I should have mentioned this as well when we talked about the stop orders, but you're not just simply going in based on the candle itself by itself... You have to blend the PD arrays on the daily chart as well." This states plainly that the M5V16 rules were under-qualified. Entries are only valid when blended with daily PD arrays. Reinforces the Layer 3 coordination/gating gap previously logged in M5V14.
- Pip-count structure (sourced, pp.626-627): The USDJPY applied example tracks exactly six limit-entry sequential targets: an 1800-pip move sourced from prose (distance from the September low to the weekly target), followed by five chart-labeled annotations for subsequent entries (980, 785, 600, 500, and 360 pips).
- Judas Swing terminology (sourced, p.625): The text refers to "the Judas Swing; it'll open, make the high in London, and then sell oﬀ..." (Note: The source PDF read "Judah swing" due to a document preparation typo, directly confirmed and corrected by C.Slim; this is not an open anomaly). CAUTION: As this is the first appearance of "Judas Swing" terminology in the Month 5 review, this carries forward the project's existing known-hazard warning (Pattern 4 in the operating guide) — if/when Judas Swing logic is ever built, it must be kept architecturally distinct from the existing Market Protraction detection inside `state_machine.py`, to avoid conflating the two distinct concepts.
- Disposition: New Layer 5 (Rule Engine) gap. The raw candle Close is trivially accessible (`ohlc["close"]`), but the limit-order execution logic is entirely missing. Confirmed via direct project search that Layer 5 (`state_machine.py`) and Layer 6 (`risk_engine.py`) both have zero existing limit-order logic.
- No other source-text anomalies detected across pp.623–627.

**Month 5, Video 18** — status: REVIEWED — no new Layer 2 detector required; new Layer 6 / Layer 5 logic logged; unresolved bearish threshold anomaly logged
- Core concept: Position Trade Management (Lesson 8). Delivers the deferred stop-loss placement and trailing rules for the long-term entries taught in M5V16 and M5V17, utilizing IPDA 20/40-day lookback windows.
- Initial Stop Placement (sourced, pp.629-630): Initial protective stops are placed beyond the lowest low (for longs) or highest high (for shorts) of the last 40 trading days. Fulfills the pending M5V16 dependency.
- Dynamic Trailing Stop Rule (sourced, p.636): The trailing stop logic shifts dynamically based on trade progress toward the HTF PD array target. Prior to reaching the target threshold, the stop trails the 40-day extreme. Once price crosses the threshold, the stop tightens to trail the 20-day extreme.
- ASYMMETRIC THRESHOLDS (Unresolved): These rules are presented as a mirrored bullish/bearish pair, but the stated thresholds for when to shift from the 40-day to the 20-day lookback are asymmetric and unresolved:
  - BULLISH Threshold (50% Confirmed): The prose contradicts itself (mentioning both 50% and three-quarters), but the worked numerical example on p.636 clearly resolves the ambiguity: "once price trades through this here(equilibrium), we start looking back 20 trading days... prior to equilibrium or halfway move, you want to be 40 trading days back."
  - BEARISH Threshold (75% Unconfirmed): The bearish prose (pp.631-632) clearly and consistently states "three-quarters of the range" twice, with NO mention of 50% anywhere nearby and NO worked numerical example provided to resolve it. 
  - Net finding: Do not harmonize these. The 50% shift is only confirmed for bullish setups. The bearish 75% threshold remains an open, unconfirmed question.
- Risk Sizing (sourced, p.629): Long-term position trades should risk "no more than one percent" of account equity. No mention of the "30% allocation subset" (the unresolved conflict from M5V13) appears anywhere in this lesson, leaving that conflict open.
- Disposition: New Layer 6 (Risk Management) and Layer 5 (Rule Engine) gap. The dynamic state-management logic required to track a trade's progress against a HTF target and shift the IPDA lookback window mid-trade is completely absent from the project. Furthermore, deriving the 20/40-day extremes themselves is a concrete extension of the still-unbuilt IPDA windowing Layer 4 gap originally logged in M5V1 (which requires explicit holiday-calendar engineering for "trading days").
- No other source-text anomalies detected across pp.628–636.

**Month 5, Video 1-18 Batch Summary** — all eighteen resolved (Month 5 complete):
- M5V1: REVIEWED — no Layer 2 detector; IPDA windowing logged as Layer 4 deferred requirement
- M5V2: LOCKED — smc._swing_structure_hierarchy() built
- M5V3: REVIEWED — no new code; Open Interest logged as TIER 5 data-infrastructure-blocked
- M5V4: REVIEWED — no new code; Open Float folded into existing M5V1 Layer 4 gap
- M5V5: LOCKED — smc._failure_swings() built
- M5V6: REVIEWED — no new code; Macro Trend classification logged as Layer 4 gap; transcription artifact explicitly flagged
- M5V7: REVIEWED — no new code; ZN/DXY qualifying checklist appended to M5V6 Layer 4 gap; two source-text anomalies logged (one contextually resolved, one unresolved)
- M5V8: REVIEWED — no new code; Central Bank Interest Rates logged as new TIER 5 data-infrastructure-blocked; Japan rate numeric inconsistency logged
- M5V9: REVIEWED — no new code; Intermarket Analysis logged as Layer 4/5 gap; CROSS-VIDEO contradiction regarding DXY/bond-price direction logged
- M5V10: REVIEWED — no new code; USD-base pair quote-inversion rule named for first time; seasonal tendency data and USDCAD/CL OHLCV both logged as distinct TIER 5 gaps
- M5V11: REVIEWED — no new code; M5V10 quote-inversion rule explicitly confirmed; two minor source-text precision ambiguities logged; TIER 5(a) blockage reinforced
- M5V12: REVIEWED — no new code; Ideal Seasonals matrix logged; USDCHF direction unstated; GBP/DXY phrasing overlapping; TIER 5(a) expanded to DXY seasonals
- M5V13: REVIEWED — no new code; Risk rules vs. risk_engine.py compared; 3:1 RR matched; 0.3% vs 2% risk sizing conflict logged; 30% allocation gap noted
- M5V14: REVIEWED — no new code; HTF PD Array Hierarchy sourced and logged; Layer 3 gap confirmed two-part (range-boundary primitive + traversal logic, both unbuilt); 6-of-7 array detectors confirmed in smc.py; Old High/Low range-bounding unmatched
- M5V15: REVIEWED — no new code; Cascade Fallback Rule logged as new absent Layer 4 logic; OB blending conflict logged vs. existing ob() logic; Breaker mid-body retest gap logged vs. _breaker_blocks()
- M5V16: REVIEWED — no new code; Stop Entry technique logged as new absent Layer 5 logic; confirmed distinct from existing ob() logic; no data gap on Open price
- M5V17: REVIEWED — no new code; Limit Entry technique logged as new absent Layer 5 logic; retroactively corrected M5V16 gating logic; Judas Swing terminology noted

## 2. KNOWN CORE LIBRARY DEFICIENCIES (new section, five tiers)

TIER 1 — Never built, no code exists anywhere in repo history:
- smc.macro_swing_grading()
- ~~smc.measured_moves()~~ **BUILT this session** as smc._measured_moves() (M4V14)
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

TIER 5 (DATA-INFRASTRUCTURE-BLOCKED) — Firm pending dependencies blocked by missing data feeds:
- Open Interest Accumulation/Distribution (M5V3) — Requires futures-contract data with an open-interest field to detect central bank hedging (not derivable from standard forex OHLCV). Sourcing this data is a committed future requirement.

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
- **`_vacuum_blocks(ohlc, ob_df, close_fill=True, close_invalidation=True)`** | Detects breakaway gap vacuum blocks driven by volatility events. | Built: Month 4 Video 9 | Status: Built from scratch
- **`_liquidity_voids(ohlc, consolidation_df, swing_highs_lows, fvg_df, close_fill=True)`** | Detects aggressive displacement runs (liquidity voids) from consolidation exit to terminating opposing swing. | Built: Month 4 Video 10 | Status: Built from scratch
- **`_liquidity_raids(ohlc, swing_highs_lows, sweep_expected_min_pips=10.0, sweep_expected_max_pips=20.0, sweep_reject_threshold_pips=25.0, pip_size=0.0001, close_revert=True)`** | Detects swing-level stop raids — wick violations with depth classification and reversion check. | Built: Month 4 Video 11 | Status: Built from scratch
- **`_measured_moves(ohlc, swing_highs_lows, max_peak_diff_pips=20.0, pip_size=0.0001, breakout_close=True, target_hit_close=True)`** | Detects double top/bottom measured-move projections; 1:1 continuation target above/below the equal extremes. | Built: Month 4 Video 14 | Status: Built from scratch
- **`_swing_structure_hierarchy(ohlc, swing_highs_lows)`** | Detects intermediate-term highs/lows via flanking short-term swing comparison. | Built: Month 5 Video 2 | Status: Built from scratch
- **`_failure_swings(ohlc, swing_highs_lows, confirm_break_close=True, close_break=True)`** | Detects failure swings -- structural mirror of _breaker_blocks() covering the non-swept half of the High-Low-High/Low-High-Low triplet space. | Built: Month 5 Video 5 | Status: Built from scratch


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
- **Layer 2 (Detection)**: Heavily implemented in `smc.py`. **Month 4 curriculum fully covered through Video 14 (~14 videos total).** Month 5 Video 1-5 batch complete this session: 2 new detectors built (`_swing_structure_hierarchy`, `_failure_swings`), 3 videos reviewed with no new code required (M5V1, M5V3, M5V4). All M4 and M5 detectors wired via module-level staticmethod monkey-patch. Remaining Layer 2 gaps: smc.macro_swing_grading() (Tier 1), smc.monthly_range_ob() (Tier 1), M4V7 (deferred to Layer 4), M4V2/M4V3 HTF-alignment concepts (deferred to Layer 4).
- **Layer 3 (Level Registry)**: Not started. No scaffolding exists. Known simplification: all current detectors are single-formation, single-resolution — no level is modeled as revisitable after first fill/invalidation (see M4V12 reusable-level finding).
- **Layer 4 (MTF Alignment)**: Scaffolding exists (`mtf_engine.py`, `mtf_demo.py`). Blocking: M4V2 pip-range minimum, M4V3 HTF OB selection, M4V7 Reclaimed OB "major swing" classification, and M5V1 IPDA Look Back / Cast Forward windowing utility (requires explicit holiday-calendar engineering assumption for "trading days" count); includes M5V3 refinement: when all reference points inside the 60-day look-back are swept, expect price to reach outside that window for the next high/low — all are Layer 4 dependencies deferred from their respective video reviews.
- **Layer 5 (Rule Engine)**: Scaffolding exists (`state_machine.py`).
- **Layer 6 (Risk Management)**: Scaffolding exists (`risk_engine.py`).
- **Layer 7 (Execution)**: Not started / Minimal (some logic exists inside `_hns_signals` and `_phantom_signals`, but no standalone execution module).

## 11. RECENT SESSION HISTORY
1. **Sep 22, 2026**: Month 5 Video 1-5 batch review — built _swing_structure_hierarchy and _failure_swings; reviewed M5V1, M5V3, M5V4 (no new code). IPDA windowing and Open Float logged as Layer 4 deferred requirements; Open Interest logged as TIER 5 blocked. Outcome: Completed.
2. **Aug 31, 2026**: M4V9-V14 batch review — built _vacuum_blocks, _liquidity_voids, _liquidity_raids, _measured_moves; reviewed M4V12 (no new code) and M4V13 (no new code); M4V14 LOCKED. Month 4 curriculum fully covered through Video 14. Outcome: Completed.
2. **Aug 7, 2026**: Add all PDFs, HTMLs, and images (except 308MB docx) to Git. Outcome: Completed.
3. **Aug 7, 2026**: Add month4 resources, MACRO test data, verify script, and update extract_pdf_images. Outcome: Completed.
4. **Jun 9, 2026**: fix: Implemented Gaps 3, 4, 5 — Neutral bond tolerance, comprehensive POI gate, and Triad+SMT chaining. Outcome: Completed.
5. **Jun 9, 2026**: fix: Triad divergence gap fixes — resolution-agnostic docstring + POI gate (M4V1). Outcome: Completed.
6. **Jun 9, 2026**: feat: Add missing 5-Year Note (ZF) data and integrate into Triad analysis. Outcome: Completed.

## 12. ANYTHING FLAGGED AS UNCERTAIN
- **Golden Master Test Integrity**: RESOLVED. `verify_step2.py` confirmed passing (HRR=471, LRR=37, 11 transitions) as of 2026-08-07. `verify_audusd_sept.py` is confirmed non-canonical — it called a function that never existed in the repo.
- **Video 8 Market Protraction Audit**: Partially resolved. `verify_market_protraction.py` restores the original script structure and runs clean (61 signals, EURUSD 15M last 3000 candles). However, the output is UNVALIDATED — no prior baseline exists. `verify_video8.py` (Multi-Timeframe) is untouched and continues to pass.
- **Orphan Scripts**: There are over 100+ scripts (`patch_*.py`, `rewrite_*.py`, `debug_*.py`, `diag_*.py`) in the root directory. It is completely UNCERTAIN which of these are still relevant and which are dead code.
- **Exact Gatekeeper Lock Dates**: UNKNOWN. The exact timestamps for when videos 1-3 were "locked" by the gatekeeper are not tracked in easily accessible `.md` logs in the root.


---
*Last Updated: 2026-09-01*
