def _phantom_signals(ohlc, phantoms, ob_df, htf_bias=None):
    """
    Executes trades on Phantom Traps.
    A signal is fired if:
    1. htf_bias aligns with the trap_type
    2. Price sweeps the interim trap (turtle soup) OR taps an Order Block at the interim trap level.
    
    The function also returns the mathematical Point 2 Take Profit target.
    """
    import pandas as pd
    import numpy as np
    
    signals = pd.DataFrame(index=ohlc.index)
    signals['signal'] = 0
    signals['trigger_type'] = ""
    signals['target_price'] = np.nan
    
    if htf_bias is None:
        htf_bias = pd.Series(1, index=ohlc.index) # Default everything to bullish for testing if not provided
        
    for i in range(len(ohlc)):
        ts = ohlc.index[i]
        
        trap_type = phantoms['trap_type'].iloc[i]
        if trap_type == 0:
            continue
            
        bias = htf_bias.iloc[i]
        if pd.isna(bias):
            continue
            
        # Ensure HTF bias aligns with the trap
        if trap_type != bias:
            continue
            
        low = ohlc['low'].iloc[i]
        high = ohlc['high'].iloc[i]
        
        trap_interim = phantoms['trap_interim'].iloc[i]
        trap_point2 = phantoms['trap_point2'].iloc[i]
        
        ob_top = ob_df['Top'].iloc[i] if 'Top' in ob_df.columns else np.nan
        ob_bottom = ob_df['Bottom'].iloc[i] if 'Bottom' in ob_df.columns else np.nan
        ob_type = ob_df['OB'].iloc[i] if 'OB' in ob_df.columns else 0
        
        # Bullish Execution
        if trap_type == 1:
            swept_interim = low <= trap_interim
            
            if swept_interim:
                signals.loc[ts, 'signal'] = 1
                signals.loc[ts, 'trigger_type'] = "Turtle Soup (Interim Low)"
                signals.loc[ts, 'target_price'] = trap_point2
            elif ob_type == 1 and not pd.isna(ob_top) and low <= ob_top and ob_bottom <= trap_interim <= ob_top:
                signals.loc[ts, 'signal'] = 1
                signals.loc[ts, 'trigger_type'] = "OB Tap (Interim Low)"
                signals.loc[ts, 'target_price'] = trap_point2
                
        # Bearish Execution
        elif trap_type == -1:
            swept_interim = high >= trap_interim
            
            if swept_interim:
                signals.loc[ts, 'signal'] = -1
                signals.loc[ts, 'trigger_type'] = "Turtle Soup (Interim High)"
                signals.loc[ts, 'target_price'] = trap_point2
            elif ob_type == -1 and not pd.isna(ob_bottom) and high >= ob_bottom and ob_bottom <= trap_interim <= ob_top:
                signals.loc[ts, 'signal'] = -1
                signals.loc[ts, 'trigger_type'] = "OB Tap (Interim High)"
                signals.loc[ts, 'target_price'] = trap_point2
                
    return signals
