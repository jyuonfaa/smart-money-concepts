# Lessons Learned Registry — C.Slim ICT Intelligence Suite

During the institutional development of this suite, we solved several critical bugs that must never be repeated. Below is the categorized engineering registry.

---

### Category A — Data & Slicing Lookback Bugs

*   **The Bug:** When building a focused visualizer (e.g. Month 2 Video 2), slicing the input dataframe to the focus window (`2016-08-03` to `2016-08-12`) *before* running detectors (like `swing_highs_lows` or `detect_reversals`) filters out all historical candles. This prevents swings from confirming, causing signals to fail silently.
*   **The Lesson:** Always run detectors, state machines, and indicator calculations on the **full dataset** first. Only slice the resulting DataFrames to the focus window *at the very end* inside the plotting routine.

---

### Category B — Direction-Correct Stop-Loss Anchoring

*   **The Bug:** Setting refined stop-losses to `ob_row['Bottom']` regardless of setup direction works perfectly for bullish trades (buying above stop). For bearish trades (shorting), placing a stop at the bottom of the daily OB puts the stop below the entry, causing immediate liquidation and inverted R-level lines.
*   **The Lesson:** Protective stop-losses must always respect market direction relative to the anchor block:
    *   **BULLISH (Long):** Stop at Daily OB Floor (`Bottom` column).
    *   **BEARISH (SHORT):** Stop at Daily OB Ceiling (`Top` column).

---

### Category C — Visual Axis Stretching (Plotly CORS Blocks)

*   **The Bug:** Plotly charts stretching their X-axis back by several weeks or months, turning 15-minute charts into unreadable horizontal strips.
*   **The Cause:** Institutional target lines or OTE rectangles drawn with absolute `start_ts` matching the historical confirmation date (`conf_ts`). If `conf_ts` is outside the focus window, Plotly forces the X-axis wide to show it.
*   **The Lesson:** Always **clip** the start coordinate of shapes to the visible range of the pane:
    ```python
    ts_left = max(ts_signal, df_pane.index[0])
    ```

---

### Category D — Visual Label Overlap and Crowding

*   **The Bug:** Staggered visual labels horizontal crowding when signals fire within a few hours of each other on the same timeframe.
*   **The Lesson:** Enforce a strict minimum temporal spacing rule between annotated labels on the same timeframe (e.g., 48 hours for 1H, 12 hours for 15M, 4 hours for 5M) combined with a Rule of 3 ceiling (maximum 3 labels per chart).

---

### Category E — Silent Return Bug in smc.py

*   **The Bug:** `smc.retracements()` was calculating all values correctly but had a missing return statement at the end of its definition. All callers were receiving `None` silently, with no error raised.
*   **The Lesson:** After any new function is added to `smc.py`, verify the return value is not `None` before using it downstream. Add a one-line smoke test: `assert result is not None` after every `smc.*` call in diagnostic scripts.

