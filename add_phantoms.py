import pandas as pd
import numpy as np

def _trendline_phantoms(ohlc, swings):
    """
    Detects False Trendline (Phantom) Traps from Month 3 Video 7.
    
    A Bullish Trap (Bearish Retail Trendline) is formed by 3 consecutive Lower Highs.
    The Trap level is the lowest low between the 2nd and 3rd Lower Highs.
    
    A Bearish Trap (Bullish Retail Trendline) is formed by 3 consecutive Higher Lows.
    The Trap level is the highest high between the 2nd and 3rd Higher Lows.
    
    Returns a DataFrame indicating where the traps exist.
    """
    result = pd.DataFrame(index=ohlc.index)
    result['bullish_trap_price'] = np.nan  # Support to buy
    result['bearish_trap_price'] = np.nan  # Resistance to sell
    
    # Extract only High swings and Low swings
    highs = swings[swings['HighLevel'] == 1].copy()
    lows = swings[swings['LowLevel'] == 1].copy()
    
    # Find Bullish Traps (3 consecutive Lower Highs)
    if len(highs) >= 3:
        for i in range(len(highs) - 2):
            h1 = highs.iloc[i]
            h2 = highs.iloc[i+1]
            h3 = highs.iloc[i+2]
            
            # Check for 3 consecutive lower highs
            if h1['High'] > h2['High'] > h3['High']:
                # The trap is the lowest low between h2 and h3
                t2 = h2['ts']
                t3 = h3['ts']
                # Search ohlc between t2 and t3 (inclusive)
                mask = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    trap_price = float(window['low'].min())
                    # The trap becomes active after the 3rd touch (h3)
                    result.loc[t3, 'bullish_trap_price'] = trap_price

    # Find Bearish Traps (3 consecutive Higher Lows)
    if len(lows) >= 3:
        for i in range(len(lows) - 2):
            l1 = lows.iloc[i]
            l2 = lows.iloc[i+1]
            l3 = lows.iloc[i+2]
            
            # Check for 3 consecutive higher lows
            if l1['Low'] < l2['Low'] < l3['Low']:
                # The trap is the highest high between l2 and l3
                t2 = l2['ts']
                t3 = l3['ts']
                # Search ohlc between t2 and t3 (inclusive)
                mask = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    trap_price = float(window['high'].max())
                    # The trap becomes active after the 3rd touch (l3)
                    result.loc[t3, 'bearish_trap_price'] = trap_price
                    
    # Forward fill the traps so they persist until hit
    result['bullish_trap_price'] = result['bullish_trap_price'].ffill()
    result['bearish_trap_price'] = result['bearish_trap_price'].ffill()
    
    return result

with open('smartmoneyconcepts/smc.py', 'r') as f:
    content = f.read()

import inspect
func_code = inspect.getsource(_trendline_phantoms)
func_code += "\nsmc.trendline_phantoms = _trendline_phantoms\n"

if "smc.trendline_phantoms = _trendline_phantoms" not in content:
    with open('smartmoneyconcepts/smc.py', 'a') as f:
        f.write("\n\n" + func_code)
    print("Added smc.trendline_phantoms to smc.py")
else:
    print("Function already exists in smc.py")
