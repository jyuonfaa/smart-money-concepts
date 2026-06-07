import pandas as pd
import numpy as np

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')
df_15m = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

episodes = [
    ('2016-04-14', 'bear', 0.76539),
    ('2016-06-21', 'bear', 0.74680), # Wait, Jun 21 is a False Bear Flag (Long Trap) in the notes! But our code calls it a 'bear' episode?
    ('2016-10-19', 'bear', 0.76970),
    ('2016-11-08', 'bear', 0.76800),
]

for ep_date_str, ep_type, ctop in episodes:
    print(f"\n=== {ep_date_str}  type={ep_type}  ctop={ctop} ===")
    ep_ts = pd.Timestamp(ep_date_str)
    search_start = ep_ts
    
    # 1. Scan for a Swing Low (for bear) or Swing High (for bull) to form
    # We'll just look for a local peak/trough in the next day
    ltf_sub = df_15m[(df_15m.index >= search_start) & (df_15m.index <= search_start + pd.Timedelta(days=2))]
    
    if len(ltf_sub) < 10:
        continue
        
    highs = ltf_sub['high'].values
    lows = ltf_sub['low'].values
    closes = ltf_sub['close'].values
    opens = ltf_sub['open'].values
    times = ltf_sub.index
    
    if ep_type == 'bear': # Short Trap (False Bull Flag) -> We need a breakdown
        # Wait for price to drop below a previous local swing low, creating displacement.
        # Find local swing lows:
        ob_bot, ob_top = np.nan, np.nan
        for i in range(2, len(ltf_sub) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_low = lows[i]
                # Look for a candle that closes below this swing low
                for j in range(i + 3, len(ltf_sub)):
                    if closes[j] < swing_low:
                        # Breakdown found! Now find the "last bullish candle" (bearish OB) prior to the move down
                        # We search backwards from j to find the highest up-candle body
                        ob_cand_idx = -1
                        for k in range(j-1, i, -1):
                            if closes[k] > opens[k]: # Up candle
                                ob_cand_idx = k
                                break
                        if ob_cand_idx != -1:
                            ob_top = max(opens[ob_cand_idx], closes[ob_cand_idx]) # ICT OB body
                            ob_bot = min(opens[ob_cand_idx], closes[ob_cand_idx])
                            
                            # Entry is a return to this zone
                            for m in range(j + 1, len(ltf_sub)):
                                if highs[m] >= ob_bot:
                                    print(f"  -> SHORT ENTRY at {times[m]} (OB formed at {times[ob_cand_idx]}, break at {times[j]})")
                                    ob_bot = -1 # prevent multiple
                                    break
                            if ob_bot == -1: break
                if ob_bot == -1: break
