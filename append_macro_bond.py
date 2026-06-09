import os

SMC_PATH = r"d:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py"

code_to_append = """

def _macro_bond_bias(asset_df, benchmark_df):
    \"\"\"
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates the SMT Divergence between the US 10-Year Note (ZN, asset) 
    and the US 30-Year Bond (ZB, benchmark) to determine the macroeconomic 
    bias for the US Dollar.

    A bearish SMT in Bonds (10Y higher high, 30Y lower high) = Rising Interest Rates = Bullish USD (+1).
    A bullish SMT in Bonds (10Y lower low, 30Y higher low) = Dropping Interest Rates = Bearish USD (-1).

    Returns a Series where:
        1: Bullish USD Macro Bias
       -1: Bearish USD Macro Bias
        0: No Divergence
    \"\"\"
    # Re-use the exact SMT engine we built in Video 5
    smt_res = smc.smt_divergence(asset_df, benchmark_df)
    
    # The `smt_divergence` engine returns a DataFrame with 'smt_divergence' column (+1 / -1)
    if 'smt_divergence' not in smt_res.columns:
        # Fallback if the signature is slightly different
        return pd.Series(0, index=asset_df.index)

    bond_smt = smt_res['smt_divergence']
    
    # Invert the polarity for the US Dollar
    usd_bias = bond_smt.copy()
    usd_bias = usd_bias * -1
    
    return usd_bias

smc.macro_bond_bias = _macro_bond_bias
"""

with open(SMC_PATH, "a", encoding="utf-8") as f:
    f.write(code_to_append)

print("Appended macro_bond_bias to smc.py")
