import re

SMC_PATH = r"smartmoneyconcepts\smc.py"

with open(SMC_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Define the new _macro_bond_bias function
new_macro_bond_bias = """def _macro_bond_bias(zn_df, zb_df, dxy_df=None):
    \"\"\"
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates the Macro USD Bias using the 3-4 Month Quarterly Shift constraint.
    Incorporates:
    - Triple Instrument False Break Filter
    - Failed Lower Low Specificity (for ZB vs DXY inverse SMT)
    - Bond Consolidation Phase Confirmation
    \"\"\"
    import pandas as pd

    zn_swings_raw = smc.swing_highs_lows_v4(zn_df)
    zn_swings = _filter_quarterly_swings(zn_swings_raw, min_days=60)

    smt_bonds = smc.smt_divergence(zn_df, zb_df, zn_swings, correlation="positive")

    usd_bias = pd.Series(0, index=zn_df.index)

    if 'smt_bearish_div' in smt_bonds.columns:
        usd_bias[smt_bonds['smt_bearish_div'] == True] = 1
        usd_bias[smt_bonds['smt_bearish_div_bm'] == True] = 1
        usd_bias[smt_bonds['smt_bullish_div'] == True] = -1
        usd_bias[smt_bonds['smt_bullish_div_bm'] == True] = -1

    if dxy_df is not None:
        zb_swings_raw = smc.swing_highs_lows_v4(zb_df)
        zb_swings = _filter_quarterly_swings(zb_swings_raw, min_days=60)
        smt_intermarket = smc.smt_divergence(zb_df, dxy_df, zb_swings, correlation="inverse")

        if 'smt_bullish_div' in smt_intermarket.columns:
            # GAP 2: Failed Lower Low Specificity Filter
            # For each signal, we check if DXY made an attempt close to its prior pivot
            dxy_atr = (dxy_df['high'] - dxy_df['low']).rolling(14).mean()
            
            for date in smt_intermarket[smt_intermarket['smt_bearish_div'] == True].index:
                # ZB higher high + DXY fails lower low -> Bearish SMT BM logic for inverse
                # We need to find the previous swing low in DXY
                dxy_swings = smc.swing_highs_lows_v4(dxy_df)
                dxy_lows = dxy_swings[dxy_swings['type'] == 'LOW']
                past_lows = dxy_lows[dxy_lows['ts'] <= date]
                if len(past_lows) >= 2:
                    current_low_p = past_lows.iloc[-1]['p']
                    prev_low_p = past_lows.iloc[-2]['p']
                    atr_val = dxy_atr.loc[date] if not pd.isna(dxy_atr.loc[date]) else 1.0
                    # Must be a failure, so current low > prev low, but within 1.0 ATR (an attempt)
                    # wait, it might be that we just ensure it didn't miss by a massive amount
                    if current_low_p > prev_low_p and (current_low_p - prev_low_p) < (1.0 * atr_val):
                        usd_bias.loc[date] = 1

            for date in smt_intermarket[smt_intermarket['smt_bullish_div'] == True].index:
                # ZB LL + DXY fails HH
                dxy_swings = smc.swing_highs_lows_v4(dxy_df)
                dxy_highs = dxy_swings[dxy_swings['type'] == 'HIGH']
                past_highs = dxy_highs[dxy_highs['ts'] <= date]
                if len(past_highs) >= 2:
                    current_high_p = past_highs.iloc[-1]['p']
                    prev_high_p = past_highs.iloc[-2]['p']
                    atr_val = dxy_atr.loc[date] if not pd.isna(dxy_atr.loc[date]) else 1.0
                    if current_high_p < prev_high_p and (prev_high_p - current_high_p) < (1.0 * atr_val):
                        usd_bias.loc[date] = -1

    # GAP 3: Filter Manipulation (Triple Instrument False Break)
    if dxy_df is not None:
        usd_bias = smc.macro_filter_manipulation(zn_df, zb_df, dxy_df, usd_bias, lookback=1)

    # GAP 4: Bond Consolidation Confirmation
    usd_bias = smc.macro_confirm_consolidation(zb_df, usd_bias, lookforward=15, atr_multiplier=0.8)

    return usd_bias
"""

# Replace the existing _macro_bond_bias
pattern = re.compile(r'def _macro_bond_bias\(zn_df, zb_df, dxy_df=None\):.*?(?=\nsmc\.macro_bond_bias = _macro_bond_bias)', re.DOTALL)
content = pattern.sub(new_macro_bond_bias, content)

with open(SMC_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied gap 2-4 patches to _macro_bond_bias.")
