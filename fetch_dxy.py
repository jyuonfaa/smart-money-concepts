import pandas as pd
import numpy as np

def create_synthetic_dxy():
    print("Generating Synthetic DXY Data for algorithmic testing...")
    
    # Load local AUDUSD
    df_raw = pd.read_csv(
        'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
        sep=';', names=['date','open','high','low','close','volume'],
        index_col=False
    )
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    
    # Resample to Daily
    daily = df_raw.resample('1D').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    # Synthetic Inverse (DXY)
    # DXY moves inversely to AUDUSD. We invert it, scale it to ~90-100 (DXY range), 
    # and add a small random walk to create artificial divergences for the detector.
    
    np.random.seed(42) # Deterministic for testing
    
    dxy = pd.DataFrame(index=daily.index)
    scale = 100 * (1 / daily['close'].mean())
    
    # Add cumulative noise to create structural divergences
    noise = np.cumsum(np.random.normal(0, 0.005, len(daily)))
    
    dxy['open'] = (1 / daily['open']) * scale * (1 + noise)
    dxy['close'] = (1 / daily['close']) * scale * (1 + noise)
    dxy['high'] = (1 / daily['low']) * scale * (1 + noise)
    dxy['low'] = (1 / daily['high']) * scale * (1 + noise)
    dxy['volume'] = daily['volume']
    
    # Ensure high > low
    dxy['high'], dxy['low'] = np.maximum(dxy['open'], dxy['close']) * 1.001, np.minimum(dxy['open'], dxy['close']) * 0.999
    
    dxy.to_csv("HISTDATA_COM_ASCII_AUDUSD_M12016/DXY_Daily_2016.csv")
    print(f"Saved {len(dxy)} rows to HISTDATA_COM_ASCII_AUDUSD_M12016/DXY_Daily_2016.csv")

if __name__ == "__main__":
    create_synthetic_dxy()
