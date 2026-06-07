import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals, false_flag_signals

def run_backtest():
    print("Loading 2016 data...")
    CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)

    df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    df_4h = df_raw.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

    print("Running core SMC indicators...")
    daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
    daily_cons = smc.consolidation(df_daily)
    daily_rets = smc.retracements(df_daily, daily_swings)
    daily_ob_df = smc.ob(df_daily, daily_swings)
    daily_reversals = detect_reversals(df_daily, daily_swings)
    daily_liq = smc.liquidity(df_daily, daily_swings)
    daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob_df, df_daily, liq_df=daily_liq)
    daily_measured_moves = smc.measured_moves(df_daily, daily_swings)

    swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
    ob_4h = smc.ob(df_4h, swings_4h)
    disp_4h = smc.displacement(df_4h)

    print("Generating False Flag Signals...")
    ff_15m = false_flag_signals(
        ohlc_daily=df_daily,
        ohlc_ltf=df_15m,
        ohlc_4h=df_4h,
        daily_consolidation=daily_cons,
        daily_retracements=daily_rets,
        daily_turtle_soup=daily_ts,
        ob_4h=ob_4h,
        disp_4h=disp_4h,
        daily_measured_moves=daily_measured_moves
    )

    bull_sigs = ff_15m[ff_15m['false_bull_flag']].copy()
    bear_sigs = ff_15m[ff_15m['false_bear_flag']].copy()
    
    bull_sigs['trade_type'] = 'Short (Bull Flag Trap)'
    bear_sigs['trade_type'] = 'Long (Bear Flag Trap)'
    all_sigs = pd.concat([bull_sigs, bear_sigs]).sort_index()

    ds_indexed = daily_swings.copy()
    ds_indexed.index = df_daily.index

    total_trades = 0
    tp1_hits = 0
    tp2_hits = 0
    full_sl_hits = 0
    be_sl_hits = 0
    total_durations = []

    # --- 3. Evaluate Trades ---
    print("\n--- Simulating Trades Chronologically ---")

    # High Impact 2016 Macro Events (Do Not Trade windows)
    # Format: ('Event Name', Start Date, End Date)
    MACRO_EVENTS_2016 = [
        ('April FOMC / BOJ Shock', pd.Timestamp('2016-04-26'), pd.Timestamp('2016-04-30')),
        ('UK Brexit Referendum', pd.Timestamp('2016-06-20'), pd.Timestamp('2016-06-25')),
        ('Aus Federal Election / NFP', pd.Timestamp('2016-06-30'), pd.Timestamp('2016-07-04')),
        ('July FOMC', pd.Timestamp('2016-07-25'), pd.Timestamp('2016-07-27')),
        ('September FOMC', pd.Timestamp('2016-09-20'), pd.Timestamp('2016-09-24')),
        ('US Presidential Election', pd.Timestamp('2016-11-01'), pd.Timestamp('2016-11-14'))
    ]

    for idx, row in all_sigs.iterrows():
        # Check Macro Event Filter
        is_news_event = False
        for event_name, start_dt, end_dt in MACRO_EVENTS_2016:
            if start_dt <= idx <= end_dt:
                print(f"[{idx}] {row['trade_type']} | Entry: {row['trap_entry']:.5f} | SKIPPED: Macro Event Filter ({event_name})")
                is_news_event = True
                break
                
        if is_news_event:
            continue
            
        ts = row['trap_entry']
        entry_price = ts
        ts_time = idx
        
        stop_loss = row['trap_stop_loss']
        ctop = row.get('trap_cons_top', np.nan)
        cbot = row.get('trap_cons_bottom', np.nan)
        is_short = 'Short' in row['trade_type']
        
        # Determine targets with NO LOOKAHEAD bias
        if is_short:
            tp1 = cbot
            past_swings = ds_indexed[ds_indexed.index <= ts_time]
            swing_lows = past_swings[past_swings['HighLow'] == -1]['Level']
            valid_lows = swing_lows[swing_lows < (tp1 if pd.notna(tp1) else entry_price)]
            tp2 = valid_lows.max() if not valid_lows.empty else np.nan
        else:
            tp1 = ctop
            past_swings = ds_indexed[ds_indexed.index <= ts_time]
            swing_highs = past_swings[past_swings['HighLow'] == 1]['Level']
            valid_highs = swing_highs[swing_highs > (tp1 if pd.notna(tp1) else entry_price)]
            tp2 = valid_highs.min() if not valid_highs.empty else np.nan

        # Future simulation path (strict causal forward-walk)
        future = df_15m[df_15m.index >= ts_time]
        
        trade_active = True
        hit_tp1 = False
        hit_tp2 = False
        hit_sl = False
        exit_time = None
        current_sl = stop_loss

        for f_idx, f_row in future.iterrows():
            if is_short:
                if f_row['high'] >= current_sl:
                    hit_sl = True
                    exit_time = f_idx
                    trade_active = False
                    break
                
                if not hit_tp1 and pd.notna(tp1) and f_row['low'] <= tp1:
                    hit_tp1 = True
                    current_sl = entry_price # Move to breakeven
                    if pd.isna(tp2) or f_row['low'] <= tp2:
                        hit_tp2 = True if not pd.isna(tp2) else False
                        exit_time = f_idx
                        trade_active = False
                        break
                        
                if hit_tp1 and pd.notna(tp2) and f_row['low'] <= tp2:
                    hit_tp2 = True
                    exit_time = f_idx
                    trade_active = False
                    break

            else:
                if f_row['low'] <= current_sl:
                    hit_sl = True
                    exit_time = f_idx
                    trade_active = False
                    break
                
                if not hit_tp1 and pd.notna(tp1) and f_row['high'] >= tp1:
                    hit_tp1 = True
                    current_sl = entry_price # Move to breakeven
                    if pd.isna(tp2) or f_row['high'] >= tp2:
                        hit_tp2 = True if not pd.isna(tp2) else False
                        exit_time = f_idx
                        trade_active = False
                        break
                        
                if hit_tp1 and pd.notna(tp2) and f_row['high'] >= tp2:
                    hit_tp2 = True
                    exit_time = f_idx
                    trade_active = False
                    break
                    
        # Max hold time: 5 days
        if trade_active and exit_time is None:
            exit_time = ts_time + pd.Timedelta(days=5)

        duration = exit_time - ts_time if exit_time else pd.Timedelta(0)
        total_durations.append(duration)

        total_trades += 1
        if hit_sl and not hit_tp1: 
            full_sl_hits += 1
        if hit_sl and hit_tp1:
            be_sl_hits += 1
        if hit_tp1: tp1_hits += 1
        if hit_tp2: tp2_hits += 1

        sl_type = 'BE' if (hit_sl and hit_tp1) else ('Full SL' if hit_sl else 'None')
        
        # POST-SL THESIS CHECK:
        # If we took a full SL, did price eventually reach TP1 anyway within 10 days?
        # This tells us: was the ANALYSIS correct but the ENTRY just got knocked out by noise?
        thesis_vindicated = False
        if hit_sl and not hit_tp1 and pd.notna(tp1) and exit_time is not None:
            post_sl_window = df_15m[(df_15m.index > exit_time) & 
                                     (df_15m.index <= exit_time + pd.Timedelta(days=10))]
            for _, post_row in post_sl_window.iterrows():
                if is_short and post_row['low'] <= tp1:
                    thesis_vindicated = True
                    break
                elif not is_short and post_row['high'] >= tp1:
                    thesis_vindicated = True
                    break

        vindicated_str = ' | Direction VINDICATED post-SL [YES]' if thesis_vindicated else ' | Thesis WRONG [NO]' if (hit_sl and not hit_tp1) else ''
        print(f"[{ts_time}] {row['trade_type']} | Entry: {entry_price:.5f} | TP1: {hit_tp1} | TP2: {hit_tp2} | SL: {sl_type} | Dur: {duration.total_seconds()/3600:.1f}h{vindicated_str}")

    print("\n================ BACKTEST RESULTS (2016) ================")
    print(f"Total Setups: {total_trades}")
    if total_trades > 0:
        print(f"Full Stop Loss Hit Rate: {full_sl_hits/total_trades*100:.1f}%")
        print(f"Breakeven Stop Hit Rate: {be_sl_hits/total_trades*100:.1f}%")
        print(f"TP1 Achieved Rate (Gross): {tp1_hits/total_trades*100:.1f}%")
    if tp1_hits > 0:
        print(f"TP2 Achieved (of those that hit TP1): {tp2_hits/tp1_hits*100:.1f}%")
    avg_dur = sum(total_durations, pd.Timedelta(0)) / total_trades if total_trades else pd.Timedelta(0)
    print(f"Average Trade Duration: {avg_dur.total_seconds()/3600:.1f} hours")
    print("=========================================================\n")

if __name__ == "__main__":
    run_backtest()
