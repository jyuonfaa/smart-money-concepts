import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

def resample_data(df, tf):
    return df.resample(tf).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()

def audit_pair(name, path, sep=',', names=None, date_format=None, start_date=None, end_date=None):
    print(f"AUDITING {name} PERFORMANCE...")
    df_raw = pd.read_csv(path, sep=sep, names=names, index_col=False)
    if names:
        df_raw['date'] = pd.to_datetime(df_raw['date'], format=date_format)
    else:
        df_raw.columns = [c.lower() for c in df_raw.columns]
        df_raw['date'] = pd.to_datetime(df_raw['date'])
    
    df_raw.set_index('date', inplace=True)
    
    if start_date and end_date:
        df_raw = df_raw.loc[start_date:end_date]
    
    df_15m = resample_data(df_raw, '15min')
    df_4h = resample_data(df_raw, '4h')
    df_daily = resample_data(df_raw, '1d')
    
    swings_4h = smc.swing_highs_lows_v4(df_4h)
    voids_4h = smc.sequence_void(df_4h)
    obs_4h = smc.identify_order_block(df_4h, swings_4h)
    bos_choch_4h = smc.bos_choch(df_4h, swings_4h)
    
    signals = []
    last_signal_ts = df_15m.index[0] - pd.Timedelta(days=1)
    
    parent_h, parent_l = df_daily['high'].max(), df_daily['low'].min()
    daily_range = parent_h - parent_l
    eq = (parent_h + parent_l) / 2
    prem_zone = parent_h - (daily_range / 3)
    disc_zone = parent_l + (daily_range / 3)
    
    for i in range(100, len(df_15m)):
        ts = df_15m.index[i]
        price = df_15m['close'].iloc[i]
        
        is_buy = price < disc_zone
        is_sell = price > prem_zone
        if not (is_buy or is_sell): continue
        
        v4h_active = voids_4h[voids_4h.index <= ts]
        in_void = not v4h_active.empty and (v4h_active.iloc[-1]['bottom'] <= price <= v4h_active.iloc[-1]['top'])
        msb_4h = bos_choch_4h[(bos_choch_4h.index <= ts) & (bos_choch_4h.index > ts - pd.Timedelta(hours=168))]
        has_msb = not msb_4h.empty
        active_obs = obs_4h[obs_4h.index <= ts]
        has_ob = not active_obs.empty and (abs(active_obs.iloc[-1]['fv'] - price) < 0.0020)

        score = (1 if in_void else 0) + (1 if has_msb else 0) + (1 if has_ob else 0) + 1 + 1
        
        if score >= 4:
            if ts > last_signal_ts + pd.Timedelta(hours=24):
                window_end = ts + pd.Timedelta(hours=48) # 48h window for MFE
                df_window = df_15m.loc[ts:window_end]
                
                if is_buy:
                    mae = (price - df_window['low'].min())
                    mfe = (df_window['high'].max() - price)
                else:
                    mae = (df_window['high'].max() - price)
                    mfe = (price - df_window['low'].min())
                
                signals.append(dict(ts=ts, mae=mae*10000, mfe=mfe*10000))
                last_signal_ts = ts
                
    avg_mae = np.mean([s['mae'] for s in signals]) if signals else 0
    avg_mfe = np.mean([s['mfe'] for s in signals]) if signals else 0
    rr = avg_mfe / avg_mae if avg_mae > 0 else 0
    
    print(f"AVG MAE: {round(avg_mae, 1)} | AVG MFE: {round(avg_mfe, 1)} | R:R: {round(rr, 2)}")
    return avg_mfe, rr

if __name__ == "__main__":
    results = {}
    results['EURUSD'] = audit_pair("EURUSD", "tests/test_data/EURUSD/EURUSD_15M.csv")
    results['AUDUSD'] = audit_pair("AUDUSD", 
                                  "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv",
                                  sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'],
                                  date_format='%Y%m%d %H%M%S')
    
    print("\n--- ANNUAL PERFORMANCE SUMMARY ---")
    for pair, (mfe, rr) in results.items():
        print(f"{pair}: {round(mfe, 1)} Pips Profit (Average R:R {round(rr, 2)})")
