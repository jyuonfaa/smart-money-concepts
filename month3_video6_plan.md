# Month 3 Video 6: Macro Economic to Micro Technical

Based on the newly extracted notes from the ICT Mentorship (pages 227-238), this module teaches how to establish a 3-to-6-month macroeconomic directional bias by tracking interest rates via the US Treasury bond markets.

## Core Concepts Extracted
1. **The Barometer:** 30-Year Treasury Bonds (ZB) and 10-Year Treasury Notes (ZN).
2. **The Inverse Correlation:** 
   - Bond prices drop = Interest rates increase = **US Dollar (DXY) rallies**.
   - Bond prices rally = Interest rates drop = **US Dollar (DXY) falls**.
3. **The Trigger (Bond SMT):** You look for SMT Divergence between the 10-year Note and the 30-year Bond at major swing points. For example, if the 10Y makes a higher high but the 30Y makes a lower high, it signals an impending drop in bonds (increase in rates), which gives a massive macro **Bullish** bias for the US Dollar.
4. **Macro to Micro Flow:** Once a Bullish USD bias is confirmed by Bond SMT, you drop down to the micro technicals on your currency pairs (e.g., going Long on USDCAD/USDJPY, or Short on EURUSD/GBPUSD/AUDUSD).

## Cross-Reference with Existing Architecture
We are in a great position here. Because we just perfected the `smc.smt_divergence()` engine in Video 5, **we do not need to build a new detection engine**. The existing engine is asset-agnostic and perfectly capable of detecting these bond divergences.

### What is New vs Refinement
- **Refinement:** We will reuse `smc.smt_divergence()`, passing `ZN` (10-year) as the asset and `ZB` (30-year) as the benchmark.
- **New (Macro Yield Translation):** We need a small translation layer. A bearish SMT in the bond market yields a **Bullish** macro bias for the Dollar.
- **New (Visualization):** We need a new dashboard (`visualize_month3_video6.py`) that visually proves this top-down flow:
  1. Top Pane: 10Y Note vs 30Y Bond SMT Divergence.
  2. Middle Pane: The inverse reaction on the US Dollar Index (DXY).
  3. Bottom Pane: The resulting surgical micro execution on a currency pair (e.g., EURUSD or USDCAD).

## Proposed Implementation Plan

### 1. The Macro Yield Translator (in `smc.py`)
We will add a lightweight wrapper function `smc.macro_bond_bias()`:
- It will run `smt_divergence(asset_df=ZN, benchmark_df=ZB)`.
- It will invert the output polarity:
  - If Bonds show a Bearish SMT (fake-out high) $\rightarrow$ Bias = `+1` (Bullish USD)
  - If Bonds show a Bullish SMT (fake-out low) $\rightarrow$ Bias = `-1` (Bearish USD)

### 2. The Verification Script (`verify_month3_video6.py`)
- We will load historical data for ZN, ZB, DXY, and EURUSD for the September-November 2016 period (the exact window ICT highlights in the notes).
- We will audit that the Bond SMT correctly fires in the 2nd/4th weeks of September and the 1st week of November, predicting the massive DXY rallies.

### 3. The Visual Masterpiece (`visualize_month3_video6.py`)
- We will create a stunning 3-pane Plotly dashboard demonstrating the "Macro to Micro" flow, drawing vertical lines from the Bond SMT triggers straight down through the DXY chart and into the EURUSD execution chart.

## User Review Required
> [!IMPORTANT]
> To execute this exact verification, I will need access to historical daily data for the 10-Year Note (`ZN`) and 30-Year Bond (`ZB`) for 2016 (or whichever period you have available). 
> 
> Do you have `ZN` and `ZB` CSV data in your `tests/test_data/` folder, or should I write a script to download the free Yahoo Finance equivalents (e.g., `^TNX` for 10Y Yield and `^TYX` for 30Y Yield) for the audit?

Please review this plan. If approved, let me know how you want to handle the Bond data, and I will begin the build!
