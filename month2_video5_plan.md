# Month 2, Video 5: "How To Mitigate Losing Trades Effectively"

Following the **ICT New Notes Protocol**, I have completely re-processed the updated PDF from Pages 82 through 91 as a fresh extraction.

---

## Step 1 — Extract the Exact Definitions (Verbatim)

**1. The Initial Stop & Loss:**
> *"assuming that we took that long position and our stop was below the mean threshold and it hit our stop... let's assume for a moment that our maximum leverage and risk on the trade would be at a full two percent."*

**2. The Re-evaluation (Secondary OB):**
> *"if the trade hasn't completely unraveled just because it swept us out below the mean threshold... we can take a look at that new order block that forms... This time, our stop loss is going to actually be below the order block that we’re framing our trade around."*

**3. The Mitigation Math (Halving Risk):**
> *"if the initial loss was 2% of the equity base, this trade again will be 1% of the equity base in total risk. ... why would any trader think like a fool and not dial back their leverage if they take a losing trade?"*

**4. The Recovery Target:**
> *"So if we have one percent at risk, we're already at one percent return. So we got half of our initial loss back in open profit. Once we get one more standard deviation... we're already at two percent mitigated. In other words, our losing trade that we just had using half of the initial risk is already mitigated."*

**5. The Mitigation Exit:**
> *"Once the market provides you R2 or the mitigation of your initial loss, you want to lock that in... either you take it off once you mitigate your loss entirely when you get R2... or you want to trail the stop loss up to where you can no longer lose back below open profit"*

---

## Step 2 — Identify What It Measures

This module measures two distinct things:
1. **Structural Re-entry:** It identifies a scenario where a primary stop loss (placed tight at the Mean Threshold) is swept, but the broader anchor OB holds. Price then forms a Secondary OB, validating a second entry.
2. **Risk Mitigation Mechanics:** It calculates the R-multiple required on a subsequent trade (with halved risk) to fully recover an initial loss, targeting a 2R recovery threshold.

---

## Step 3 — Cross-Reference Against Existing Architecture

- **`risk_engine.py` (Layer 6):** The risk mitigation math belongs here. We currently have `calc_expectancy` and `calc_position_size`.
- **`state_machine.py` (Layer 4):** Our current state machine uses a strict 8-candle cooldown (`cooldown = 8`) preventing rapid re-entries. It also defaults to placing stops at the Daily OB Floor (`use_daily_ob_stop = True`), rather than the tight Mean Threshold described in the initial trade.

---

## Step 4 — Identify What is New vs. What is a Refinement

- **New Concept 1 (Math):** A **Loss Mitigation Calculator** that dynamically halves risk on consecutive losses and tracks the R-multiple required to return to breakeven.
- **New Concept 2 (Structure):** A **Re-Entry State** that bypasses the 8-candle cooldown when a secondary OB forms inside an unbroken anchor.
- **Refinement:** Adjusting the initial protective stop to the Mean Threshold.

---

## Step 5 — State the Build Plan

Because this module blends both risk math and structural state execution, I have separated the build plan into two phases. Phase 1 is the mandatory math layer. Phase 2 is the optional structural layer.

### Phase 1: Risk Mitigation Engine (Mandatory)
1. **`risk_engine.py`:** Add `calc_mitigation_recovery(initial_risk_pct, reentry_risk_pct)` returning the required R-multiple to breakeven.
2. **`visualize_month2_video5.py`:** Create a Plotly dashboard highlighting the "Mitigation Curve", contrasting the safe 1%-per-R climb to 2R against the dangerous "doubling down" approach.
3. **`verify_month2_video5.py`:** Assert that a 2% initial loss requires exactly 2.0R to recover when risk is halved to 1%.

### Phase 2: State Machine Rewiring (Optional)
If we implement the structural trade context from the video, we must:
1. Edit `state_machine.py` to add a `use_mean_threshold_stop` parameter to force the tighter initial stops.
2. Build an exception into the `cooldown` logic to allow a Re-entry Signal if price taps a newly formed Secondary OB after a stop-out.

---

## Open Questions for C.Slim

> [!IMPORTANT]
> **Q1: Implementation Scope**
> Should I implement **Phase 1 only** (building the Mitigation Calculator and Dashboard, keeping our `state_machine.py` strict and untouched, just like we did for Video 4)? 
> Or do you want me to also build **Phase 2** (rewiring the state machine to actively trade these Secondary OB re-entries on the charts)?
