import re

SMC_PATH = r"d:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py"

with open(SMC_PATH, "r", encoding="utf-8") as f:
    content = f.read()

content = re.split(r'def _macro_bond_bias\(', content)[0]

new_code = """
def _macro_bond_bias(zn_df, zb_df, dxy_df=None):
    \"\"\"
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates Macro Regime (3-4 Month Shift) and Micro Execution Triggers.
    
    Returns a DataFrame containing:
        - 'regime': The forward-filled Macro Regime (+1 Bullish USD, -1 Bearish USD, 0 Neutral)
        - 'signal': The aligned Micro Execution Triggers (+1 Long USD, -1 Short USD)
    \"\"\"
    import pandas as pd

    df_out = pd.DataFrame(index=zn_df.index)
    df_out['regime'] = 0
    df_out['signal'] = 0

    if dxy_df is None:
        return df_out

    # =========================================================================
    # LAYER 1: MACRO REGIME (Quarterly Shift)
    # ZB vs DXY Inverse Correlation with 60-day filter
    # =========================================================================
    zb_swings_raw = smc.swing_highs_lows_v4(zb_df)
    zb_swings_macro = _filter_quarterly_swings(zb_swings_raw, min_days=60)
    
    smt_macro = smc.smt_divergence(zb_df, dxy_df, zb_swings_macro, correlation="inverse")
    
    regime_series = pd.Series(0, index=zn_df.index)
    if 'smt_bullish_div' in smt_macro.columns:
        # Bearish ZB SMT vs DXY (ZB HH, DXY fails LL) -> Bullish USD Regime
        regime_series[smt_macro['smt_bearish_div'] == True] = 1
        # Bullish ZB SMT vs DXY (ZB LL, DXY fails HH) -> Bearish USD Regime
        regime_series[smt_macro['smt_bullish_div'] == True] = -1

    # Forward-fill the regime
    df_out['regime'] = regime_series.replace(0, pd.NA).ffill().fillna(0)

    # =========================================================================
    # LAYER 2: MICRO EXECUTION TRIGGERS (Short-Term Timing)
    # ZN vs ZB Positive Correlation (Unfiltered)
    # =========================================================================
    zn_swings = smc.swing_highs_lows_v4(zn_df)
    smt_micro = smc.smt_divergence(zn_df, zb_df, zn_swings, correlation="positive")
    
    trigger_series = pd.Series(0, index=zn_df.index)
    if 'smt_bearish_div' in smt_micro.columns:
        trigger_series[smt_micro['smt_bearish_div'] == True] = 1
        trigger_series[smt_micro['smt_bearish_div_bm'] == True] = 1
        trigger_series[smt_micro['smt_bullish_div'] == True] = -1
        trigger_series[smt_micro['smt_bullish_div_bm'] == True] = -1

    # =========================================================================
    # LAYER 3: ALIGNMENT & MANIPULATION FILTER
    # =========================================================================
    dxy_swings_raw = smc.swing_highs_lows_v4(dxy_df)
    zn_dates = set(zn_swings['ts'])
    zb_dates = set(zb_swings_raw['ts'])
    dxy_dates = set(dxy_swings_raw['ts'])
    manipulation_dates = zn_dates.intersection(zb_dates).intersection(dxy_dates)

    for dt, trigger in trigger_series[trigger_series != 0].items():
        # Discard false break manipulation
        if dt in manipulation_dates:
            continue
            
        # The Execution Trigger must align with the active Macro Regime
        active_regime = df_out.at[dt, 'regime']
        if active_regime != 0 and active_regime == trigger:
            df_out.at[dt, 'signal'] = trigger

    return df_out

smc.macro_bond_bias = _macro_bond_bias
"""

# Append the original _macro_pair_bias and _macro_ob_alignment back
pair_bias_code = """

def _macro_pair_bias(macro_bias_series, pair_name):
    \"\"\"
    GAP 1: Currency Pair Classification Engine
    Translates the USD Macro Bias into an actionable LONG/SHORT bias for a specific pair.
    
    Pairs starting with USD (USDCAD, USDCHF, USDJPY) are directly correlated.
    Pairs ending with USD (EURUSD, GBPUSD, AUDUSD, NZDUSD) are inversely correlated.
    
    Returns a Series of +1 (LONG), -1 (SHORT), or 0 (NEUTRAL).
    \"\"\"
    import pandas as pd
    
    pair_upper = pair_name.upper()
    is_usd_first = pair_upper.startswith('USD')
    
    pair_bias = pd.Series(0, index=macro_bias_series.index)
    
    if is_usd_first:
        pair_bias = macro_bias_series.copy()
    else:
        # Inverse correlation
        pair_bias = macro_bias_series * -1
        
    return pair_bias

smc.macro_pair_bias = _macro_pair_bias


def _macro_ob_alignment(zb_df, dxy_df):
    \"\"\"
    Detects the "Prime Setup" confluence when:
    DXY is inside a Daily Bullish Order Block AND
    ZB is inside a Daily Bearish Order Block at the exact same time.
    \"\"\"
    import pandas as pd

    # Calculate Order Blocks — smc.ob() requires legacy swing_highs_lows format (HighLow column)
    zb_swings_ob  = smc.swing_highs_lows(zb_df)
    dxy_swings_ob = smc.swing_highs_lows(dxy_df)
    zb_ob  = smc.ob(zb_df,  zb_swings_ob)
    dxy_ob = smc.ob(dxy_df, dxy_swings_ob)

    alignment = pd.Series(False, index=dxy_df.index)

    # Inspect actual OB column names — smc.ob() may return 'OB' or sub-columns
    zb_col  = 'OB'  if 'OB'  in zb_ob.columns  else (zb_ob.columns[0]  if len(zb_ob.columns) > 0 else None)
    dxy_col = 'OB'  if 'OB'  in dxy_ob.columns else (dxy_ob.columns[0] if len(dxy_ob.columns) > 0 else None)

    if zb_col is None or dxy_col is None:
        return alignment

    # Forward-fill the current active OB zone
    zb_active  = zb_ob[zb_col].replace(0, pd.NA).ffill()
    dxy_active = dxy_ob[dxy_col].replace(0, pd.NA).ffill()

    # Prime Setup: DXY in Bullish OB (+1) AND ZB in Bearish OB (-1)
    prime_setup = (dxy_active == 1) & (zb_active == -1)
    prime_setup = prime_setup.reindex(dxy_df.index).fillna(False)

    return prime_setup

smc.macro_ob_alignment = _macro_ob_alignment
"""

with open(SMC_PATH, "w", encoding="utf-8") as f:
    f.write(content.rstrip() + "\n\n" + new_code + pair_bias_code)

print("Injected Macro Regime vs Execution architecture into smc.py")
