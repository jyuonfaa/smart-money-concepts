import pandas as pd
import numpy as np
from smartmoneyconcepts.smc import smc

# Create dummy data for 20 days
dates = pd.date_range('2023-01-01', periods=20, freq='D')

# Asset: Makes a Lower Low
asset_data = {
    'open': np.random.rand(20) * 10 + 100,
    'high': np.random.rand(20) * 10 + 110,
    'low': np.random.rand(20) * 10 + 90,
    'close': np.random.rand(20) * 10 + 100,
}
# Force a Lower Low at day 10 vs day 5
asset_data['low'][5] = 80
asset_data['low'][10] = 75

asset_ohlc = pd.DataFrame(asset_data, index=dates)

# Benchmark (DXY): Fails to make a Higher High
bm_data = {
    'open': np.random.rand(20) * 10 + 100,
    'high': np.random.rand(20) * 10 + 110,
    'low': np.random.rand(20) * 10 + 90,
    'close': np.random.rand(20) * 10 + 100,
}
bm_data['high'][5] = 120
bm_data['high'][10] = 115 # Failed to make HH

bm_ohlc = pd.DataFrame(bm_data, index=dates)

# Mock swings
swings = pd.DataFrame({
    'ts': [dates[5], dates[10]],
    'p': [80.0, 75.0],
    'type': ['LOW', 'LOW']
})

# Mock FVG: Bullish FVG appears at day 12
fvg_df = pd.DataFrame(index=dates)
fvg_df['FVG'] = np.nan
fvg_df.loc[dates[12], 'FVG'] = 1

# Mock Liquidity: Old Low swept at day 10
liq_df = pd.DataFrame(index=dates)
liq_df['Liquidity'] = np.nan
liq_df['Level'] = np.nan
liq_df.loc[dates[5], 'Liquidity'] = -1
liq_df.loc[dates[5], 'Level'] = 80.0

# Run SMT divergence
res = smc.smt_divergence(
    asset_ohlc, 
    bm_ohlc, 
    swings, 
    correlation="inverse", 
    lookaround_bars=5,
    fvg_df=fvg_df,
    liquidity_df=liq_df
)

print(res[['smt_bias', 'smt_bullish_div', 'smt_confirmed', 'smt_at_liquidity']].dropna(subset=['smt_bullish_div'])[res['smt_bullish_div'] == True])
