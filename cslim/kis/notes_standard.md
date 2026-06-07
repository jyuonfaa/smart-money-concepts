# ICT NOTES STANDARD — HOW TO READ AND APPLY THE PROJECT NOTES

The ICT Mentorship 2016 notes are the specification. Every detector, every signal, every condition in this codebase must be derived from those notes exactly. General technical analysis knowledge is not a substitute. If ICT's definition conflicts with standard TA, ICT wins.

**The four conditions and their exact coupled tools — never mix these up:**
- Consolidation → Equilibrium (50%) and OTE zone (62–79%). Boundaries defined by candle **bodies** (open/close), never wicks.
- Expansion → Order Blocks. Confirmed by a candle body closing **beyond** the consolidation boundary.
- Retracement → FVG and Liquidity Voids. Use `smc.fvg()` — do not rebuild.
- Reversal → Stop Runs only. Wick pierces swing high/low, body closes back inside. Use `smc.swing_highs_lows()` — never `smc.liquidity()`.

**State transition rules — these are hard gates, not probabilities:**
- Consolidation → Retracement: impossible
- Consolidation → Reversal: impossible
- Every move out of consolidation must be classified as Expansion first

**When implementing any ICT concept:**
1. Find the exact quote from the notes that defines it
2. Identify what the code must measure based on that quote
3. Only then write the implementation

**When stuck on any ICT concept:**
Find an open-source TradingView Pine Script indicator for that concept and translate the logic to Python. Do not invent the logic from scratch.

**Non-negotiable implementation rules derived from the notes:**
- Candle bodies only for consolidation boundaries — open/close, not high/low
- Percentile-based thresholds for displacement and FVG filters — not fixed ATR multipliers
- No lookahead — signals use only data available at candle close
- Skip Sunday candles (dayofweek == 6) in all swing confirmation logic
- All zones and target lines anchor to conf_ts — never to chart start
- Maximum 3 active OTE zones displayed simultaneously (Rule of 3)
- smc library integer outputs — FVG direction is `1` (bullish) or `-1` (bearish), never strings

**If the notes do not define it, do not build it.**
