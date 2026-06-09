import sys
sys.path.insert(0, '.')

with open('smartmoneyconcepts/smc.py', 'r') as f:
    lines = f.readlines()

# Keep everything up to line 2094 (before _trendline_phantoms)
clean_lines = lines[:2094]

new_code = '''
def _trendline_phantoms(ohlc, swings):
    """
    Detects False Trendline (Phantom) Traps from Month 3 Video 7.
    
    Returns a DataFrame with columns:
    - trap_interim  : price of the high/low between touches 2 and 3
    - trap_point2   : price of the 2nd touch (retail stop cluster)
    - trap_touch3   : price of the 3rd touch (for limit-order entry, Gap 7)
    - trap_p1_ts    : timestamp of Point 1 (the origin swing, for FVG target lookup)
    - trap_fvg_top  : top of the FVG left by Point 1 impulse (Gap 8 secondary target)
    - trap_fvg_bot  : bottom of the FVG left by Point 1 impulse (Gap 8 secondary target)
    - trap_ts       : timestamp when the trap became active (after 3rd touch)
    - trap_type     : 1 for Bullish Trap, -1 for Bearish Trap
    """
    import pandas as pd
    import numpy as np

    result = pd.DataFrame(index=ohlc.index)
    result['trap_interim'] = np.nan
    result['trap_point2']  = np.nan
    result['trap_touch3']  = np.nan
    result['trap_p1_ts']   = pd.NaT
    result['trap_fvg_top'] = np.nan
    result['trap_fvg_bot'] = np.nan
    result['trap_ts']      = pd.NaT
    result['trap_type']    = 0

    highs = swings[swings['type'] == 'HIGH'].copy()
    lows  = swings[swings['type'] == 'LOW'].copy()

    # ------------------------------------------------------------------ #
    # Helper: find the FVG left by the Point 1 impulse candle             #
    # ICT says the impulse from Point 1 creates a Fair Value Gap           #
    # (low of the up-candle that made Point 1  ->  high of next up-candle) #
    # ------------------------------------------------------------------ #
    def _find_p1_fvg(p1_ts, direction):
        """Return (fvg_top, fvg_bot) of the FVG at Point 1 impulse, or (nan, nan)."""
        try:
            idx = ohlc.index.get_loc(p1_ts)
        except KeyError:
            return np.nan, np.nan
        # Look at the candle AT Point 1 and the one immediately after
        if idx + 1 >= len(ohlc):
            return np.nan, np.nan
        c0 = ohlc.iloc[idx]      # candle that made the Point 1 extreme
        c1 = ohlc.iloc[idx + 1]  # candle after Point 1
        if direction == 'bearish':
            # Bearish FVG (price fell from Point 1 high):
            # Gap = low of c0  to  high of c1 (if gap exists)
            if c1['high'] < c0['low']:
                return float(c0['low']), float(c1['high'])
        else:
            # Bullish FVG (price rose from Point 1 low):
            # Gap = high of c0  to  low of c1
            if c1['low'] > c0['high']:
                return float(c1['low']), float(c0['high'])
        return np.nan, np.nan

    # ------------------------------------------------------------------ #
    # Find Bullish Traps (3 consecutive Lower Highs)                       #
    # Retail draws a down-sloping resistance line; we expect price to buy  #
    # ------------------------------------------------------------------ #
    if len(highs) >= 3:
        for i in range(len(highs) - 2):
            h1 = highs.iloc[i]
            h2 = highs.iloc[i+1]
            h3 = highs.iloc[i+2]

            if h1['p'] > h2['p'] > h3['p']:
                t1 = h1['ts']
                t2 = h2['ts']
                t3 = h3['ts']
                mask   = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    # FVG at Point 1 (bearish impulse left a gap going down)
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bearish')

                    result.loc[t3, 'trap_interim']  = float(window['low'].min())
                    result.loc[t3, 'trap_point2']   = float(h2['p'])
                    result.loc[t3, 'trap_touch3']   = float(h3['p'])   # Gap 7
                    result.loc[t3, 'trap_p1_ts']    = t1
                    result.loc[t3, 'trap_fvg_top']  = fvg_top          # Gap 8
                    result.loc[t3, 'trap_fvg_bot']  = fvg_bot          # Gap 8
                    result.loc[t3, 'trap_ts']       = t3
                    result.loc[t3, 'trap_type']     = 1

    # ------------------------------------------------------------------ #
    # Find Bearish Traps (3 consecutive Higher Lows)                       #
    # Retail draws an up-sloping support line; we expect price to sell     #
    # ------------------------------------------------------------------ #
    if len(lows) >= 3:
        for i in range(len(lows) - 2):
            l1 = lows.iloc[i]
            l2 = lows.iloc[i+1]
            l3 = lows.iloc[i+2]

            if l1['p'] < l2['p'] < l3['p']:
                t1 = l1['ts']
                t2 = l2['ts']
                t3 = l3['ts']
                mask   = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    # FVG at Point 1 (bullish impulse left a gap going up)
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bullish')

                    result.loc[t3, 'trap_interim']  = float(window['high'].max())
                    result.loc[t3, 'trap_point2']   = float(l2['p'])
                    result.loc[t3, 'trap_touch3']   = float(l3['p'])   # Gap 7
                    result.loc[t3, 'trap_p1_ts']    = t1
                    result.loc[t3, 'trap_fvg_top']  = fvg_top          # Gap 8
                    result.loc[t3, 'trap_fvg_bot']  = fvg_bot          # Gap 8
                    result.loc[t3, 'trap_ts']       = t3
                    result.loc[t3, 'trap_type']     = -1

    # Forward fill so levels persist until consumed
    for col in ['trap_interim','trap_point2','trap_touch3','trap_fvg_top','trap_fvg_bot']:
        result[col] = result[col].ffill()
    result['trap_ts']    = result['trap_ts'].ffill()
    result['trap_p1_ts'] = result['trap_p1_ts'].ffill()
    result['trap_type']  = result['trap_type'].replace(0, np.nan).ffill().fillna(0)

    return result

smc.trendline_phantoms = _trendline_phantoms


def _phantom_signals(ohlc, phantoms, ob_df, htf_bias=None):
    """
    Full 3-Phase + Gap-6/7/8 Market Maker Trap Execution Engine.

    Phase 2 Entry Triggers (at the Interim Extreme):
      A. Turtle Soup  — price sweeps below/above the interim level
      B. Limit Order  — price touches the 3rd-touch trendline level (Gap 7)
      C. OB Tap       — price taps an Order Block coincident with the interim level
      D. Breaker      — price breaks a previous LTF swing in the direction of the trap (Gap 6)

    Phase 2 Target : trap_point2 (retail stop cluster)
    Secondary Target: trap_fvg_top / trap_fvg_bot (FVG from Point 1 impulse, Gap 8)

    Phase 3 Reversal (after Point 2 is swept):
      Signal : opposite direction
      Target : trap_interim (deep liquidity pool)

    Signals: signal=1 (Buy), signal=-1 (Sell)
    """
    import pandas as pd
    import numpy as np

    signals = pd.DataFrame(index=ohlc.index)
    signals['signal']          = 0
    signals['trigger_type']    = ""
    signals['target_price']    = np.nan
    signals['secondary_target'] = np.nan    # Gap 8: FVG target

    if htf_bias is None:
        htf_bias = pd.Series(1, index=ohlc.index)

    consumed_traps = set()
    phase2_fired   = set()

    # ---- Pre-compute a simple "Breaker" flag (Gap 6) ----
    # A Bearish Breaker = candle that breaks above the previous swing HIGH
    # A Bullish Breaker = candle that breaks below the previous swing LOW
    # We detect this by comparing each close to the prior bar's high/low.
    breaker_up   = ohlc['close'] > ohlc['high'].shift(1)   # breaks prior high → bearish breaker
    breaker_down = ohlc['close'] < ohlc['low'].shift(1)    # breaks prior low  → bullish breaker

    for i in range(len(ohlc)):
        ts = ohlc.index[i]

        trap_type = phantoms['trap_type'].iloc[i]
        if trap_type == 0:
            continue

        trap_ts = phantoms['trap_ts'].iloc[i]
        if pd.isna(trap_ts) or trap_ts in consumed_traps:
            continue

        bias = htf_bias.iloc[i]
        if pd.isna(bias) or trap_type != bias:
            continue

        low   = ohlc['low'].iloc[i]
        high  = ohlc['high'].iloc[i]
        close = ohlc['close'].iloc[i]

        trap_interim = phantoms['trap_interim'].iloc[i]
        trap_point2  = phantoms['trap_point2'].iloc[i]
        trap_touch3  = phantoms['trap_touch3'].iloc[i]   # Gap 7
        trap_fvg_top = phantoms['trap_fvg_top'].iloc[i]  # Gap 8
        trap_fvg_bot = phantoms['trap_fvg_bot'].iloc[i]  # Gap 8

        ob_top    = ob_df['Top'].iloc[i]    if 'Top'    in ob_df.columns else np.nan
        ob_bottom = ob_df['Bottom'].iloc[i] if 'Bottom' in ob_df.columns else np.nan
        ob_type   = ob_df['OB'].iloc[i]     if 'OB'     in ob_df.columns else 0

        # ================================================================ #
        # BULLISH TRAP (3 Lower Highs — retail sells, we buy)              #
        # ================================================================ #
        if trap_type == 1:
            swept_point2  = high >= trap_point2
            swept_interim = low  <= trap_interim
            # Gap 7: price touches or trades into the 3rd-touch resistance (the trendline itself)
            at_touch3     = high >= trap_touch3
            # Gap 6: Bearish Breaker just fired (price broke a prior LTF high → reversal signal to sell)
            breaker_fired = bool(breaker_up.iloc[i]) and high >= trap_interim

            # ---- Phase 3 (requires Phase 2 to have already fired) ---- #
            if trap_ts in phase2_fired and swept_point2:
                signals.loc[ts, 'signal']           = -1
                signals.loc[ts, 'trigger_type']     = "Phase 3 SELL — Point2 High Swept"
                signals.loc[ts, 'target_price']     = trap_interim
                signals.loc[ts, 'secondary_target'] = trap_fvg_bot if not pd.isna(trap_fvg_bot) else np.nan
                consumed_traps.add(trap_ts)

            # ---- Phase 2 — Turtle Soup (sweep of Interim Low) ---- #
            elif swept_interim and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = 1
                signals.loc[ts, 'trigger_type']     = "Phase 2 BUY — Turtle Soup"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_top if not pd.isna(trap_fvg_top) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — Limit Order at 3rd Touch (Gap 7) ---- #
            elif at_touch3 and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = 1
                signals.loc[ts, 'trigger_type']     = "Phase 2 BUY — Limit at 3rd Touch"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_top if not pd.isna(trap_fvg_top) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — Bearish Breaker at Interim (Gap 6) ---- #
            elif breaker_fired and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = 1
                signals.loc[ts, 'trigger_type']     = "Phase 2 BUY — Bearish Breaker"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_top if not pd.isna(trap_fvg_top) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — OB Tap at Interim ---- #
            elif (ob_type == 1 and not pd.isna(ob_top)
                  and low <= ob_top
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                signals.loc[ts, 'signal']           = 1
                signals.loc[ts, 'trigger_type']     = "Phase 2 BUY — OB Tap"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_top if not pd.isna(trap_fvg_top) else np.nan
                phase2_fired.add(trap_ts)

        # ================================================================ #
        # BEARISH TRAP (3 Higher Lows — retail buys, we sell)              #
        # ================================================================ #
        elif trap_type == -1:
            swept_point2  = low  <= trap_point2
            swept_interim = high >= trap_interim
            # Gap 7: price touches or trades into the 3rd-touch support (the trendline itself)
            at_touch3     = low  <= trap_touch3
            # Gap 6: Bullish Breaker just fired (price broke a prior LTF low → reversal signal to buy)
            breaker_fired = bool(breaker_down.iloc[i]) and low <= trap_interim

            # ---- Phase 3 (requires Phase 2 to have already fired) ---- #
            if trap_ts in phase2_fired and swept_point2:
                signals.loc[ts, 'signal']           = 1
                signals.loc[ts, 'trigger_type']     = "Phase 3 BUY — Point2 Low Swept"
                signals.loc[ts, 'target_price']     = trap_interim
                signals.loc[ts, 'secondary_target'] = trap_fvg_top if not pd.isna(trap_fvg_top) else np.nan
                consumed_traps.add(trap_ts)

            # ---- Phase 2 — Turtle Soup (sweep of Interim High) ---- #
            elif swept_interim and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = -1
                signals.loc[ts, 'trigger_type']     = "Phase 2 SELL — Turtle Soup"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_bot if not pd.isna(trap_fvg_bot) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — Limit Order at 3rd Touch (Gap 7) ---- #
            elif at_touch3 and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = -1
                signals.loc[ts, 'trigger_type']     = "Phase 2 SELL — Limit at 3rd Touch"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_bot if not pd.isna(trap_fvg_bot) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — Bullish Breaker at Interim (Gap 6) ---- #
            elif breaker_fired and trap_ts not in phase2_fired:
                signals.loc[ts, 'signal']           = -1
                signals.loc[ts, 'trigger_type']     = "Phase 2 SELL — Bullish Breaker"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_bot if not pd.isna(trap_fvg_bot) else np.nan
                phase2_fired.add(trap_ts)

            # ---- Phase 2 — OB Tap at Interim ---- #
            elif (ob_type == -1 and not pd.isna(ob_bottom)
                  and high >= ob_bottom
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                signals.loc[ts, 'signal']           = -1
                signals.loc[ts, 'trigger_type']     = "Phase 2 SELL — OB Tap"
                signals.loc[ts, 'target_price']     = trap_point2
                signals.loc[ts, 'secondary_target'] = trap_fvg_bot if not pd.isna(trap_fvg_bot) else np.nan
                phase2_fired.add(trap_ts)

    return signals

smc.phantom_signals = _phantom_signals
'''

with open('smartmoneyconcepts/smc.py', 'w') as f:
    f.writelines(clean_lines)
    f.write(new_code)

print("smc.py rewritten with all Gap 6, 7, 8 fixes.")
