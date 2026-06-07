import pandas as pd
import os
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

def run_annual_audit():
    data_path = "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    print("==========================================================")
    print("ANNUAL SOVEREIGN AUDIT (MASTER 2016 DATA)")
    print("==========================================================\n")

    # Load 1M data and resample to 15M for institutional speed
    df_1m = pd.read_csv(data_path, sep=';', names=['ts', 'open', 'high', 'low', 'close', 'vol'], index_col=False)
    df_1m['ts'] = pd.to_datetime(df_1m['ts'], format='%Y%m%d %H%M%S')
    df_1m.set_index('ts', inplace=True)
    
    # Process month by month to avoid memory issues
    months = range(1, 13)
    global_results = []

    for m in months:
        print(f"Processing Month {m}...")
        df_month = df_1m[df_1m.index.month == m]
        if df_month.empty: continue
        
        df_15m = df_month.resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
        
        # 1. Scanners
        swings = smc.swing_highs_lows_v4(df_15m)
        fvgs = smc.fvg(df_15m)
        expansion = fvgs[['FVG', 'Top', 'Bottom', 'CE', 'MitigatedIndex']].copy()
        expansion.columns = ['Expansion', 'Top', 'Bottom', 'CE', 'MitigatedIndex']
        cons = smc.consolidation(df_15m)
        clean_ranges = smc.detect_clean_ranges(df_15m, swings)
        
        # 2. State Machine
        from smartmoneyconcepts.state_machine import detect_reversals
        reversals = detect_reversals(df_15m, swings)
        sm = PriceDeliveryStateMachine()
        audit = sm.process(
            ohlc=df_15m,
            consolidation=cons,
            expansion=expansion,
            liquidity=smc.liquidity(df_15m, swings),
            swing_hl=swings,
            clean_ranges=clean_ranges,
            reversals=reversals
        )
        
        # 3. Accuracy Calculation
        lrr_mask = (audit['SovereignEnv'] == "LRR").astype(int)
        lrr_diff = lrr_mask.diff()
        starts = lrr_mask.index[lrr_diff == 1]
        ends = lrr_mask.index[lrr_diff == -1]
        
        successes = 0
        totals = 0
        for start, end in zip(starts, ends):
            totals += 1
            seg = df_15m.loc[start:end]
            move = abs(seg['close'].iloc[-1] - seg['close'].iloc[0])
            if move > 0.0015: # 15 pips on 15m is strong delivery
                successes += 1
            elif len(seg) > 8:
                successes += 1
        
        accuracy = (successes / totals * 100) if totals > 0 else 0
        global_results.append({"Month": m, "Runs": totals, "Accuracy": f"{accuracy:.1f}%"})

    report = pd.DataFrame(global_results)
    print("\n" + "="*40)
    print("FINAL ANNUAL SOVEREIGN REPORT (AUDUSD 2016)")
    print("="*40)
    print(report.to_string(index=False))
    print("="*40)

if __name__ == "__main__":
    run_annual_audit()
