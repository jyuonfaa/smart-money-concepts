import sys
import pandas as pd
import numpy as np

sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts.smc import smc

pd.options.mode.chained_assignment = None

def run_verification():
    print("=" * 70)
    print("M4V10 Liquidity Voids Verification (AUDUSD 2016 15M) - Second Poke & Common Gap")
    print("=" * 70)

    csv_path = r'HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(csv_path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'])
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    df_15m = df_raw.resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()

    swing_hl = smc.swing_highs_lows(df_15m, swing_length=5)
    cons_df = smc.consolidation(df_15m)
    fvg_df = smc.fvg(df_15m)

    lv_df = smc._liquidity_voids(df_15m, cons_df, swing_hl, fvg_df)

    all_voids = lv_df[lv_df['LVStart'].notna()].copy()
    filled_voids = all_voids[all_voids['LVFilled'].notna()].copy()
    poked_voids = filled_voids[filled_voids['LVSecondPokeConfirmed'] == True].copy()
    gap_voids = poked_voids[poked_voids['LVCommonGapTop'].notna()].copy()
    entry_voids = gap_voids[gap_voids['LVCommonGapEntryIndex'].notna()].copy()

    total_voids = len(all_voids)
    total_filled = len(filled_voids)
    total_poked = len(poked_voids)
    total_gap = len(gap_voids)
    total_entry = len(entry_voids)

    print("\nTOTAL COUNTS:")
    print(f"  Total Voids Detected:                         {total_voids}")
    print(f"  Voids Reaching LVFilled:                      {total_filled}")
    print(f"  Voids with Confirmed Second Poke:             {total_poked}")
    print(f"  Voids Producing a Common Gap:                 {total_gap}")
    print(f"  Voids with Entry Confirmed:                   {total_entry}")

    # Chronological Sanity Check
    # Required ordering: LVStart <= formation (index) <= LVFilled < LVSecondPokeIndex < LVCommonGapEntryIndex
    ordering_violations = 0
    for ts, row in entry_voids.iterrows():
        t_start = pd.Timestamp(row['LVStart'])
        t_form  = pd.Timestamp(ts)
        t_fill  = pd.Timestamp(row['LVFilled'])
        t_poke  = pd.Timestamp(row['LVSecondPokeIndex'])
        t_entry = pd.Timestamp(row['LVCommonGapEntryIndex'])

        if not (t_start <= t_form and t_form <= t_fill and t_fill < t_poke and t_poke < t_entry):
            ordering_violations += 1

    print(f"\nCHRONOLOGICAL ORDERING SANITY CHECK:")
    print(f"  Violations (LVStart <= Form <= Fill < Poke < Entry): {ordering_violations}")

    print("\nREPRESENTATIVE SAMPLE ROWS (All New Fields):")
    print(f"{'VoidEnd':<20} | {'MissLiq':<9} | {'LVFilled':<20} | {'SecondPokeIndex':<20} | {'GapTop':<7} | {'GapBottom':<7} | {'CommonGapEntryIndex':<20}")
    print("-" * 118)
    for ts, row in entry_voids.head(5).iterrows():
        ts_str = str(ts)
        ml = str(row['MissingLiquidity'])
        f_str = str(row['LVFilled'])
        p_str = str(row['LVSecondPokeIndex'])
        gt = f"{row['LVCommonGapTop']:.5f}"
        gb = f"{row['LVCommonGapBottom']:.5f}"
        e_str = str(row['LVCommonGapEntryIndex'])
        print(f"{ts_str:<20} | {ml:<9} | {f_str:<20} | {p_str:<20} | {gt:<7} | {gb:<7} | {e_str:<20}")

if __name__ == '__main__':
    run_verification()
