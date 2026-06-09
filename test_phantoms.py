import pandas as pd
from smartmoneyconcepts.smc import smc

eurusd = pd.read_csv('tests/test_data/MACRO/EURUSD_Daily_2016.csv', parse_dates=['date'], index_col='date')
swings = smc.swing_highs_lows_v4(eurusd)
highs = swings[swings['type'] == 'H'].copy()

print(f"Total Highs: {len(highs)}")
print("Sample:")
print(highs[['ts', 'p']].head(10))

for i in range(min(10, len(highs) - 2)):
    h1 = highs.iloc[i]
    h2 = highs.iloc[i+1]
    h3 = highs.iloc[i+2]
    print(f"H1: {h1['p']} | H2: {h2['p']} | H3: {h3['p']} => Descending? {h1['p'] > h2['p'] > h3['p']}")
