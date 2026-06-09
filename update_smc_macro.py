import re

SMC_PATH = r"d:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py"

with open(SMC_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Strip out the old macro_bond_bias
content = re.split(r'def _macro_bond_bias\(', content)[0]

new_code = """
def _macro_bond_bias(zn_df, zb_df, dxy_df=None):
    \"\"\"
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates the Macro USD Bias using the 3-4 Month Quarterly Shift constraint.
    \"\"\"
    import pandas as pd
    
    # 1. Quarterly Shift Constraint: swing_length=20 (1 month of trading days)
    # This prevents the engine from firing on minor intraday/weekly noise
    zn_swings = smc.swing_highs_lows_v4(zn_df, swing_length=20)
    
    # Internal Bond SMT (ZN vs ZB, Positive Correlation)
    smt_bonds = smc.smt_divergence(zn_df, zb_df, zn_swings, correlation="positive")
    
    usd_bias = pd.Series(0, index=zn_df.index)
    
    if 'smt_bearish_div' in smt_bonds.columns:
        # Bearish SMT in Bonds -> Bullish USD (+1)
        usd_bias[smt_bonds['smt_bearish_div'] == True] = 1
        usd_bias[smt_bonds['smt_bearish_div_bm'] == True] = 1
        
        # Bullish SMT in Bonds -> Bearish USD (-1)
        usd_bias[smt_bonds['smt_bullish_div'] == True] = -1
        usd_bias[smt_bonds['smt_bullish_div_bm'] == True] = -1

    # 2. Inter-market SMT (ZB vs DXY, Inverse Correlation)
    if dxy_df is not None:
        zb_swings = smc.swing_highs_lows_v4(zb_df, swing_length=20)
        smt_intermarket = smc.smt_divergence(zb_df, dxy_df, zb_swings, correlation="inverse")
        
        if 'smt_bullish_div' in smt_intermarket.columns:
            # Bearish Bond / Bullish DXY Inverse SMT
            # ZB higher high + DXY fails lower low -> Bearish SMT BM logic for inverse
            # wait, if correlation is inverse:
            # Asset (ZB) HH + BM (DXY) fails LL -> This is Asset-led Bearish (Scenario B in smt_divergence) -> 'smt_bearish_div'
            # If ZB has Bearish SMT against DXY, it means ZB made HH, DXY failed LL -> Bullish USD (+1)
            usd_bias[smt_intermarket['smt_bearish_div'] == True] = 1
            
            # Asset (ZB) LL + BM (DXY) fails HH -> Asset-led Bullish -> 'smt_bullish_div'
            # If ZB has Bullish SMT against DXY, it means ZB made LL, DXY failed HH -> Bearish USD (-1)
            usd_bias[smt_intermarket['smt_bullish_div'] == True] = -1

    return usd_bias

smc.macro_bond_bias = _macro_bond_bias


def _macro_ob_alignment(zb_df, dxy_df):
    \"\"\"
    Detects the "Prime Setup" confluence when:
    DXY is inside a Daily Bullish Order Block AND
    ZB is inside a Daily Bearish Order Block at the exact same time.
    \"\"\"
    import pandas as pd
    
    # Calculate Order Blocks
    zb_ob = smc.ob(zb_df)
    dxy_ob = smc.ob(dxy_df)
    
    alignment = pd.Series(False, index=dxy_df.index)
    
    if 'OB' not in zb_ob.columns or 'OB' not in dxy_ob.columns:
        return alignment
        
    # We want dates where DXY OB == 1 (Bullish) and ZB OB == -1 (Bearish)
    # The `ob()` function returns 1 for bullish, -1 for bearish.
    
    # Forward fill the current active OB
    zb_active = zb_ob['OB'].replace(0, pd.NA).ffill()
    dxy_active = dxy_ob['OB'].replace(0, pd.NA).ffill()
    
    # The Prime Setup:
    prime_setup = (dxy_active == 1) & (zb_active == -1)
    
    # Reindex to match just in case
    prime_setup = prime_setup.reindex(dxy_df.index).fillna(False)
    
    return prime_setup

smc.macro_ob_alignment = _macro_ob_alignment

"""

with open(SMC_PATH, "w", encoding="utf-8") as f:
    f.write(content.rstrip() + "\n\n" + new_code)

print("Updated smc.py with enhanced macro bias and OB alignment.")
