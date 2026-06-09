import sys
sys.path.insert(0, '.')

with open('smartmoneyconcepts/smc.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

clean_lines = lines[:2094]

new_code = """
def _trendline_phantoms(ohlc, swings):
    \"\"\"
    Detects False Trendline (Phantom) Traps from Month 3 Video 7.

    Returns a DataFrame with columns:
    - trap_interim  : price of the high/low between touches 2 and 3
    - trap_point2   : price of the 2nd touch (retail stop cluster)
    - trap_touch3   : price of the 3rd touch (for limit-order entry, Gap 7)
    - trap_p1_ts    : timestamp of Point 1 (for FVG target lookup)
    - trap_fvg_top  : top of the FVG left by Point 1 impulse (Gap 8)
    - trap_fvg_bot  : bottom of the FVG left by Point 1 impulse (Gap 8)
    - trap_ts       : timestamp when trap became active (after 3rd touch)
    - trap_type     : 1 for Bullish Trap, -1 for Bearish Trap
    \"\"\"
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

    def _find_p1_fvg(p1_ts, direction):
        \"\"\"Return (fvg_top, fvg_bot) of the FVG at Point 1 impulse, or (nan, nan).\"\"\"
        try:
            idx = ohlc.index.get_loc(p1_ts)
        except KeyError:
            return np.nan, np.nan
        if idx + 1 >= len(ohlc):
            return np.nan, np.nan
        c0 = ohlc.iloc[idx]
        c1 = ohlc.iloc[idx + 1]
        if direction == 'bearish':
            if c1['high'] < c0['low']:
                return float(c0['low']), float(c1['high'])
        else:
            if c1['low'] > c0['high']:
                return float(c1['low']), float(c0['high'])
        return np.nan, np.nan

    # Bullish Traps: 3 consecutive Lower Highs
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
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bearish')
                    result.loc[t3, 'trap_interim'] = float(window['low'].min())
                    result.loc[t3, 'trap_point2']  = float(h2['p'])
                    result.loc[t3, 'trap_touch3']  = float(h3['p'])
                    result.loc[t3, 'trap_p1_ts']   = t1
                    result.loc[t3, 'trap_fvg_top'] = fvg_top
                    result.loc[t3, 'trap_fvg_bot'] = fvg_bot
                    result.loc[t3, 'trap_ts']      = t3
                    result.loc[t3, 'trap_type']    = 1

    # Bearish Traps: 3 consecutive Higher Lows
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
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bullish')
                    result.loc[t3, 'trap_interim'] = float(window['high'].max())
                    result.loc[t3, 'trap_point2']  = float(l2['p'])
                    result.loc[t3, 'trap_touch3']  = float(l3['p'])
                    result.loc[t3, 'trap_p1_ts']   = t1
                    result.loc[t3, 'trap_fvg_top'] = fvg_top
                    result.loc[t3, 'trap_fvg_bot'] = fvg_bot
                    result.loc[t3, 'trap_ts']      = t3
                    result.loc[t3, 'trap_type']    = -1

    for col in ['trap_interim','trap_point2','trap_touch3','trap_fvg_top','trap_fvg_bot']:
        result[col] = result[col].ffill()
    result['trap_ts']    = result['trap_ts'].ffill()
    result['trap_p1_ts'] = result['trap_p1_ts'].ffill()
    result['trap_type']  = result['trap_type'].replace(0, np.nan).ffill().fillna(0)

    return result

smc.trendline_phantoms = _trendline_phantoms


def _phantom_signals(ohlc, phantoms, ob_df, htf_bias=None):
    \"\"\"
    Full 3-Phase Market Maker Trap Execution Engine (Month 3, Video 7).

    Phase 2 Entry Triggers at the Interim Extreme:
      A. Turtle Soup       -- price sweeps below/above the interim level
      B. Limit at 3rd Touch -- price touches the 3rd-touch trendline level (Gap 7)
      C. OB Tap            -- price taps an Order Block at the interim level
      D. Breaker           -- price breaks a prior swing in the trap direction (Gap 6)

    Phase 2 Target        : trap_point2 (retail stop cluster)
    Secondary Target      : trap_fvg_top / trap_fvg_bot (FVG from Point 1, Gap 8)

    Phase 3 Reversal (after Point 2 is swept):
      Signal  : opposite direction
      Target  : trap_interim (deep liquidity pool)

    signal column  : 1=Buy, -1=Sell
    trigger_type   : identifies which phase and entry type fired
    target_price   : primary Take Profit
    secondary_target: FVG-based secondary Take Profit (Gap 8)
    \"\"\"
    import pandas as pd
    import numpy as np

    signals = pd.DataFrame(index=ohlc.index)
    signals['signal']           = 0
    signals['trigger_type']     = ""
    signals['target_price']     = np.nan
    signals['secondary_target'] = np.nan

    if htf_bias is None:
        htf_bias = pd.Series(1, index=ohlc.index)

    consumed_traps = set()
    phase2_fired   = set()

    # Pre-compute Breaker flags (Gap 6)
    # Bearish Breaker: close breaks above prior bar high (retail trapped long -- we sell)
    # Bullish Breaker: close breaks below prior bar low  (retail trapped short -- we buy)
    breaker_up   = ohlc['close'] > ohlc['high'].shift(1)
    breaker_down = ohlc['close'] < ohlc['low'].shift(1)

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

        trap_interim = phantoms['trap_interim'].iloc[i]
        trap_point2  = phantoms['trap_point2'].iloc[i]
        trap_touch3  = phantoms['trap_touch3'].iloc[i]
        trap_fvg_top = phantoms['trap_fvg_top'].iloc[i]
        trap_fvg_bot = phantoms['trap_fvg_bot'].iloc[i]

        ob_top    = ob_df['Top'].iloc[i]    if 'Top'    in ob_df.columns else np.nan
        ob_bottom = ob_df['Bottom'].iloc[i] if 'Bottom' in ob_df.columns else np.nan
        ob_type   = ob_df['OB'].iloc[i]     if 'OB'     in ob_df.columns else 0

        def _fvg_secondary(direction):
            if direction == 'bull':
                return float(trap_fvg_top) if not pd.isna(trap_fvg_top) else np.nan
            return float(trap_fvg_bot) if not pd.isna(trap_fvg_bot) else np.nan

        # ============================================================== #
        # BULLISH TRAP  (3 Lower Highs -- retail sells, we buy)          #
        # ============================================================== #
        if trap_type == 1:
            swept_point2  = high >= trap_point2
            swept_interim = low  <= trap_interim
            at_touch3     = high >= trap_touch3
            breaker_fired = bool(breaker_up.iloc[i]) and high >= trap_interim

            if trap_ts in phase2_fired and swept_point2:
                # Phase 3: buy-stops at Point 2 purged -- Market Maker SELLS
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 3 SELL -- Point2 High Swept"
                signals.loc[ts, 'target_price']      = trap_interim
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                consumed_traps.add(trap_ts)

            elif swept_interim and trap_ts not in phase2_fired:
                # Phase 2-A: Turtle Soup at Interim Low
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Turtle Soup"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif at_touch3 and trap_ts not in phase2_fired:
                # Phase 2-B: Limit Order at 3rd Touch (Gap 7)
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Limit at 3rd Touch"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif breaker_fired and trap_ts not in phase2_fired:
                # Phase 2-D: Bearish Breaker near Interim (Gap 6)
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Bearish Breaker"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif (ob_type == 1 and not pd.isna(ob_top)
                  and low <= ob_top
                  and not pd.isna(ob_bottom)
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                # Phase 2-C: OB Tap at Interim Low
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- OB Tap"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

        # ============================================================== #
        # BEARISH TRAP  (3 Higher Lows -- retail buys, we sell)          #
        # ============================================================== #
        elif trap_type == -1:
            swept_point2  = low  <= trap_point2
            swept_interim = high >= trap_interim
            at_touch3     = low  <= trap_touch3
            breaker_fired = bool(breaker_down.iloc[i]) and low <= trap_interim

            if trap_ts in phase2_fired and swept_point2:
                # Phase 3: sell-stops at Point 2 purged -- Market Maker BUYS
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 3 BUY -- Point2 Low Swept"
                signals.loc[ts, 'target_price']      = trap_interim
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                consumed_traps.add(trap_ts)

            elif swept_interim and trap_ts not in phase2_fired:
                # Phase 2-A: Turtle Soup at Interim High
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Turtle Soup"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif at_touch3 and trap_ts not in phase2_fired:
                # Phase 2-B: Limit Order at 3rd Touch (Gap 7)
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Limit at 3rd Touch"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif breaker_fired and trap_ts not in phase2_fired:
                # Phase 2-D: Bullish Breaker near Interim (Gap 6)
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Bullish Breaker"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif (ob_type == -1 and not pd.isna(ob_bottom)
                  and high >= ob_bottom
                  and not pd.isna(ob_top)
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                # Phase 2-C: OB Tap at Interim High
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- OB Tap"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

    return signals

smc.phantom_signals = _phantom_signals
"""

with open('smartmoneyconcepts/smc.py', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
    f.write(new_code)

print("smc.py rewritten with Gap 6, 7, 8 fixes applied.")
