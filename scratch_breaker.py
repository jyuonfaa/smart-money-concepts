import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swings = smc.swing_highs_lows(df_daily, swing_length=10)

def breaker_blocks(ohlc: pd.DataFrame, swing_highs_lows: pd.DataFrame) -> pd.Series:
    breaker = np.zeros(len(ohlc), dtype=np.int32)
    top = np.zeros(len(ohlc), dtype=np.float32)
    bottom = np.zeros(len(ohlc), dtype=np.float32)
    broken_index = np.zeros(len(ohlc), dtype=np.int32)

    swing_indices = np.where(~np.isnan(swing_highs_lows["HighLow"]))[0]
    
    for i in range(2, len(swing_indices)):
        prev_swing = swing_indices[i-2]
        mid_swing = swing_indices[i-1]
        curr_swing = swing_indices[i]
        
        # Bearish Breaker
        if (swing_highs_lows["HighLow"].iloc[prev_swing] == 1 and 
            swing_highs_lows["HighLow"].iloc[mid_swing] == -1 and 
            swing_highs_lows["HighLow"].iloc[curr_swing] == 1):
            
            if ohlc["high"].iloc[curr_swing] > ohlc["high"].iloc[prev_swing]:
                breaker_idx = mid_swing
                for j in range(mid_swing, prev_swing, -1):
                    if ohlc["close"].iloc[j] < ohlc["open"].iloc[j]:
                        breaker_idx = j
                        break
                
                breaker_top = ohlc["high"].iloc[breaker_idx]
                breaker_bottom = ohlc["low"].iloc[breaker_idx]
                
                for k in range(curr_swing + 1, len(ohlc)):
                    if ohlc["close"].iloc[k] < breaker_bottom:
                        breaker[breaker_idx] = -1
                        top[breaker_idx] = breaker_top
                        bottom[breaker_idx] = breaker_bottom
                        broken_index[breaker_idx] = k
                        break

        # Bullish Breaker
        elif (swing_highs_lows["HighLow"].iloc[prev_swing] == -1 and 
              swing_highs_lows["HighLow"].iloc[mid_swing] == 1 and 
              swing_highs_lows["HighLow"].iloc[curr_swing] == -1):
            
            if ohlc["low"].iloc[curr_swing] < ohlc["low"].iloc[prev_swing]:
                breaker_idx = mid_swing
                for j in range(mid_swing, prev_swing, -1):
                    if ohlc["close"].iloc[j] > ohlc["open"].iloc[j]:
                        breaker_idx = j
                        break
                
                breaker_top = ohlc["high"].iloc[breaker_idx]
                breaker_bottom = ohlc["low"].iloc[breaker_idx]
                
                for k in range(curr_swing + 1, len(ohlc)):
                    if ohlc["close"].iloc[k] > breaker_top:
                        breaker[breaker_idx] = 1
                        top[breaker_idx] = breaker_top
                        bottom[breaker_idx] = breaker_bottom
                        broken_index[breaker_idx] = k
                        break

    breaker = np.where(breaker == 0, np.nan, breaker)
    top = np.where(top == 0, np.nan, top)
    bottom = np.where(bottom == 0, np.nan, bottom)
    broken_index = np.where(broken_index == 0, np.nan, broken_index)

    return pd.concat(
        [
            pd.Series(breaker, name="Breaker"),
            pd.Series(top, name="Top"),
            pd.Series(bottom, name="Bottom"),
            pd.Series(broken_index, name="BrokenIndex"),
        ],
        axis=1,
    )

breakers = breaker_blocks(df_daily, swings)
breakers.index = df_daily.index
valid_breakers = breakers.dropna()
print(f"Found {len(valid_breakers)} Breaker Blocks on Daily AUDUSD.")
print(valid_breakers.head())
