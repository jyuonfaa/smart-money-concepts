import pandas as pd

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_15m = df_raw.resample('15min').agg({
    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
}).dropna().loc['2016-08-01':'2016-10-01']

signals = [
    ('2016-09-06 10:00:00', 0.76238, 0.76628, 0.76143, 0.74883),
    ('2016-09-07 08:30:00', 0.76830, 0.76926, 0.76702, 0.74883),
    ('2016-09-22 02:00:00', 0.76365, 0.76628, 0.76352, 0.74883),
    ('2016-09-23 02:30:00', 0.76442, 0.76628, 0.76352, 0.74883),
    ('2016-09-26 08:45:00', 0.76373, 0.76628, 0.76352, 0.74883),
    ('2016-09-26 21:30:00', 0.76331, 0.76628, 0.76252, 0.74883),
    ('2016-09-28 14:15:00', 0.76802, 0.76926, 0.76702, 0.74883)
]

results = []
for ts_str, entry, stop, tp1, tp2 in signals:
    idx = pd.to_datetime(ts_str)
    
    # We are SHORT (Bearish trap)
    risk = stop - entry
    reward = entry - tp1
    rr = reward / risk if risk > 0 else 0
    
    future = df_15m.loc[idx:]
    outcome = 'OPEN'
    exit_idx = None
    
    for f_idx, row in future.iloc[1:].iterrows():
        if row['high'] >= stop:
            outcome = 'LOSS'
            exit_idx = f_idx
            break
        elif row['low'] <= tp1:
            outcome = 'WIN'
            exit_idx = f_idx
            break
            
    dur = exit_idx - idx if exit_idx else pd.Timedelta(0)
    results.append({
        'Date': ts_str,
        'Outcome': outcome,
        'Risk_Pips': risk*10000,
        'Reward_Pips': reward*10000,
        'RR': rr,
        'Duration': dur
    })

res_df = pd.DataFrame(results)
wins = len(res_df[res_df['Outcome']=='WIN'])
losses = len(res_df[res_df['Outcome']=='LOSS'])
win_rate = wins / len(res_df) * 100

print(res_df.to_string())
print(f"\nWin Rate: {win_rate:.1f}% ({wins}/{len(res_df)})")
print(f"Avg Risk: {res_df['Risk_Pips'].mean():.1f} pips")
print(f"Avg Reward (TP1): {res_df['Reward_Pips'].mean():.1f} pips")
print(f"Avg RR: {res_df['RR'].mean():.2f}")
print(f"Avg Duration: {res_df['Duration'].mean()}")
