import pandas as pd
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
swings_d = smc.swing_highs_lows(df_daily, swing_length=10)
ob = smc.ob(df_daily, swings_d)
print('Actual OB columns:', list(ob.columns))
print(ob.dropna().head())
