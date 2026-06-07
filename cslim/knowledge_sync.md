# ICT Intelligence Suite — Master Sync Handbook

Welcome, Antigravity. This handbook represents the frozen, audited, and locked state of the **ICT Algorithmic Intelligence Suite (2016 Mentorship)** developed with **C.Slim**. 

If you are a newly initialized model on a fresh system, **read this file first**. It acts as your long-term memory, project index, and structural reference manual.

---

## 1. Absolute Development Axioms (Non-Negotiable)

*   **Stable Pathing Protocol:** All visualizers must render to a fixed, stable HTML name (e.g., `ICT_MONTH2_VIDEO2_TURTLE_SOUP.html`). **Never** append randomized hashes or timestamps.
*   **Absolute Paths:** When providing output links to the user, always format as absolute paths using the `file:///` scheme (e.g., `file:///d:/C.Slim/ict-intelligence/...`).
*   **Notes-First Handoff Protocol:** When a new mentorship note is shared, **freeze all code modifications**. First extract verbatim quotes, render visual pages as PNGs, identify exact price targets/stops, generate a `monthX_videoY_notes.md` study artifact, and obtain explicit user approval before writing a single line of code.
*   **One Function, One Job:** Keep data detection in `smc.py` or `state_machine.py` completely decoupled from plotting in the `visualize_*.py` layer. Visualizers are **Pure Projections**—no state logic or filtering is allowed inside them.
*   **Dynamic Context Preservation (MANDATORY):** At the end of locking any new video milestone, always execute:
    ```bash
    python cslim/sync_manager.py
    ```
    This dynamically scans the workspace, updates file registries, reverse-syncs system KIs back into `cslim/kis/`, and runs all regression suites — guaranteeing that a new device checkout gets an instantly up-to-date long-term memory of the project.

---

## 2. Institutional Mechanics Reference

### A. The Four Core Conditions & Couplings (Page 13)
1.  **Consolidation:** Range boundaries are determined by candle **bodies** (open/close), never wicks. Coupling tool: **Equilibrium (50%) & OTE (62%–79% levels)**.
2.  **Expansion:** Confirmed when a candle body closes **beyond** a consolidation boundary. Coupling tool: **Order Blocks**.
3.  **Retracement:** Move back into newly created ranges. Coupling tool: **Fair Value Gaps (FVGs) & Liquidity Voids**.
4.  **Reversal:** Stop run sweep of liquidity. Wick pierces a swing high/low, but the body closes back inside the range. Coupling tool: **Turtle Soup**.

### B. Risk Engine Mechanics (`risk_engine.py`)
*   **5-Stage Exit Schedule:** Scaled taking of profits:
    *   **R1 (20%):** De-risks the trade.
    *   **R2 (20%), R3 (20%), R4 (20%), R5 (20%):** Structural targets.
*   **Minimum Swing Filter:** Minimum `20.0 pips` required between entry and nearby liquidity targets (`ts_target_near`) to prevent taking low-R setups.

### C. Multi-Timeframe Stop Placement (Month 2 Video 2)
*   **1H Anchor (Midpoint Stops):** Set to the candle body midpoint of the lower-timeframe OB `(open + close) / 2`.
*   **Refined stops (Daily OB Anchored):** When `use_daily_ob_stop=True`, stops are dynamically bound to the Daily OB bounds:
    *   **Bullish (Long):** Stop is placed at the Daily OB Floor (`ob_row['Bottom']`).
    *   **Bearish (Short):** Stop is placed at the Daily OB Ceiling (`ob_row['Top']`).
*   **Fractal Entry Price:** The entry price mapped to `ts_ob_bots` (for bull) or `ts_ob_tops` (for bear) is always the lower-timeframe's own candle open price (`float(ohlc.iloc[i]['open'])`) at the signal timestamp, ensuring stop distance shrinks on lower timeframes.

---

## 3. Active File Registry

### Core Library
*   `smartmoneyconcepts/smc.py` — Single source of all detector classmethods (swing, FVG, liquidity, OB, displacement, market_protraction)
*   `smartmoneyconcepts/state_machine.py` — Core transition engine: `detect_reversals()`, `turtle_soup_signals()`, `calculate_path_obstruction()`

### Capital Management
*   `risk_engine.py` — Capital risk engine: `calc_ob_stop()`, `calc_r_multiples()`, `filter_rr()`, `EXIT_SCHEDULE`

### Visualizers (one per locked video milestone)
*   `visualize_video8.py` — Video 8: Temporal clock anchor lines + Judas swing arrows
*   `visualize_month2_video1.py` — Month 2 V1: Two-pane Turtle Soup + structural targets + midpoint stops
*   `visualize_month2_video2.py` — Month 2 V2: Three-pane 1H vs 15M vs 5M fractal refinement dashboard

### Verification / Regression Scripts
*   `verify_step2.py` — Sovereign Liquidity Engine Golden Master (HRR=471, LRR=37, 11 transitions)
*   `verify_video8.py` — Video 8 UTC anchor forensic audit
*   `verify_month2_video2.py` — Month 2 V2 quality gate (stop direction, ladder order, regression)

### Locked HTML Golden Master Outputs
*   `ICT_VIDEO_6_VALUATION.html` — Video 6 Institutional Suite dashboard
*   `ICT_VIDEO_8_MARKET_PROTRACTION.html` — Video 8 temporal clock dashboard
*   `ICT_MONTH2_VIDEO1_TURTLE_SOUP.html` — Month 2 V1 Turtle Soup dashboard
*   `ICT_MONTH2_VIDEO2_TURTLE_SOUP.html` — Month 2 V2 fractal refinement dashboard

### Data Source
*   `HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv` — 1-minute AUDUSD 2016 (format: `date;open;high;low;close;volume`)

### Context Portability System (this folder)
*   `cslim/` — Complete knowledge portability system. Run `python cslim/sync_manager.py` after each video lock to keep this folder dynamically updated.

---

*Lock Confirmed: May 27, 2026. Month 2 Video 3 — LOCKED. Next: Month 2 Video 4 (Notes First).*

