import sys
import pandas as pd
import numpy as np
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts.smc import smc

pd.options.mode.chained_assignment = None

def run_verification():
    print("=" * 70)
    print("M4V9 Vacuum Blocks Verification (AUDUSD 2016 15M) - Partial Fill Audit v2")
    print("=" * 70)

    csv_path = r'HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(csv_path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'])
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    df_15m = df_raw.resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()

    swing_hl = smc.swing_highs_lows(df_15m, swing_length=5)
    ob_df = smc.ob(df_15m, swing_hl)

    vb_df = smc._vacuum_blocks(df_15m, ob_df)
    vbs = vb_df[vb_df['VB'].notna()].copy()

    total_vbs = len(vbs)
    overlapping_vbs = vbs[vbs['VBOverlapsOB'] == True]
    confirmed_partial = vbs[vbs['VBPartialFillConfirmed'] == True]
    revisited = confirmed_partial[confirmed_partial['VBResidualRevisited'].notna()]
    not_revisited = confirmed_partial[confirmed_partial['VBResidualRevisited'].isna()]

    # Compute how many would have matched VBFilled naively (same timestamp)
    # Under naive logic, naive_closed = first close through residual boundary after rev_idx
    opens  = df_15m['open'].values
    highs  = df_15m['high'].values
    lows   = df_15m['low'].values
    closes = df_15m['close'].values
    idx_array = df_15m.index
    ob_dirs       = ob_df['OB'].values
    ob_tops       = ob_df['Top'].values
    ob_bottoms    = ob_df['Bottom'].values
    ob_mitigated  = ob_df['MitigatedIndex'].values

    same_timestamp_count = 0
    for ts, row in confirmed_partial.iterrows():
        i = df_15m.index.get_loc(ts)
        direction = int(row['VB'])
        vb_low = float(row['VBLow'])
        vb_high = float(row['VBHigh'])
        overlap_ob_top = None
        overlap_ob_bottom = None
        for j in range(i):
            if pd.isna(ob_dirs[j]): continue
            mit = ob_mitigated[j]
            if pd.isna(mit): continue
            if ((mit == 0.0) or (mit > i)) and ob_dirs[j] == direction and ob_bottoms[j] <= vb_high and ob_tops[j] >= vb_low:
                overlap_ob_top = ob_tops[j]
                overlap_ob_bottom = ob_bottoms[j]
                break

        filled_ts = row['VBFilled']

        # Re-derive rev_idx
        ext = None
        rev_idx = -1
        for j in range(i + 1, len(df_15m)):
            c_j = closes[j]
            l_j = lows[j]
            h_j = highs[j]
            if direction == 1:
                ext = l_j if ext is None else min(ext, l_j)
                if c_j > overlap_ob_top and ext < overlap_ob_top:
                    rev_idx = j
                    break
            else:
                ext = h_j if ext is None else max(ext, h_j)
                if c_j < overlap_ob_bottom and ext > overlap_ob_bottom:
                    rev_idx = j
                    break

        naive_closed_ts = None
        if rev_idx != -1:
            for k in range(rev_idx + 1, len(df_15m)):
                c_k = closes[k]
                if direction == 1:
                    if c_k <= vb_low:
                        naive_closed_ts = idx_array[k]
                        break
                else:
                    if c_k >= vb_high:
                        naive_closed_ts = idx_array[k]
                        break

        if pd.notna(filled_ts) and pd.notna(naive_closed_ts) and filled_ts == naive_closed_ts:
            same_timestamp_count += 1

    print(f"\nTOTAL COUNTS:")
    print(f"  Total Vacuum Blocks Detected:                 {total_vbs}")
    print(f"  VBs Overlapping Live Same-Dir OB:             {len(overlapping_vbs)}")
    print(f"  VBs with VBPartialFillConfirmed == True:      {len(confirmed_partial)}")
    print(f"    - Genuine VBResidualRevisited set:          {len(revisited)}")
    print(f"    - VBResidualRevisited is NaN:               {len(not_revisited)}")
    print(f"  Naive closure matching VBFilled (deduped):    {same_timestamp_count}")

    print("\nREPRESENTATIVE SAMPLE ROWS:")
    hdr = f"{'Date':<20} | {'Dir':<4} | {'PartLevel':<9} | {'Boundary':<9} | {'ResidualRevisited':<20} | {'VBFilled'}"
    print(hdr)
    print("-" * len(hdr))

    # Show samples of both genuine revisited, deduped (NaN), and unclosed
    sample_ts = [
        pd.Timestamp('2016-01-20 10:15:00'),  # Deduped to NaN (coincided with VBFilled)
        pd.Timestamp('2016-01-20 12:30:00'),  # Unclosed (NaN)
        pd.Timestamp('2016-04-20 22:15:00'),  # Genuine Revisit (VBFilled earlier, revisited later!)
        pd.Timestamp('2016-11-09 21:15:00'),  # Genuine Revisit
        pd.Timestamp('2016-12-30 09:30:00'),  # Deduped to NaN (coincided with VBFilled)
    ]
    for ts in sample_ts:
        if ts in confirmed_partial.index:
            row = confirmed_partial.loc[ts]
            d_str = "BULL" if row['VB'] == 1 else "BEAR"
            p_lvl = f"{row['VBPartialFillLevel']:.5f}" if pd.notna(row['VBPartialFillLevel']) else "NaN"
            r_bnd = f"{row['VBResidualBoundary']:.5f}" if pd.notna(row['VBResidualBoundary']) else "NaN"
            r_rev = str(row['VBResidualRevisited']) if pd.notna(row['VBResidualRevisited']) else "NaN"
            f_cls = str(row['VBFilled']) if pd.notna(row['VBFilled']) else "NaN"
            print(f"{str(ts):<20} | {d_str:<4} | {p_lvl:<9} | {r_bnd:<9} | {r_rev:<20} | {f_cls}")

if __name__ == "__main__":
    run_verification()
