import pandas as pd
import numpy as np
import re

SMC_PATH = r"d:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py"

with open(SMC_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# We will strip out the existing _filter_quarterly_swings, _macro_bond_bias, _macro_ob_alignment
# and replace them with the advanced versions.
content = re.split(r'def _filter_quarterly_swings\(', content)[0]

new_code = """
def _filter_quarterly_swings(swings_df, min_days=60):
    \"\"\"
    Enforce the ICT Quarterly Shift Constraint.
    Filter swing_highs_lows_v4 output to only keep pivots that are at least
    `min_days` calendar days apart. This simulates a 3-4 month macro lookback.
    \"\"\"
    if swings_df.empty:
        return swings_df
    
    filtered = [swings_df.iloc[0]]
    for i in range(1, len(swings_df)):
        days_apart = (swings_df.iloc[i]['ts'] - filtered[-1]['ts']).days
        if days_apart >= min_days:
            filtered.append(swings_df.iloc[i])
    
    import pandas as pd
    return pd.DataFrame(filtered).reset_index(drop=True)


def _macro_bond_bias(zn_df, zb_df, dxy_df=None):
    \"\"\"
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates the Macro USD Bias using the 3-4 Month Quarterly Shift constraint,
    incorporating Triple False Break detection and Consolidation Confirmation.
    \"\"\"
    import pandas as pd
    import numpy as np

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
        
        # SMT Divergence automatically enforces the "Failed Lower Low" specificity.
        # It requires the Benchmark (DXY) to print a Higher Low while the Asset (ZB) prints a Higher High.
        smt_intermarket = smc.smt_divergence(zb_df, dxy_df, zb_swings, correlation="inverse")

        if 'smt_bullish_div' in smt_intermarket.columns:
            usd_bias[smt_intermarket['smt_bearish_div'] == True] = 1
            usd_bias[smt_intermarket['smt_bullish_div'] == True] = -1

        # GAP 3: Triple Instrument False Break Filter
        # If ZN, ZB, and DXY all have an extreme (swing) on the exact same day, it's manipulation (e.g. Election Night)
        # We discard any signals on these specific dates.
        dxy_swings_raw = smc.swing_highs_lows_v4(dxy_df)
        zn_dates = set(zn_swings_raw['ts'])
        zb_dates = set(zb_swings_raw['ts'])
        dxy_dates = set(dxy_swings_raw['ts'])
        
        manipulation_dates = zn_dates.intersection(zb_dates).intersection(dxy_dates)
        for d in manipulation_dates:
            if d in usd_bias.index:
                usd_bias.loc[d] = 0

    # GAP 4: Consolidation Phase Confirmation
    # Check if Bond Market (ZB) consolidates for 10 days after the signal.
    # We compare 10-day post-signal ATR to 20-day pre-signal ATR.
    def calc_atr(df, period):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
        
    zb_atr = calc_atr(zb_df, 14)
    
    confirmed_bias = pd.Series(0, index=usd_bias.index)
    signals = usd_bias[usd_bias != 0]
    
    for dt, bias in signals.items():
        # Find index of dt in zb_df
        try:
            idx = zb_df.index.get_loc(dt)
            # Need at least 20 days prior and 10 days post
            if idx < 20 or idx + 10 >= len(zb_df):
                continue
                
            pre_atr = zb_atr.iloc[idx]
            post_atr = zb_atr.iloc[idx + 10]
            
            # If volatility compresses or stays roughly flat (< 1.2x pre_atr), it's a valid consolidation buildup
            if post_atr < (pre_atr * 1.2):
                confirmed_bias.loc[dt] = bias
        except KeyError:
            continue

    return confirmed_bias

smc.macro_bond_bias = _macro_bond_bias


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
    f.write(content.rstrip() + "\n\n" + new_code)

print("Injected advanced macro fixes into smc.py")
