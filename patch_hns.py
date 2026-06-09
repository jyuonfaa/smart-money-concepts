import pandas as pd
import numpy as np

def append_to_smc():
    code = """

def _false_hns_patterns(ohlc, swings):
    \"\"\"
    Detects False Head and Shoulders Traps (Month 3 Video 8).
    \"\"\"
    # Clean swings
    swing_arr = swings[~swings['type'].isna()].copy()
    
    # Store detected patterns
    patterns = []
    
    # Iterate through swings in chunks of 5
    for i in range(len(swing_arr) - 4):
        window = swing_arr.iloc[i:i+5]
        types = window['type'].values
        prices = window['p'].values
        timestamps = window['ts'].values
        
        # Bullish Trap: Standard H&S (H, L, H, L, H)
        if (types[0] == 'HIGH' and types[1] == 'LOW' and 
            types[2] == 'HIGH' and types[3] == 'LOW' and 
            types[4] == 'HIGH'):
            
            ls = prices[0]
            l1 = prices[1]
            t1 = timestamps[1]
            
            head = prices[2]
            
            l2 = prices[3]
            t2 = timestamps[3]
            rs = prices[4]
            
            # Head must be highest
            if head > ls and head > rs:
                patterns.append({
                    'trap_type': 1, # Bullish trap
                    'trap_ts': timestamps[4],
                    'p1': l1,
                    't1': t1,
                    'p2': l2,
                    't2': t2,
                    'target': head
                })
                
        # Bearish Trap: Inverted H&S (L, H, L, H, L)
        elif (types[0] == 'LOW' and types[1] == 'HIGH' and 
              types[2] == 'LOW' and types[3] == 'HIGH' and 
              types[4] == 'LOW'):
              
            ls = prices[0]
            h1 = prices[1]
            t1 = timestamps[1]
            
            head = prices[2]
            
            h2 = prices[3]
            t2 = timestamps[3]
            rs = prices[4]
            
            # Head must be lowest
            if head < ls and head < rs:
                patterns.append({
                    'trap_type': -1, # Bearish trap
                    'trap_ts': timestamps[4],
                    'p1': h1,
                    't1': t1,
                    'p2': h2,
                    't2': t2,
                    'target': head
                })
                
    return pd.DataFrame(patterns) if patterns else pd.DataFrame(columns=['trap_type', 'trap_ts', 'p1', 't1', 'p2', 't2', 'target'])

def _hns_signals(ohlc, patterns, htf_bias=None):
    \"\"\"
    Executes trades on the diagonal neckline sweep.
    \"\"\"
    signals = pd.DataFrame(index=ohlc.index)
    signals['signal'] = 0
    signals['trigger_type'] = np.nan
    signals['target_price'] = np.nan
    
    if patterns.empty:
        return signals
        
    if htf_bias is None:
        htf_bias = pd.Series(0, index=ohlc.index)
        
    consumed_traps = set()
    
    for i, (ts, row) in enumerate(ohlc.iterrows()):
        bias = htf_bias.loc[ts] if ts in htf_bias.index else 0
        if bias == 0:
            continue
            
        high = row['high']
        low = row['low']
        
        # Get active patterns up to this point
        active = patterns[patterns['trap_ts'] < ts]
        
        for _, trap in active.iterrows():
            trap_ts = trap['trap_ts']
            if trap_ts in consumed_traps:
                continue
                
            trap_type = trap['trap_type']
            if trap_type != bias:
                continue
                
            # Project Diagonal Neckline
            t1 = trap['t1']
            t2 = trap['t2']
            p1 = trap['p1']
            p2 = trap['p2']
            target = trap['target']
            
            # Time difference in seconds
            dt1 = t1.timestamp()
            dt2 = t2.timestamp()
            dt_now = ts.timestamp()
            
            if dt2 == dt1:
                continue
                
            slope = (p2 - p1) / (dt2 - dt1)
            projected_neckline = p2 + slope * (dt_now - dt2)
            
            if trap_type == 1:
                # Bullish Trap: Need low to sweep below neckline
                if low <= projected_neckline:
                    signals.loc[ts, 'signal'] = 1
                    signals.loc[ts, 'trigger_type'] = "H&S Neckline Sweep BUY"
                    signals.loc[ts, 'target_price'] = target
                    consumed_traps.add(trap_ts)
                    
            elif trap_type == -1:
                # Bearish Trap: Need high to sweep above neckline
                if high >= projected_neckline:
                    signals.loc[ts, 'signal'] = -1
                    signals.loc[ts, 'trigger_type'] = "Inv H&S Neckline Sweep SELL"
                    signals.loc[ts, 'target_price'] = target
                    consumed_traps.add(trap_ts)
                    
    return signals

smc.false_hns_patterns = _false_hns_patterns
smc.hns_signals = _hns_signals
"""
    with open('smartmoneyconcepts/smc.py', 'a') as f:
        f.write(code)
    print("Patched smc.py successfully.")

if __name__ == '__main__':
    append_to_smc()
