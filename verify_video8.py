import pandas as pd
from smartmoneyconcepts import smc

def main():
    print("====================================================================")
    print("RUNNING FORENSIC REGRESSION AUDIT: VIDEO 8 MARKET PROTRACTION")
    print("====================================================================")
    
    # 1. Load data
    csv_path = "tests/test_data/EURUSD/EURUSD_15M.csv"
    print(f"Loading test data from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    # Ensure correct index and datetime formatting
    date_col = 'Date' if 'Date' in df.columns else 'date'
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    df = df.iloc[-3000:] # Audit the last 3000 candles to get a rich dataset
    
    # 2. Run detector
    print("Running smc.market_protraction()...")
    result = smc.market_protraction(df, threshold_pips=0.0005)
    
    # 3. Analyze signals
    signals = result[result['protraction_dir'] != 0].copy()
    
    print("\n--- Summary of Signal Frequencies ---")
    freqs = signals['protraction_anchor'].value_counts()
    for anchor, count in freqs.items():
        print(f"  * {anchor}: {count} signals detected")
    print(f"  * Total Protraction Swings: {len(signals)}")
    
    print("\n--- Detailed Forensic Log (Last 15 Swings) ---")
    headers = f"{'Timestamp (UTC)':<22} | {'Anchor Time':<10} | {'Direction':<9} | {'Magnitude (Pips)':<16}"
    print(headers)
    print("-" * len(headers))
    
    for idx, row in signals.tail(15).iterrows():
        ts_str = idx.strftime('%Y-%m-%d %H:%M')
        anchor = row['protraction_anchor']
        direction = "BULLISH" if row['protraction_dir'] == 1 else "BEARISH"
        # Convert magnitude to pips for presentation (EURUSD 1 pip = 0.0001)
        mag_pips = row['protraction_mag'] / 0.0001
        
        print(f"{ts_str:<22} | {anchor:<10} | {direction:<9} | {mag_pips:<16.2f}")
        
    print("\n====================================================================")
    print("FORENSIC REGRESSION AUDIT: COMPLETE")
    print("====================================================================")

if __name__ == "__main__":
    main()
