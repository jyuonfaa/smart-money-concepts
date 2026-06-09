with open('smartmoneyconcepts/smc.py', 'r') as f:
    lines = f.readlines()

clean_lines = lines[:2094]

func_code = """
def _trendline_phantoms(ohlc, swings):
    \"\"\"
    Detects False Trendline (Phantom) Traps from Month 3 Video 7.
    
    Returns a DataFrame with columns:
    - trap_interim: The price of the high/low between touches 2 and 3
    - trap_point2: The price of the 2nd touch
    - trap_type: 1 for Bullish Trap (buy support), -1 for Bearish Trap (sell resistance)
    \"\"\"
    import pandas as pd
    import numpy as np
    
    result = pd.DataFrame(index=ohlc.index)
    result['trap_interim'] = np.nan
    result['trap_point2'] = np.nan
    result['trap_type'] = 0
    
    # Extract only High swings and Low swings
    highs = swings[swings['type'] == 'HIGH'].copy()
    lows = swings[swings['type'] == 'LOW'].copy()
    
    # Find Bullish Traps (3 consecutive Lower Highs)
    if len(highs) >= 3:
        for i in range(len(highs) - 2):
            h1 = highs.iloc[i]
            h2 = highs.iloc[i+1]
            h3 = highs.iloc[i+2]
            
            # Check for 3 consecutive lower highs
            if h1['p'] > h2['p'] > h3['p']:
                t2 = h2['ts']
                t3 = h3['ts']
                # The trap_interim is the lowest low between h2 and h3
                mask = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    result.loc[t3, 'trap_interim'] = float(window['low'].min())
                    result.loc[t3, 'trap_point2'] = float(h2['p'])
                    result.loc[t3, 'trap_type'] = 1

    # Find Bearish Traps (3 consecutive Higher Lows)
    if len(lows) >= 3:
        for i in range(len(lows) - 2):
            l1 = lows.iloc[i]
            l2 = lows.iloc[i+1]
            l3 = lows.iloc[i+2]
            
            # Check for 3 consecutive higher lows
            if l1['p'] < l2['p'] < l3['p']:
                t2 = l2['ts']
                t3 = l3['ts']
                # The trap_interim is the highest high between l2 and l3
                mask = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    result.loc[t3, 'trap_interim'] = float(window['high'].max())
                    result.loc[t3, 'trap_point2'] = float(l2['p'])
                    result.loc[t3, 'trap_type'] = -1
                    
    # Do NOT ffill here. We let the execution engine consume them.
    return result

smc.trendline_phantoms = _trendline_phantoms

def _phantom_signals(ohlc, phantoms, ob_df, htf_bias=None):
    \"\"\"
    Executes trades on Phantom Traps.
    A signal is fired if:
    1. htf_bias aligns with the trap_type
    2. Price sweeps the interim trap (turtle soup) OR taps an Order Block at the interim trap level.
    
    The function also returns the mathematical Point 2 Take Profit target.
    Once a trap is executed, it is consumed and invalidated.
    \"\"\"
    import pandas as pd
    import numpy as np
    
    signals = pd.DataFrame(index=ohlc.index)
    signals['signal'] = 0
    signals['trigger_type'] = ""
    signals['target_price'] = np.nan
    
    if htf_bias is None:
        htf_bias = pd.Series(1, index=ohlc.index) # Default everything to bullish for testing if not provided
        
    current_bullish_trap = None
    current_bearish_trap = None
        
    for i in range(len(ohlc)):
        ts = ohlc.index[i]
        
        # Check for new traps
        t_type = phantoms['trap_type'].iloc[i]
        if t_type == 1:
            current_bullish_trap = {
                'interim': phantoms['trap_interim'].iloc[i],
                'point2': phantoms['trap_point2'].iloc[i]
            }
        elif t_type == -1:
            current_bearish_trap = {
                'interim': phantoms['trap_interim'].iloc[i],
                'point2': phantoms['trap_point2'].iloc[i]
            }
            
        bias = htf_bias.iloc[i]
        low = ohlc['low'].iloc[i]
        high = ohlc['high'].iloc[i]
        
        ob_top = ob_df['Top'].iloc[i] if 'Top' in ob_df.columns else np.nan
        ob_bottom = ob_df['Bottom'].iloc[i] if 'Bottom' in ob_df.columns else np.nan
        ob_type = ob_df['OB'].iloc[i] if 'OB' in ob_df.columns else 0
        
        # Bullish Execution
        if current_bullish_trap is not None and not pd.isna(bias) and bias == 1:
            trap_interim = current_bullish_trap['interim']
            trap_point2 = current_bullish_trap['point2']
            
            swept_interim = low <= trap_interim
            
            if swept_interim:
                signals.loc[ts, 'signal'] = 1
                signals.loc[ts, 'trigger_type'] = "Turtle Soup (Interim Low)"
                signals.loc[ts, 'target_price'] = trap_point2
                current_bullish_trap = None # Consume the trap
            elif ob_type == 1 and not pd.isna(ob_top) and low <= ob_top and ob_bottom <= trap_interim <= ob_top:
                signals.loc[ts, 'signal'] = 1
                signals.loc[ts, 'trigger_type'] = "OB Tap (Interim Low)"
                signals.loc[ts, 'target_price'] = trap_point2
                current_bullish_trap = None # Consume the trap
                
        # Bearish Execution
        if current_bearish_trap is not None and not pd.isna(bias) and bias == -1:
            trap_interim = current_bearish_trap['interim']
            trap_point2 = current_bearish_trap['point2']
            
            swept_interim = high >= trap_interim
            
            if swept_interim:
                signals.loc[ts, 'signal'] = -1
                signals.loc[ts, 'trigger_type'] = "Turtle Soup (Interim High)"
                signals.loc[ts, 'target_price'] = trap_point2
                current_bearish_trap = None # Consume the trap
            elif ob_type == -1 and not pd.isna(ob_bottom) and high >= ob_bottom and ob_bottom <= trap_interim <= ob_top:
                signals.loc[ts, 'signal'] = -1
                signals.loc[ts, 'trigger_type'] = "OB Tap (Interim High)"
                signals.loc[ts, 'target_price'] = trap_point2
                current_bearish_trap = None # Consume the trap
                
    return signals

smc.phantom_signals = _phantom_signals
"""

with open('smartmoneyconcepts/smc.py', 'w') as f:
    f.writelines(clean_lines)
    f.write(func_code)

print("smc.py rewritten with trap consumption logic successfully.")
