# ICT Mentorship Month 2 Video 7: Market Maker Trap False Flag

## Overview
This document extracts the foundational concepts, verbatim quotes, and trading rules from "Month 2 Video 7: Market Maker Trap False Flag" (Pages 110-129), adhering to the **Notes-First Handoff Protocol**. No code will be written until this logic is fully reviewed and approved.

## 1. Verbatim Conceptual Extracts

**On False Flags:**
> "A false flag is basically a pattern that classic chartists and pure chart pattern traders will fall victim to a lot... in a mature bull trend or in higher time frame distribution levels, price will post—or create, or print if you will—in our charts a false bull flag."

**On False Bear Flags:**
> "Not all sudden price declines that move into a short-term consolidation are bear flags. And obviously, in mature bear trends or in higher time frame accumulation levels, price will post false bear flags, and obviously retail traders will see this as a classic continuation sell pattern, but many times it will reverse."

**On Higher Time Frame Alignment:**
> "The takeaway is understanding higher time frame charts and understanding the discount markets will assist in identifying when these are potentially false bear flags or when not to expect another leg lower but in fact a buy."

**On Executing False Bull Flags (Turtle Soup Scenario):**
> "You can get a turtle soup scenario it will start to come up and start to break down and that's the easiest one to trade because you'll actually see it go up get people tripped up thinking it's going to go higher then it rolls over. Once that happens, you want to sell the first return back to a bearish orderblock."

**On Executing False Bear Flags:**
> "We want to wait for a swing high to be created and violated on the upside... Market trades above it and then comes back to the last bearish candle... So we can take that idea and not look at it as a bear flag but look at it as a buying opportunity. So we can be a buyer now that price has come down to the last bearish candle with a stop below the flag's low."

## 2. Institutional Logic & Rules

### Core Setup: Market Maker Trap
The market creates patterns (bull/bear flags) that induce retail continuation trading, only to reverse abruptly because they are anchored inside higher timeframe premium/discount zones.

### Identifying the Trap
1. **False Bull Flag:** Looks like a consolidation slanted slightly lower after an impulse move up. However, if it forms inside a **Higher Timeframe Bearish Orderblock (Premium/Distribution Zone)**, it is a trap.
2. **False Bear Flag:** Looks like a consolidation slanted slightly upward after an impulse move down. However, if it forms inside a **Higher Timeframe Accumulation Zone (Discount/Below old lows)**, it is a trap.
3. **Candle Body Supremacy:** The trap is often identified by looking at the **bodies of the candles on higher timeframes**, ignoring wicks. The wicks simply represent the stop runs that feed the reversal.

### Entry & Stop Mechanics

#### Bearish Setup (False Bull Flag Trap)
- **Condition:** Price rallies into a Premium/Distribution area (Bearish OB) and prints a bull flag.
- **Trigger:** Price breaks down instead of continuing higher (Turtle Soup). 
- **Entry:** Sell short on the first return back to a newly created **bearish orderblock**.
- **Stop Loss:** Placed directly above the highest wick of the false bull flag.

#### Bullish Setup (False Bear Flag Trap)
- **Condition:** Price drops into a Discount/Accumulation area (below previous candle bodies) and prints a bear flag.
- **Trigger:** Wait for a short-term Swing High (SH) to be violated on the upside.
- **Entry:** Buy on the retracement down to the **last bearish candle** (Bullish OB). Example Entry price from notes: `0.7468`.
- **Stop Loss:** Placed directly below the absolute lowest wick of the false bear flag.

## 3. Next Steps for Implementation
Before we transition this into code for `visualize_month2_video7.py` and `smc.py`, we need to define how to structurally identify a "False Flag" programmatically:
1. **Identify the Impulse Leg + Consolidation:** Need a mathematical definition for the short-term flag pattern (e.g., strong displacement followed by 3-5 candles of counter-trend consolidation).
2. **Contextualize with Higher Timeframe:** The algorithm must cross-reference this flag with the Daily/4H Premium/Discount zones (already built in the Sovereign Engine).
3. **Trigger Confirmation:** Implement the structural break trigger (Turtle soup rollover or Swing High violation) before validating the entry OB.

**Awaiting User Approval on Notes and Conceptual Mapping.**
