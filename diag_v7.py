import pandas as pd
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

path = "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv"
df_raw = pd.read_csv(path, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_15m_full = df_raw.loc['2016-08-01':'2016-10-31'].resample('15min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

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

sm = PriceDeliveryStateMachine()
audit = sm.process(ohlc=df_15m, consolidation=cons_a, expansion=exp, liquidity=liq_a, swing_hl=swings_a)

# Check obstruction counts for Sep 12-15
mask = (audit.index >= '2016-09-12') & (audit.index <= '2016-09-15')
subset = audit[mask]
obs_vals = sorted(subset['Obstruction'].unique())
print(f"Sep 12-15 obstruction values: {obs_vals}")
obs_dist = subset['Obstruction'].value_counts().to_dict()
print(f"Sep 12-15 obstruction dist: {obs_dist}")

# Check sig swings 
sig_swings = swings_a[swings_a['label'].str.contains('Religious', na=False)]
print(f"\nSig swings total: {len(sig_swings)}")
sept_swings = sig_swings[(sig_swings['ts'] >= '2016-09-01') & (sig_swings['ts'] <= '2016-09-30')]
print(f"Sig swings Sept: {len(sept_swings)}")
for _, s in sept_swings.iterrows():
    print(f"  {s['ts']} {s['type']} @ {s['p']:.5f}")

# Check price range Sep 8-14
sept_8 = df_15m.loc['2016-09-08':'2016-09-08']
sept_14 = df_15m.loc['2016-09-14':'2016-09-14']
if not sept_8.empty and not sept_14.empty:
    print(f"\nSep 8 range: {sept_8['low'].min():.5f} - {sept_8['high'].max():.5f}")
    print(f"Sep 14 range: {sept_14['low'].min():.5f} - {sept_14['high'].max():.5f}")

# Check what the macro boundary is
print(f"\nMacro cons zones from cons detector:")
cons_sept = cons_a[cons_a['Consolidation'].notna()]
if not cons_sept.empty:
    print(f"  First cons: {cons_sept.index[0]}, Top={cons_sept.iloc[0]['Top']:.5f}, Bot={cons_sept.iloc[0]['Bottom']:.5f}")
    print(f"  Last cons: {cons_sept.index[-1]}, Top={cons_sept.iloc[-1]['Top']:.5f}, Bot={cons_sept.iloc[-1]['Bottom']:.5f}")
    # Find distinct zones
    gaps = cons_sept.index.to_series().diff()
    big_gaps = gaps[gaps > pd.Timedelta(hours=6)]
    print(f"  Distinct zone breaks (>6h gap): {len(big_gaps)}")
    for idx in big_gaps.index:
        print(f"    Gap at {idx}")
