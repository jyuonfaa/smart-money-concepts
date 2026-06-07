# NEW NOTES PROTOCOL — HOW TO READ AND PROCESS ANY NEW ICT NOTES

When new ICT notes are provided, do not write any code. Read and process first.

**Step 1 — Extract the exact definitions**
Identify every new concept introduced. For each one, find the exact quote or rule that defines it. Write it out verbatim. This is the specification. Everything built from it must trace back to this exact language.

**Step 2 — Identify what it measures**
For each new concept ask: what is price doing, at what level, relative to what reference point? ICT concepts are always about price behavior at a specific location. Name the location and the behavior precisely before thinking about code.

**Step 3 — Cross-reference against existing architecture**
Check the existing codebase before building anything new:
- Does `smc.py` already have a function that detects this or part of it?
- Does the state machine already handle this condition?
- Can an existing detector be extended rather than replaced?
- Which layer of the 7-layer architecture does this belong to?

**Step 4 — Identify what is new vs what is a refinement**
Some new notes refine an existing concept — tighten a threshold, add a condition, change a boundary rule. Others introduce a genuinely new detector. Treat these differently. A refinement edits existing code. A new concept adds a new function following the one-function-one-job rule.

**Step 5 — State the build plan before building**
Write out:
- What new function or change is needed
- Which file it goes in
- What inputs it takes and what it returns
- Which existing functions it depends on

Only begin coding after this plan is stated and confirmed.

**Rules that never change regardless of what new notes say:**
- Bodies not wicks for consolidation boundaries
- No lookahead — candle close data only
- Percentile not ATR for displacement thresholds
- Sunday candles skipped in all swing logic
- smc outputs are integers not strings
- Visual verification required before moving to the next concept

**If new notes are ambiguous:**
Do not interpret. Do not assume. State the ambiguity explicitly and ask which interpretation is correct before writing a single line.
