# Month 2, Video 4: "No Fear of Losing" — Updated Implementation Plan

I have now fully extracted the PDF text and rendered the chart screenshots on Pages 75-81. This review reveals that Video 4 is **not just a math lesson**. Before diving into the Expectancy Matrix, ICT provides specific structural refinements for trade framing in the charts on Pages 76 and 77.

---

## 1. Structural Refinements (Pages 76–77)

The charts and surrounding text define the "simple trade idea" used to frame the 5:1 R:R model:

**A. Mean Threshold Invalidation (Closing Basis):**
> *"The middle of that down candle, we're going to be using that as a mean threshold. In other words, we don't want to see that violated on the closing basis."*
Currently, our `turtle_soup_signals` uses a hard, intra-candle protective stop (`ts_ob_stops`). A closing-basis stop requires new logic: monitoring if the *close* of a candle falls below the mean threshold, allowing intra-candle wicks to pierce it.

**B. Fixed 20-Pip Stop Distance:**
> *"Using 20 pips as the trade stop loss easily frames reward multiples..."*
Currently, we derive stop distances dynamically from the OB size (fractal refinement). This suggests standardizing risk to a fixed 20 pips for these setups.

**C. Target Projection (+20 pips over Old High):**
> *"Nearly an old high(at point 1 in screenshot above), 20 pips above it, gives us a nice objective..."*
Currently, our `ts_tgt_far` targets are set exactly to the liquidity pool (old high). This refinement adds a `+ 20 pips` (`+0.0020`) extension beyond the old high to clear the buy stops.

**D. Secondary Bullish Order Block:**
> *"...there's a mean threshold and a hypothetical long entry on the secondary bullish order block."*
This introduces a 2-stage entry: price hits the Primary OB, but entry waits for a Secondary OB to form within the retracement.

---

## 2. The Expectancy Matrix (Pages 78–81)

The second half of the module is the core capital management lesson. ICT runs 6 mathematical scenarios showing how accuracy, risk%, and R:R produce returns on a $5,000 account.

| Scenario | Accuracy | Risk/Trade | R:R | Net Profit | Monthly % |
|----------|----------|-----------|-----|------------|-----------|
| 1 | 30% | 2% | 3:1 | $200 | 4% |
| 2 | 30% | 2% | 5:1 | $800 | 16% |
| 3 | 40% | 2% | 5:1 | $1,400 | 28% |
| 4 | 50% | 2% | 5:1 | $2,000 | 40% |
| **5 (Optimal)** | **50%** | **1%** | **5:1** | **$1,000** | **20%** |
| 6 | 50% | 0.5% | 5:1 | $500 | 10% |

**Position Sizing Formula:** `dollar_per_pip = (account × risk%) / stop_pips`

---

## Open Questions for C.Slim

Because Video 4 introduces both structural execution rules and capital management math, I need your direction on how deep to build this.

> [!WARNING]
> **Q1 — Structural Refinements: Code them or treat as context?**
> The text says: *"Okay folks, we're going to give a brief overview on framing a trade just for the context of this discussion."*
> Do you want me to update `state_machine.py` and `turtle_soup_signals` to implement the Target Projections (+20 pips), Secondary OB entries, and Closing-Basis Stops? Or are these just observational context for the expectancy math, meaning I should leave the state machine untouched?

> [!IMPORTANT]
> **Q2 — Expectancy Matrix: Operative or Documentation?**
> Should the expectancy matrix be an operative calculator function (`calc_expectancy`) in `risk_engine.py` that takes parameters and returns projections, or just a documentation constant? *(I recommend building the calculator).*

> [!IMPORTANT]
> **Q3 — Position Sizing Function:**
> Should I add the `calc_position_size()` function to `risk_engine.py`? *(I recommend Yes).*

> [!IMPORTANT]
> **Q4 — Visualization:**
> What should the Video 4 dashboard (`ICT_MONTH2_VIDEO4.html`) display?
> **Option A:** A statistical dashboard showing the Expectancy Matrix as a bar chart and table.
> **Option B:** A price chart highlighting the Target Projections and Secondary OBs (if we implement Q1).

---

## Proposed Changes (Assuming Math-Only Implementation)

If you decide the structural rules are just context (answering NO to Q1), the plan is:

1. **`risk_engine.py`:** Add `EXPECTANCY_SCENARIOS`, `calc_expectancy()`, and `calc_position_size()`.
2. **`verify_month2_video4.py`:** Add checks to validate the math against the 6 scenarios and run Golden Master regression.
3. **`visualize_month2_video4.py`:** Build a 2-pane statistical Plotly dashboard (Option A for Q4).

*Please advise on Q1-Q4 before I write any code.*
