import pandas as pd
from smartmoneyconcepts.smc import smc

def run_verification():
    print("--- MONTH 3 VIDEO 6: MACRO REGIME VS MICRO EXECUTION ---")
    print("Loading historical data for ZN, ZB, DXY, and EURUSD (2016)...")
    
    try:
        zn = pd.read_csv("tests/test_data/MACRO/ZN_Daily_2016.csv")
        zb = pd.read_csv("tests/test_data/MACRO/ZB_Daily_2016.csv")
        dxy = pd.read_csv("tests/test_data/MACRO/DXY_Daily_2016.csv")
        eurusd = pd.read_csv("tests/test_data/MACRO/EURUSD_Daily_2016.csv")
    except FileNotFoundError:
        print("Data files not found. Did the fetch script complete?")
        return

    for df in [zn, zb, dxy, eurusd]:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

    common_dates = zn.index.intersection(zb.index).intersection(dxy.index).intersection(eurusd.index)
    zn = zn.loc[common_dates].copy()
    zb = zb.loc[common_dates].copy()
    dxy = dxy.loc[common_dates].copy()
    eurusd = eurusd.loc[common_dates].copy()

    # Calculate Macro Bias (Returns DataFrame with 'regime' and 'signal')
    print("Calculating Quarterly Macro Regime and Micro Execution Triggers...")
    macro_df = smc.macro_bond_bias(zn, zb, dxy)
    
    # Calculate Inter-market Order Block Alignment
    print("Detecting Inter-Market Order Block Confluence (Prime Setups)...")
    ob_alignment = smc.macro_ob_alignment(zb, dxy)
    
    signals = macro_df['signal'][macro_df['signal'] != 0]
    prime_setups = ob_alignment[ob_alignment == True]

    print("\n--- FORENSIC AUDIT: 2016 MACRO SIGNALS (Regime + Execution) ---")
    print(f"{'Date':<15} | {'Macro Regime':<15} | {'Execution':<15} | {'EURUSD Action':<15}")
    print("-" * 75)
    
    eurusd_bias = smc.macro_pair_bias(signals, 'EURUSD')

    for date, bias in signals.items():
        regime = macro_df.at[date, 'regime']
        regime_str = "BULLISH (+1)" if regime == 1 else "BEARISH (-1)"
        signal_str = "BUY USD" if bias == 1 else "SELL USD"
        eurusd_action = "SHORT" if eurusd_bias.loc[date] == -1 else "LONG"
        print(f"{date.strftime('%Y-%m-%d'):<15} | {regime_str:<15} | {signal_str:<15} | {eurusd_action:<15}")

    print("\n--- FORENSIC AUDIT: INTER-MARKET OB ALIGNMENT (Prime Setups) ---")
    print("These are dates where DXY is in a Daily Bullish OB AND ZB is in a Daily Bearish OB.")
    print("-" * 75)
    for date, is_prime in prime_setups.items():
        print(f"{date.strftime('%Y-%m-%d'):<15} | PRIME MACRO/MICRO CONFLUENCE DETECTED")

    print("\nVerification Complete.")

if __name__ == "__main__":
    run_verification()
