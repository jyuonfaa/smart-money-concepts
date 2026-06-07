# GATEKEEPER HANDOFF PROTOCOL — CONCEPT LOCKING

No ICT concept is considered "Done" until it formally passes this three-step Gatekeeper Check. This prevents carry-forward bugs and ensures a stable foundation for the Market Maker Model.

## Step 1 — Data Audit (Standardized Trail)
The state machine's raw output must be verified in the console log using the **Standardized Audit Trail Format**.
- **Requirement:** 100% adherence to the state transition gates.
- **Checkpoint:** Verify that `Obstruction Counts`, `FVG Alignments`, and `Smoothed Envs` are mathematically correct before touching the visualizer.

## Step 2 — Visual Audit (Institutional Footprint)
The rendered Plotly chart must be visually compared against the source diagrams/videos in the project notes.
- **Requirement:** Environmental colors (LRR Green / HRR Maroon), displacement markers (Yellow boxes), and liquidity zones must match the "Institutional Footprint" described by ICT.
- **Verification:** The rendered output is the only verification that counts for a "Done" status.

## Step 3 — Golden Master Check (Regression)
The new code must be run against the existing **Golden Master Datasets** to ensure no regressions in previously locked concepts.
- **Anchor Dataset:** AUDUSD Sep 11–18, 2016.
- **Benchmark:** This period must remain predominantly HRR (High Resistance) regardless of new detector additions.

**A concept is only LOCKED once all three checks pass. No exceptions.**
