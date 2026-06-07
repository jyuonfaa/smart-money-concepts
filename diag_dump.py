import pandas as pd
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

print('Loading data...')
path = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_15m_full = df_raw.loc['2016-08-01':'2016-10-31'].resample('15min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

print('Running scanners...')
swings = smc.swing_highs_lows_v4(df_15m_full)
liq = smc.liquidity(df_15m_full, swings)
fvgs = smc.fvg(df_15m_full)
cons = smc.consolidation(df_15m_full, prd=10, conslen=5)

df_15m = df_15m_full.loc['2016-09-01':'2016-09-30']
swings_a = swings[swings['ts'].isin(df_15m.index) | (swings['ts'] < df_15m.index[0])]
liq_a = liq.loc[df_15m.index]
exp = fvgs.loc[df_15m.index][['FVG','Top','Bottom','CE','MitigatedIndex']].copy()
exp.columns = ['Expansion','Top','Bottom','CE','MitigatedIndex']
cons_a = cons.loc[df_15m.index]

print('Running state machine...')
sm = PriceDeliveryStateMachine()
audit = sm.process(ohlc=df_15m, consolidation=cons_a, expansion=exp, liquidity=liq_a, swing_hl=swings_a)

print('\n--- RAW STATE DUMP: SEP 11 TO SEP 18 ---')
subset = audit.loc['2016-09-11':'2016-09-18']

for idx, row in subset.iterrows():
    close = df_15m.loc[idx, 'close']
    print(f"{idx} | Close: {close:.5f} | State: {row['State']} | Obs: {row['Obstruction']}")
    
print("\n--- Summary of Sep 11-18 States ---")
print(subset['State'].value_counts())
