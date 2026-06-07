# ICT Development & Communication Rules

## Absolute Path Protocol
- **MANDATORY:** Always provide the full absolute file path for all generated HTML reports using the `file:///` URI scheme.
- **Reasoning:** Local file security blocks (CORS) in modern browsers often prevent opening local HTML files via relative names; absolute paths ensure direct access.

## Stable Pathing Protocol
- **MANDATORY:** All automated scripts must output to a **STABLE** master filename (e.g., `ICT_VIDEO_5_PREMIUM.html`).
- **Forbidden:** Do not use `uuid` or random suffixes in output filenames.
- **Reasoning:** This allows the user to refresh a single browser tab rather than managing multiple files, streamlining the institutional review process.

## Axis-Safe Anchoring Protocol
- **MANDATORY:** All institutional shapes (OTE zones, target lines) must be **CLIPPED** to the visible data range of each pane.
- **Implementation:** `start_ts = max(ote['conf_ts'], df_pane.index[0])`.
- **Reasoning:** This prevents Plotly from stretching the X-axis of surgical charts (e.g., 15M) back to historical confirmation dates (e.g., March), ensuring the chart remains focused on recent price action while still visually "pinning" the lines to the left edge if they are historical.

## Institutional Audit Integrity
- **MANDATORY:** Every institutional dashboard (Video 4, Video 5, etc.) must include a console-based "Institutional Sequence Audit".
- **Requirements:**
    - Print `Timestamp | Type | Price | Zone` for every plotted signal.
    - Explicitly verify and assert 100% chronological alternation (H -> L -> H).
    - Use Anchor Clipping to prevent unanchored visual artifacts when confirmation dates are outside the visible chart range.

## Visual-Textual Synchronicity Protocol
- **MANDATORY:** Never analyze ICT mentorship text or notes in isolation. Every textual concept MUST be cross-referenced with its corresponding diagram or screenshot.
- **Implementation:** If a text refers to a "shaded area," "yellow box," or "x markers," you MUST use the browser/vision tools to visually verify the exact candle high/low being referenced.
- **Reasoning:** ICT concepts are inherently visual; the text explains the "why," but the diagrams define the "where." Ignoring diagrams leads to algorithmic errors in identifying institutional footprints.

## Notes-First Handoff Protocol
- **MANDATORY:** When new curriculum notes or PDFs are shared, you MUST freeze all code changes and execution commands. 
- **Execution Protocol:**
    1. **Extract Verbatim Text:** Run extraction scripts to read all raw page texts.
    2. **Render Visual Pages:** Proactively render every referenced PDF page as a high-resolution PNG image using PyMuPDF (`fitz`) and save it to the App Data directory.
    3. **Perform Mathematical Audit:** Map out the exact numerical values, price levels, stop losses, and target pips from the charts, verifying their mathematical relationships (e.g., checking R-multiples and entry/stop distances).
    4. **Generate Study Artifacts:** Build a detailed verbatim notes artifact (`monthX_videoY_notes.md`) containing embedded page PNGs and clean tables *before* drafting any technical implementation plans.
    5. **Aesthetic Lock:** Do not write or modify code until the user explicitly reviews the notes artifact and approves the subsequent implementation plan.

## Reasoning and Execution Standard — ICT Algorithmic Trading System

**Before touching any code:**
1. Read the relevant ICT definition from the project notes. The definition tells you what the code is supposed to measure. If there is no definition for it in the notes, stop and ask.
2. Ask: is the current code's model of the problem correct, or just its syntax? A wrong model cannot be fixed by adjusting parameters — it must be replaced with the correct model derived from the definition.

**When a bug is reported:**
1. Print the raw data first. Verify the data layer is producing correct values before looking at the visualization layer.
2. State the exact line that is wrong, what it currently computes, and what it should compute instead.
3. Write the minimal change. Do not touch anything outside the stated bug.
4. A clean script run is not verification. The rendered chart output is the only verification that counts.

**When a fix does not produce the expected output:**
Do not adjust thresholds, expand windows, or add fallback conditions. Go back to the raw data, identify what the code is actually measuring, and compare it against the ICT definition. The mismatch between those two things is always the root cause.

**Never:**
- Build features that were not requested
- Approve a fix based on execution logs alone
- Use a parameter change to compensate for a wrong model
- Assume anything not written in the ICT project notes

## Dynamic Context Preservation Rule
- **MANDATORY:** At the end of locking any new video (e.g. V8, M2V1, M2V2, M2V3, etc.), you MUST execute:
  `python cslim/sync_manager.py`
- **Reasoning:** This dynamically scans the workspace directory, updates the file registries in the master handbook, pulls any updated system-level KIs back into the local repository folder, and executes all verification suites to ensure zero regressions are committed, guaranteeing that a new device checkout gets an instantly up-to-date long-term memory of the project.

