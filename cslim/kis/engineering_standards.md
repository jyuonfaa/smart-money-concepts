# ICT ENGINEERING STANDARDS — ARCHITECTURE AND VERIFICATION

These standards ensure the technical integrity and visual consistency of the ICT Algorithmic Trading System.

## Standard 1 — Pure Projection (Visualization)
The visualization layer (`visualize_*.py`) must be a **Pure Projection** of the `audit_logs` DataFrame.
- **NO Independent Logic:** No smoothing, environment classification, state flipping, or deduplication is allowed inside the visualizer.
- **Single Source of Truth:** All logical processing must happen in the `state_machine.py` (or `smc.py`) data layer first.
- **Guarantee:** If a value appears in the console audit, it must be the exact same value that determines the chart's color or label.

## Standard 2 — Audit Trail Format
Every new detector or state change must be verified using a standardized console output format to ensure clear, reviewable logs.
- **Format:** `Timestamp | Price | Raw State | Smoothed Env | Obstruction Count | Kill-Switch Trigger`
- **Smoothed Env:** This must be a column in the `audit_logs` DataFrame (calculated in the state machine), not a visualizer calculation.

## Standard 3 — Golden Master Dataset Protocol
To prevent silent regressions during complex development, every major logic change must be verified against the project's "Golden Master" range.
- **Test Range:** Sep 11–18, 2016 (AUDUSD).
- **Expected Benchmark:** This period is predominantly HRR (High Resistance) regardless of new detector additions.
- **Requirement:** Before finalizing any new feature or state machine change, run an audit against this range to ensure historical classifications remain intact.

## Standard 4 — Institutional Time-Macro Standard
The ICT algorithm is anchored in **Price + Time**.
- **NY Time Only:** All logic gates must reference Eastern Standard Time (UTC-5/UTC-4).
- **Time Gates:** Signal firing is gated by specific institutional windows (Killzones and Macros).
- **Time Anchors:** The Midnight Open is a hard vertical anchor for all expansion and daily bias logic.
- **Specific Windows:** Start/End times for these gates are defined strictly by the ICT notes; do not assume standard session times.

## Standard 5 — Error-Correcting Communication Protocol
Before writing implementation code for any new or complex ICT concept, **Antigravity** must present its understanding of the model visually.
- **Format:** A Mermaid or ASCII diagram showing price behavior at the relevant level, with the verbatim ICT quote it is derived from written above it.
- **Confirmation:** Explicit user confirmation of the diagram is required before any code is written.
- **Purpose:** To catch "Model Errors" before they are encoded into the state machine.

**Watch the video, take the notes, share the notes. Never design from assumption.**
