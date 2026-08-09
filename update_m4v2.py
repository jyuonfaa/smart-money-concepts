import re

with open('cslim/project_forensics.md', 'r', encoding='utf-8') as f:
    text = f.read()

insertion = """**Month 4, Video 2** — status: Reviewed — no new detector function required; one actionable risk-filter parameter identified for Layer 6 (pip-range minimum for trade validity)
- Core content: External Range Liquidity vs. Internal Range Liquidity, and MTF cascade (Monthly -> Weekly -> Daily -> 4H -> 15M) for framing entries at internal range liquidity (order blocks) with exits at external range liquidity (old highs/lows). No new smc.py function required — uses only existing FVG, OB, and liquidity detectors.
- Sourced quote (pages 288-289): "...if the high in between the range low and the high that retraced from, if it's only 20 pips, is that a trade that would be viewed as something that you would take? In my opinion, no, because the range is only 20 pips... But the precursor is you want to look at price swings that offer about 40 pips. If you can see anything at 40 pips or higher in looking for a retracement to go long on that, that gives you a reasonable first profit objective... So if you're looking for say you're a trader, you want to have nothing less than 50 pips, okay, well that's great... So what you do is you want to look for ranges that have 50 pips or more, preferably about 75 to 80 pips is perfect, because even if it doesn't even break the range and go up above this old high, it still gives you the opportunity to get that 50 pips."
- Note: ICT's own guidance isn't a single fixed number — ranges from "reasonable" at 40 pips up to "perfect" at 75-80 pips. Any implementation should treat this as a preference range, not one hard threshold.
- Proposed (NOT implemented): risk_engine.py function validate_liquidity_run(entry_price, target_price, min_pips=40.0, optimal_pips=75.0, pip_size=0.0001) — rejects trades where the entry-to-target range falls below min_pips. Pending your decision on whether to build this now or defer.

"""

text = text.replace("## 2. KNOWN CORE LIBRARY DEFICIENCIES", insertion + "## 2. KNOWN CORE LIBRARY DEFICIENCIES")

with open('cslim/project_forensics.md', 'w', encoding='utf-8') as f:
    f.write(text)
