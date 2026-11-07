import sys
import pandas as pd
import numpy as np

sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts.smc import smc

pd.options.mode.chained_assignment = None

def run_verification():
    print("=" * 70)
    print("M4V11 Liquidity Raids Verification (AUDUSD 2016 15M) - Entry Techniques")
    print("=" * 70)

    csv_path = r'HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(csv_path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'])
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    df_15m = df_raw.resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()

    swing_hl = smc.swing_highs_lows(df_15m, swing_length=5)
    raids_df = smc._liquidity_raids(df_15m, swing_hl)

    valid_raids = raids_df[raids_df['RaidType'].notna()].copy()
    total_raids = len(valid_raids)
    tech_a_count = len(valid_raids[valid_raids['TechAEntryPrice'].notna()])
    tech_b_count = len(valid_raids[valid_raids['TechBEntryNear'].notna()])
    tech_b_expected_or_higher = len(valid_raids[valid_raids['SweepDepthPips'] >= 10.0])

    print("\nTOTAL COUNTS:")
    print(f"  Total Raids Detected:                          {total_raids}")
    print(f"  Raids with TechAEntryPrice set:                {tech_a_count}")
    print(f"  Raids with TechBEntryNear/Far set (>=10 pips): {tech_b_count}")
    print(f"  Raids >= 10 pips in raw SweepDepthPips:        {tech_b_expected_or_higher}")

    # Check consistency: TechA should equal SwingLevel exactly
    tech_a_matches = (valid_raids['TechAEntryPrice'] == valid_raids['SwingLevel']).all()
    print(f"  TechAEntryPrice matches SwingLevel 100%:       {tech_a_matches}")

    # Check TechB only set when SweepDepthPips >= 10.0
    tech_b_matches_filter = (tech_b_count == tech_b_expected_or_higher)
    print(f"  TechB population matches >=10 pips filter:     {tech_b_matches_filter}")

    print("\nREPRESENTATIVE SAMPLE ROWS (Technique B Populated):")
    cols = ['RaidType', 'SwingLevel', 'SweepDepthPips', 'Classification', 'TechAEntryPrice', 'TechBEntryNear', 'TechBEntryFar', 'TechBStopNear', 'TechBStopFar']
    sample = valid_raids[valid_raids['TechBEntryNear'].notna()].head(5)
    for ts, row in sample.iterrows():
        print(f"\nRaidIndex: {ts} | Type: {row['RaidType']} | Swing: {row['SwingLevel']:.5f} | Depth: {row['SweepDepthPips']:.1f} pips | Class: {row['Classification']}")
        print(f"  TechAEntryPrice : {row['TechAEntryPrice']:.5f}")
        print(f"  TechBEntryNear  : {row['TechBEntryNear']:.5f}")
        print(f"  TechBEntryFar   : {row['TechBEntryFar']:.5f}")
        print(f"  TechBStopNear   : {row['TechBStopNear']:.5f} (30 pips from far edge)")
        print(f"  TechBStopFar    : {row['TechBStopFar']:.5f} (50 pips from far edge)")

if __name__ == '__main__':
    run_verification()
