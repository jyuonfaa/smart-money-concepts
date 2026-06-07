import pandas as pd
import numpy as np
from enum import Enum


class PriceDeliveryState(Enum):
    CONSOLIDATION = "consolidation"
    EXPANSION     = "expansion"
    RETRACEMENT   = "retracement"
    REVERSAL      = "reversal"
    UNKNOWN       = "unknown"


def detect_reversals(ohlc, swing_hl):
    """
    ICT Reversal / Stop Run Detector.
    
    ICT Month 1, Video 1:
      "Reversal is when price moves the opposite direction. The market makers
       have run a level of stops and a significant move should unfold.
       What to look for: the liquidity pools just above an old price high
       and just below an old price low."
    
    Logic:
      BEARISH REVERSAL — wick pierces above a prior swing high, body closes back below.
      BULLISH REVERSAL — wick pierces below a prior swing low, body closes back above.
      Order Block = the last opposing candle before the reversal candle.
    
    Returns DataFrame with columns:
      Reversal:    1.0 (bullish) / -1.0 (bearish) / NaN
      SweptLevel:  the swing high or low that was swept
      OB_Top:      top of the reversal order block
      OB_Bottom:   bottom of the reversal order block
    """
    n = len(ohlc)
    h = ohlc["high"].values
    l = ohlc["low"].values
    c = ohlc["close"].values
    o = ohlc["open"].values
    
    shl_hl = swing_hl["HighLow"].values
    shl_lv = swing_hl["Level"].values
    
    # Collect swing levels with their bar index
    swing_highs = []  # (index, level)
    swing_lows = []   # (index, level)
    for idx in range(n):
        if shl_hl[idx] == 1.0:
            swing_highs.append((idx, shl_lv[idx]))
        elif shl_hl[idx] == -1.0:
            swing_lows.append((idx, shl_lv[idx]))
    
    reversal = np.full(n, np.nan)
    swept_level = np.full(n, np.nan)
    ob_top = np.full(n, np.nan)
    ob_bottom = np.full(n, np.nan)
    
    # Track which swing levels are still "live" (not yet broken by a close).
    # A level is invalidated when any candle's CLOSE exceeds it,
    # making it a one-shot trigger — exactly like real stop orders.
    sh_valid = [True] * len(swing_highs)
    sl_valid = [True] * len(swing_lows)
    
    for i in range(1, n):
        best_signal = None
        
        # --- BEARISH REVERSAL: sweep above a swing high ---
        for k, (sh_idx, sh_level) in enumerate(swing_highs):
            if not sh_valid[k]:
                continue
            if sh_idx >= i:
                continue
            if i - sh_idx > 200:
                continue
            
            # Check if a prior candle already closed above this level
            if h[i] > sh_level and c[i] < sh_level:
                if best_signal is None or sh_idx > best_signal[0]:
                    best_signal = (sh_idx, sh_level, -1.0, k, 'sh')
            
            # If body closes above, invalidate (stops taken, no rejection)
            if c[i] > sh_level:
                sh_valid[k] = False
        
        # --- BULLISH REVERSAL: sweep below a swing low ---
        for k, (sl_idx, sl_level) in enumerate(swing_lows):
            if not sl_valid[k]:
                continue
            if sl_idx >= i:
                continue
            if i - sl_idx > 200:
                continue
            
            if l[i] < sl_level and c[i] > sl_level:
                if best_signal is None or sl_idx > best_signal[0]:
                    best_signal = (sl_idx, sl_level, 1.0, k, 'sl')
            
            if c[i] < sl_level:
                sl_valid[k] = False
        
        if best_signal is not None:
            _, level, direction, k_idx, kind = best_signal
            reversal[i] = direction
            swept_level[i] = level
            
            if kind == 'sh':
                sh_valid[k_idx] = False
            else:
                sl_valid[k_idx] = False
            
            if direction == -1.0:
                for j in range(i - 1, max(0, i - 30), -1):
                    if c[j] > o[j]:
                        ob_top[i] = h[j]
                        ob_bottom[i] = l[j]
                        break
            else:
                for j in range(i - 1, max(0, i - 30), -1):
                    if c[j] < o[j]:
                        ob_top[i] = h[j]
                        ob_bottom[i] = l[j]
                        break
    
    return pd.DataFrame({
        "Reversal": reversal,
        "SweptLevel": swept_level,
        "OB_Top": ob_top,
        "OB_Bottom": ob_bottom,
    }, index=ohlc.index)


def turtle_soup_signals(
    ohlc: pd.DataFrame,
    reversals: pd.DataFrame,
    daily_ob: pd.DataFrame,
    daily_ohlc: pd.DataFrame,
    liq_df: pd.DataFrame = None,
    use_daily_ob_stop: bool = False,
    refinement_level: str = None,
    liq_1h: pd.DataFrame = None,
    ny_midnight: pd.Series = None,
    lethargy_window: int = 5,
    lethargy_threshold_pips: float = 0.0010,
    ltf_session_obs: pd.DataFrame = None,
    entry_buffer_pips: float = 0.0005,
    require_down_candle_violation: bool = False,
    fvg_df: pd.DataFrame = None,
    max_session_ob_age_days: int = 3,
    monthly_ob_df: pd.DataFrame = None,
    smt_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    ICT Month 2, Video 1: Turtle Soup Confluence Flag.

    Turtle Soup = a bullish reversal (stop run below old low) that lands
    precisely inside a Daily Bullish Order Block.

    ICT verbatim (page 59):
      "Price trades down into that level and slams right into it.
       Now we are in turtle soup conditions (that means a break below an old low).
       We could potentially expect this market to run higher."

    Logic (no new detection — reuses existing reversal_bull signal):
      turtle_soup_bull = reversal == 1.0
                         AND current_price >= daily_ob_bottom
                         AND current_price <= daily_ob_top
                         (where daily OB is the most recent unmitigated bullish OB on the Daily chart)

      turtle_soup_bear = reversal == -1.0
                         AND current_price >= daily_ob_bottom
                         AND current_price <= daily_ob_top
                         (where daily OB is the most recent unmitigated bearish OB on the Daily chart)

    Parameters
    ----------
    ohlc              : pd.DataFrame  — the lower-timeframe (15M or 1H) OHLCV bar data
    reversals         : pd.DataFrame  — output of detect_reversals(), contains 'Reversal' column
    daily_ob          : pd.DataFrame  — output of smc.ob() run on Daily timeframe (RangeIndex)
    daily_ohlc        : pd.DataFrame  — the Daily OHLCV data (RangeIndex, matching daily_ob)
    liq_df            : pd.DataFrame  — optional output of smc.liquidity() on the same ohlc data.
    use_daily_ob_stop : bool          — when True, ts_ob_stop uses daily OB bottom instead of LTF midpoint
    refinement_level  : str           — label ('1H', '15M', '5M') mapped to the signal refinement tier
    entry_buffer_pips : float         — ICT Month 3 V3: 5 pips added above the OB bottom as the limit entry
    require_down_candle_violation : bool — ICT Month 3 V3: require a bearish candle at/below midnight
                                           open to be violated on the upside before firing bullish signal.

    Returns
    -------
    pd.DataFrame with columns:
      turtle_soup_bull : bool  — True where bullish Turtle Soup confluence fires
      turtle_soup_bear : bool  — True where bearish Turtle Soup confluence fires
      ts_ob_top        : float — Ceiling of ICT entry zone (wick high for bull, bar.open for bear)
      ts_ob_bottom     : float — Floor of ICT entry zone (bar.open for bull, wick low for bear)
      ts_entry_price   : float — Precision entry = ts_ob_bottom + entry_buffer_pips (bull) or ts_ob_top - buffer (bear)
      ts_ob_stop       : float — ICT stop
      ts_target_near   : float — Nearest buy/sell stop cluster above/below entry (from liq_df)
      ts_target_far    : float — Furthest buy/sell stop cluster above/below entry (from liq_df)
      down_candle_violated : bool — True if a bearish candle at/below midnight open was broken on upside
      ts_target_fvg        : float — Nearest unmitigated FVG above entry (bull) or below entry (bear)
      refinement_level : str   — The passed refinement level label
    """
    n = len(ohlc)
    bull_flags    = np.zeros(n, dtype=bool)
    bear_flags    = np.zeros(n, dtype=bool)
    ts_ob_tops    = np.full(n, np.nan)
    ts_ob_bots    = np.full(n, np.nan)
    ts_ob_stops   = np.full(n, np.nan)
    ts_tgt_near   = np.full(n, np.nan)
    ts_tgt_far    = np.full(n, np.nan)
    ts_tgt_1h     = np.full(n, np.nan)
    power3_sponsored = np.zeros(n, dtype=bool)
    is_lethargic  = np.zeros(n, dtype=bool)
    ts_entry_price = np.full(n, np.nan)
    down_candle_violated = np.zeros(n, dtype=bool)
    ts_tgt_fvg    = np.full(n, np.nan)
    monthly_ob_gated = np.ones(n, dtype=bool)  # Default True (pass); set False if outside Monthly OB zone

    # ── Monthly OB Gate: pre-resolve active zone from monthly_ob_df ──────
    # If a monthly_ob_df is provided, extract the active zone boundaries.
    # Only signals whose LTF close price falls INSIDE the active Monthly OB zone will fire.
    m_bull_active = False
    m_bear_active = False
    m_bull_ob_low  = np.nan   # Bullish OB floor — buy zone bottom
    m_bull_ob_high = np.nan   # Bullish OB ceiling — activation level
    m_bear_ob_low  = np.nan   # Bearish OB floor — activation level
    m_bear_ob_high = np.nan   # Bearish OB ceiling — sell zone top

    if monthly_ob_df is not None and len(monthly_ob_df) > 0:
        last_row = monthly_ob_df.iloc[-1]
        m_bull_active  = bool(last_row.get('monthly_bull_ob_active', False))
        m_bear_active  = bool(last_row.get('monthly_bear_ob_active', False))
        m_bull_ob_low  = float(last_row.get('monthly_down_ob_low',  np.nan))
        m_bull_ob_high = float(last_row.get('monthly_down_ob_high', np.nan))
        m_bear_ob_low  = float(last_row.get('monthly_up_ob_low',   np.nan))
        m_bear_ob_high = float(last_row.get('monthly_up_ob_high',  np.nan))

    # Pre-extract OHLC arrays for fast vectorized access
    h_prices = ohlc['high'].values
    l_prices = ohlc['low'].values
    o_prices = ohlc['open'].values

    # Build a list of active (unmitigated) OB rows indexed to their bar index
    bull_obs = []  # list of (ob_row, bar_row) for bullish OBs
    bear_obs = []  # list of (ob_row, bar_row) for bearish OBs

    for i in range(len(daily_ob)):
        ob_row  = daily_ob.iloc[i]
        bar_row = daily_ohlc.iloc[i]
        if pd.isna(ob_row['OB']):
            continue
        is_mitigated = (not pd.isna(ob_row['MitigatedIndex']) and ob_row['MitigatedIndex'] > 0)
        if ob_row['OB'] == 1.0 and not is_mitigated:
            bull_obs.append((ob_row, bar_row))
        elif ob_row['OB'] == -1.0 and not is_mitigated:
            bear_obs.append((ob_row, bar_row))

    rev_vals = reversals['Reversal'].values
    c_prices = ohlc['close'].values
    # Re-use the pre-extracted arrays (h_prices, l_prices, o_prices already set above)

    # Midnight open series as numpy for fast per-bar access
    midnight_vals = ny_midnight.values if ny_midnight is not None else None

    for i in range(n):
        rev = rev_vals[i]
        c   = c_prices[i]

        # ── SMT Trend Confirmation Gate (ICT Page 217-218) ────────────────────
        # "The idea of stalking reversal patterns in this condition is not highly
        # probable — you want to avoid it altogether."
        # When the macro trend is symmetrically confirmed, suppress contra-trend reversals.
        smt_confirmed_bull = False
        smt_confirmed_bear = False
        if smt_df is not None:
            current_date = str(ohlc.index[i].date())[:10]
            try:
                smt_row = smt_df.loc[:current_date].iloc[-1]
                if bool(smt_row.get('smt_trend_confirmed', False)):
                    direction = smt_row.get('smt_trend_direction', 'NEUTRAL')
                    smt_confirmed_bull = (direction == 'BULLISH')
                    smt_confirmed_bear = (direction == 'BEARISH')
            except (KeyError, IndexError):
                pass

        if rev == 1.0 and bull_obs:
            # ── Monthly OB Gate (Bullish): price must be inside the active Bullish Monthly OB zone ──
            if monthly_ob_df is not None and m_bull_active:
                if not (m_bull_ob_low <= c <= m_bull_ob_high):
                    monthly_ob_gated[i] = False
                    continue
            elif monthly_ob_df is not None and not m_bull_active:
                monthly_ob_gated[i] = False
                continue

            # SMT Gate: suppress bullish reversals when trend is confirmed bearish (ICT Page 217)
            if smt_confirmed_bear:
                continue

            for ob_row, bar_row in bull_obs:
                ob_top        = float(ob_row['Top'])     # wick high = ceiling of green zone
                entry_zone_btm = float(bar_row['open'])  # open of down candle = floor of green zone
                if entry_zone_btm <= c <= ob_top:
                    # Session OB precision check — also enforces recency (max_session_ob_age_days)
                    if ltf_session_obs is not None:
                        past_obs = ltf_session_obs.iloc[:i]
                        # Apply recency window: only OBs formed within max_session_ob_age_days trading days
                        if max_session_ob_age_days is not None and hasattr(ohlc.index, 'date'):
                            cutoff_ts = ohlc.index[i] - pd.Timedelta(days=max_session_ob_age_days)
                            past_obs = past_obs[past_obs.index >= cutoff_ts.value if hasattr(cutoff_ts, 'value') else past_obs.index >= cutoff_ts]
                        # 1.0 is bullish OB
                        active_obs = past_obs[(past_obs['OB'] == 1.0) & (past_obs['MitigatedIndex'].isna() | (past_obs['MitigatedIndex'] > i))]
                        if len(active_obs) > 0:
                            last_ob = active_obs.iloc[-1]
                            if not (float(last_ob['Bottom']) <= c <= float(last_ob['Top'])):
                                continue # Price didn't tap the session OB, skip
                        else:
                            continue # No active session OB within recency window, skip

                    bull_flags[i]  = True
                    ts_ob_tops[i]  = ob_top
                    ts_ob_bots[i]  = float(ohlc.iloc[i]['open'])  # LTF candle open, not daily OB candle open

                    # ICT Month 3 V3: 5-pip buffer — precision entry sits above the OB floor
                    ts_entry_price[i] = float(ohlc.iloc[i]['open']) + entry_buffer_pips

                    # ICT Month 3 V3: Down-candle violation flag
                    # Look back up to 10 bars for a bearish candle at/below midnight open
                    # that has since had its high taken out (violated on the upside)
                    if midnight_vals is not None and not pd.isna(midnight_vals[i]):
                        midnight_lvl = float(midnight_vals[i])
                        lookback = max(0, i - 10)
                        for j in range(i - 1, lookback - 1, -1):
                            # Bearish candle at or below midnight open
                            if c_prices[j] < o_prices[j] and l_prices[j] <= midnight_lvl:
                                # Was that candle's high subsequently taken out (violated)?
                                if h_prices[i] > o_prices[j]:
                                    down_candle_violated[i] = True
                                break  # only check the most recent qualifying down candle
                    if use_daily_ob_stop:
                        ts_ob_stops[i] = float(ob_row['Bottom'])  # floor of daily OB — below bullish entry
                    else:
                        ts_ob_stops[i] = (float(bar_row['open']) + float(bar_row['close'])) / 2.0
                    
                    if liq_df is not None:
                        past = liq_df.iloc[:i]
                        cands = past[
                            (past['Liquidity'] == 1.0) &
                            (past['IsTooClean'] == 1) &
                            (past['Level'] > entry_zone_btm)
                        ]['Level']
                        if len(cands) > 0:
                            ts_tgt_near[i] = float(cands.min())
                            ts_tgt_far[i]  = float(cands.max())
                            
                    if liq_1h is not None:
                        past_1h = liq_1h[liq_1h.index <= ohlc.index[i]]
                        ref_level = ts_tgt_far[i] if not np.isnan(ts_tgt_far[i]) else entry_zone_btm
                        cands_1h = past_1h[
                            (past_1h['Liquidity'] == 1.0) &
                            (past_1h['IsTooClean'] == 1) &
                            (past_1h['Level'] > ref_level)
                        ]['Level']
                        if len(cands_1h) > 0:
                            ts_tgt_1h[i] = float(cands_1h.min())

                    # FVG Target Tier (Bullish): nearest unmitigated bullish FVG above entry
                    # Scans the full FVG dataset — an unmitigated void above price is a price magnet
                    # regardless of whether it formed before or after this bar.
                    if fvg_df is not None:
                        bull_fvgs = fvg_df[
                            (fvg_df['FVG'] == 1.0) &
                            (fvg_df['MitigatedIndex'] > i) &
                            (fvg_df['Bottom'] > c)
                        ]
                        if len(bull_fvgs) > 0:
                            # Nearest = smallest Bottom above entry
                            ts_tgt_fvg[i] = float(bull_fvgs['Bottom'].min())
                            
                    if ny_midnight is not None and not pd.isna(ny_midnight.iloc[i]):
                        if c < float(ny_midnight.iloc[i]):
                            power3_sponsored[i] = True
                            
                    # Lethargy Check (Bullish)
                    end_idx = min(n, i + 1 + lethargy_window)
                    if end_idx > i + 1:
                        max_close = np.max(c_prices[i+1:end_idx])
                        if max_close < (c + lethargy_threshold_pips):
                            is_lethargic[i] = True
                    else:
                        # Not enough data forward, assume lethargic
                        is_lethargic[i] = True
                            
                    break

        elif rev == -1.0 and bear_obs:
            # ── Monthly OB Gate (Bearish): price must be inside the active Bearish Monthly OB zone ──
            if monthly_ob_df is not None and m_bear_active:
                if not (m_bear_ob_low <= c <= m_bear_ob_high):
                    monthly_ob_gated[i] = False
                    continue
            elif monthly_ob_df is not None and not m_bear_active:
                monthly_ob_gated[i] = False
                continue

            # SMT Gate: suppress bearish reversals when trend is confirmed bullish (ICT Page 217)
            if smt_confirmed_bull:
                continue

            for ob_row, bar_row in bear_obs:
                ob_bot        = float(ob_row['Bottom'])  # wick low = floor of red zone
                entry_zone_top = float(bar_row['open'])  # open of up candle = ceiling of red zone
                if ob_bot <= c <= entry_zone_top:
                    # Session OB precision check — also enforces recency (max_session_ob_age_days)
                    if ltf_session_obs is not None:
                        past_obs = ltf_session_obs.iloc[:i]
                        # Apply recency window
                        if max_session_ob_age_days is not None and hasattr(ohlc.index, 'date'):
                            cutoff_ts = ohlc.index[i] - pd.Timedelta(days=max_session_ob_age_days)
                            past_obs = past_obs[past_obs.index >= cutoff_ts.value if hasattr(cutoff_ts, 'value') else past_obs.index >= cutoff_ts]
                        # -1.0 is bearish OB
                        active_obs = past_obs[(past_obs['OB'] == -1.0) & (past_obs['MitigatedIndex'].isna() | (past_obs['MitigatedIndex'] > i))]
                        if len(active_obs) > 0:
                            last_ob = active_obs.iloc[-1]
                            if not (float(last_ob['Bottom']) <= c <= float(last_ob['Top'])):
                                continue
                        else:
                            continue

                    bear_flags[i]  = True
                    ts_ob_tops[i]  = float(ohlc.iloc[i]['open'])  # LTF candle open, not daily OB candle open
                    ts_ob_bots[i]  = ob_bot

                    # ICT Month 3 V3: 5-pip buffer — precision entry sits below the OB ceiling
                    ts_entry_price[i] = float(ohlc.iloc[i]['open']) - entry_buffer_pips

                    # ICT Month 3 V3: Down-candle violation flag (Bearish: bullish candle at/above midnight violated)
                    if midnight_vals is not None and not pd.isna(midnight_vals[i]):
                        midnight_lvl = float(midnight_vals[i])
                        lookback = max(0, i - 10)
                        for j in range(i - 1, lookback - 1, -1):
                            # Bullish candle at or above midnight open
                            if c_prices[j] > o_prices[j] and h_prices[j] >= midnight_lvl:
                                # Was that candle's low subsequently violated on the downside?
                                if l_prices[i] < o_prices[j]:
                                    down_candle_violated[i] = True
                                break
                    if use_daily_ob_stop:
                        ts_ob_stops[i] = float(ob_row['Top'])     # ceiling of daily OB — above bearish entry
                    else:
                        ts_ob_stops[i] = (float(bar_row['open']) + float(bar_row['close'])) / 2.0
                    
                    if liq_df is not None:
                        past = liq_df.iloc[:i]
                        cands = past[
                            (past['Liquidity'] == -1.0) &
                            (past['IsTooClean'] == 1) &
                            (past['Level'] < ts_ob_tops[i])
                        ]['Level']
                        if len(cands) > 0:
                            ts_tgt_near[i] = float(cands.max())
                            ts_tgt_far[i]  = float(cands.min())
                            
                    if liq_1h is not None:
                        past_1h = liq_1h[liq_1h.index <= ohlc.index[i]]
                        ref_level = ts_tgt_far[i] if not np.isnan(ts_tgt_far[i]) else ts_ob_tops[i]
                        cands_1h = past_1h[
                            (past_1h['Liquidity'] == -1.0) &
                            (past_1h['IsTooClean'] == 1) &
                            (past_1h['Level'] < ref_level)
                        ]['Level']
                        if len(cands_1h) > 0:
                            ts_tgt_1h[i] = float(cands_1h.max())

                    # FVG Target Tier (Bearish): nearest unmitigated bearish FVG below entry
                    # Scans the full FVG dataset — an unmitigated void below price is a price magnet.
                    if fvg_df is not None:
                        bear_fvgs = fvg_df[
                            (fvg_df['FVG'] == -1.0) &
                            (fvg_df['MitigatedIndex'] > i) &
                            (fvg_df['Top'] < c)
                        ]
                        if len(bear_fvgs) > 0:
                            # Nearest = largest Top below entry
                            ts_tgt_fvg[i] = float(bear_fvgs['Top'].max())
                            
                    if ny_midnight is not None and not pd.isna(ny_midnight.iloc[i]):
                        if c > float(ny_midnight.iloc[i]):
                            power3_sponsored[i] = True
                            
                    # Lethargy Check (Bearish)
                    end_idx = min(n, i + 1 + lethargy_window)
                    if end_idx > i + 1:
                        min_close = np.min(c_prices[i+1:end_idx])
                        if min_close > (c - lethargy_threshold_pips):
                            is_lethargic[i] = True
                    else:
                        is_lethargic[i] = True
                            
                    break

    return pd.DataFrame({
        'turtle_soup_bull':     bull_flags,
        'turtle_soup_bear':     bear_flags,
        'ts_ob_top':            ts_ob_tops,
        'ts_ob_bottom':         ts_ob_bots,
        'ts_entry_price':       ts_entry_price,
        'ts_ob_stop':           ts_ob_stops,
        'ts_target_near':       ts_tgt_near,
        'ts_target_far':        ts_tgt_far,
        'ts_target_1h':         ts_tgt_1h,
        'ts_target_fvg':        ts_tgt_fvg,
        'power3_sponsored':     power3_sponsored,
        'is_lethargic':         is_lethargic,
        'down_candle_violated': down_candle_violated,
        'monthly_ob_gated':     monthly_ob_gated,
        'refinement_level':     [refinement_level] * n,
    }, index=ohlc.index)


def false_flag_signals(
    ohlc_daily: pd.DataFrame,
    ohlc_ltf: pd.DataFrame,
    ohlc_4h: pd.DataFrame,
    daily_consolidation: pd.DataFrame,
    daily_retracements: pd.DataFrame,
    daily_turtle_soup: pd.DataFrame,
    ob_4h: pd.DataFrame,
    disp_4h: pd.DataFrame,
    daily_measured_moves: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    ICT Month 2, Video 7: False Flag / Market Maker Trap.

    A false flag occurs when retail traders perceive a short-term continuation pattern (consolidation)
    but the higher timeframe narrative (Daily Equilibrium) dictates a reversal. The trap is triggered
    by a Turtle Soup sweep of the flag's extreme.

    This rebuilt version uses the Daily chart as the detection layer (Page 117), confirms the
    flagpole with a 4H displacement candle, then uses the 4H OB as the precision entry zone.
    The LTF (15M) finds the first candle that returns to the 4H OB zone and closes
    inside/beyond the swept flag level.
    """
    n_ltf = len(ohlc_ltf)
    false_bull_flag = np.zeros(n_ltf, dtype=bool)
    false_bear_flag = np.zeros(n_ltf, dtype=bool)
    trap_entry      = np.full(n_ltf, np.nan)
    trap_stop_loss  = np.full(n_ltf, np.nan)
    trap_cons_top_arr = np.full(n_ltf, np.nan)
    trap_cons_bot_arr = np.full(n_ltf, np.nan)
    ts_target_measured = np.full(n_ltf, np.nan)

    # --- 1. Identify Daily Episodes ---
    daily_episodes = []
    n_daily = len(ohlc_daily)

    d_dir = daily_retracements['Direction'].values
    ret_pct = daily_retracements['CurrentRetracement%'].values
    is_bullish = d_dir == 1
    is_bearish = d_dir == -1

    # Premium: upper half of the swing range (50–90% retracement).
    # Cap at 90%: above 90% means price has essentially negated the swing entirely
    # (no longer a distribution zone — price is at or above the prior swing high).
    # Discount: lower half of the swing range, same 90% cap on the other side.
    daily_premium = (is_bullish & (ret_pct < 50)) | (is_bearish & (ret_pct > 50) & (ret_pct <= 90))
    daily_discount = (is_bullish & (ret_pct > 50) & (ret_pct <= 90)) | (is_bearish & (ret_pct < 50))

    is_cons = daily_consolidation['Consolidation'].notna() & (daily_consolidation['Consolidation'] != 0)
    is_cons = is_cons.values
    cons_top_vals = daily_consolidation['Top'].values
    cons_bot_vals = daily_consolidation['Bottom'].values

    ts_bear = daily_turtle_soup['turtle_soup_bear'].values
    ts_bull = daily_turtle_soup['turtle_soup_bull'].values

    disp_4h_times = ohlc_4h.index.values
    disp_4h_vals  = disp_4h['Displacement'].values

    last_fired_zone = None  # (ctop, cbot) tuple — block re-entries on identical flag zones
    last_fired_extreme = None

    CONS_LOOKBACK = 5  # daily bars: Ensure consolidation is fresh (a true Flag)
    POLE_LOOKBACK = 5  # daily bars: Window to find the flagpole before the consolidation

    # Precompute daily body sizes for flagpole strength check
    daily_opens  = ohlc_daily['open'].values
    daily_closes = ohlc_daily['close'].values
    daily_bodies = np.abs(daily_closes - daily_opens)
    avg_daily_body = np.mean(daily_bodies)  # baseline: average daily candle body size
    POLE_BODY_MULTIPLIER = 1.5  # flagpole must be at least 1.5x the average daily body

    for i in range(n_daily):
        # Find most recent consolidation zone within lookback window
        # Also record the FIRST bar of that consolidation zone (cons_start_j)
        ctop, cbot = np.nan, np.nan
        window_start = max(0, i - CONS_LOOKBACK)
        cons_start_j = window_start  # default: start of window
        for j in range(i, window_start - 1, -1):
            if is_cons[j] and not np.isnan(cons_top_vals[j]):
                ctop = cons_top_vals[j]
                cbot = cons_bot_vals[j]
                cons_start_j = j
                break
        if np.isnan(ctop):
            continue

        # FLAGPOLE CHECK (Daily timeframe, per the ICT notes):
        # The pole is a strong directional daily candle that preceded the consolidation.
        # We look at the 10 daily bars before the consolidation zone was FIRST detected
        # (cons_start_j). If the consolidation was first detected on the same sweep day
        # (cons_start_j == i, which happens when the SMC library confirms the zone late),
        # we fall back to looking at the 10 bars before bar i itself.
        pole_search_anchor = cons_start_j if cons_start_j < i else i
        pole_window_start  = max(0, pole_search_anchor - 10)
        pole_window_end    = pole_search_anchor
        pole_bodies  = daily_bodies[pole_window_start:pole_window_end]
        pole_opens   = daily_opens[pole_window_start:pole_window_end]
        pole_closes  = daily_closes[pole_window_start:pole_window_end]
        # At least ONE candle in the window must be a strong directional impulse
        has_bull_pole = bool(np.any(
            (pole_closes > pole_opens) &
            (pole_bodies >= avg_daily_body * POLE_BODY_MULTIPLIER)
        ))
        has_bear_pole = bool(np.any(
            (pole_closes < pole_opens) &
            (pole_bodies >= avg_daily_body * POLE_BODY_MULTIPLIER)
        ))

        # Price sanity check: the sweep must actually reach the flag extreme.
        # For a False Bull Flag (short): daily high must reach the flag TOP (cons_top).
        # For a False Bear Flag (long): daily low must reach the flag BOTTOM (cons_bot).
        # We check BOTH here and skip only if neither condition could possibly apply.
        daily_high_i = ohlc_daily['high'].values[i]
        daily_low_i  = ohlc_daily['low'].values[i]
        can_be_bull_trap = daily_high_i >= ctop * 0.998  # swept the top
        can_be_bear_trap = daily_low_i  <= cbot * 1.002  # swept the bottom
        if not can_be_bull_trap and not can_be_bear_trap:
            continue

        daily_close_i = ohlc_daily['close'].values[i]
        daily_low_i   = ohlc_daily['low'].values[i]

        # Guard: if HTF premium/discount data is missing, skip this bar
        if np.isnan(daily_premium[i]) or np.isnan(daily_discount[i]):
            continue

        # Cooldown: generally don't re-enter the same zone, UNLESS the new sweep
        # is significantly deeper (hunting the stops of the premature entry).
        this_zone = (round(ctop, 4), round(cbot, 4))
        
        # PATH 1 — Turtle Soup sweep (formal swing high/low violated)
        # FALSE BULL FLAG EPISODE (Short Trap)
        if ts_bear[i] and daily_premium[i] and has_bull_pole:
            if last_fired_zone != this_zone or daily_high_i > last_fired_extreme:
                daily_episodes.append({
                    'date': ohlc_daily.index[i],
                    'type': 'bear',
                    'cons_top': ctop,
                    'cons_bot': cbot,
                    'sweep_extreme': daily_high_i,
                    'target_measured': daily_high_i - daily_measured_moves['BearAmplitude'].values[i] if daily_measured_moves is not None else np.nan
                })
                last_fired_zone = this_zone
                last_fired_extreme = daily_high_i

        # FALSE BEAR FLAG EPISODE (Long Trap)
        elif ts_bull[i] and daily_discount[i] and has_bear_pole:
            if last_fired_zone != this_zone or ohlc_daily['low'].values[i] < last_fired_extreme:
                daily_episodes.append({
                    'date': ohlc_daily.index[i],
                    'type': 'bull',
                    'cons_top': ctop,
                    'cons_bot': cbot,
                    'sweep_extreme': ohlc_daily['low'].values[i],
                    'target_measured': ohlc_daily['low'].values[i] + daily_measured_moves['BullAmplitude'].values[i] if daily_measured_moves is not None else np.nan
                })
                last_fired_zone = this_zone
                last_fired_extreme = ohlc_daily['low'].values[i]

        # PATH 2 — Consolidation Breakout Failure (wick outside, closes back inside)
        # FALSE BULL FLAG (Short Trap)
        elif can_be_bull_trap and (daily_close_i < ctop) and daily_premium[i] and has_bull_pole:
            if last_fired_zone != this_zone or daily_high_i > last_fired_extreme:
                daily_episodes.append({
                    'date': ohlc_daily.index[i],
                    'type': 'bear',
                    'cons_top': ctop,
                    'cons_bot': cbot,
                    'sweep_extreme': daily_high_i,
                    'target_measured': daily_high_i - daily_measured_moves['BearAmplitude'].values[i] if daily_measured_moves is not None else np.nan
                })
                last_fired_zone = this_zone
                last_fired_extreme = daily_high_i

        # FALSE BEAR FLAG (Long Trap)
        elif can_be_bear_trap and (daily_close_i > cbot) and daily_discount[i] and has_bear_pole:
            if last_fired_zone != this_zone or daily_low_i < last_fired_extreme:
                daily_episodes.append({
                    'date': ohlc_daily.index[i],
                    'type': 'bull',
                    'cons_top': ctop,
                    'cons_bot': cbot,
                    'sweep_extreme': daily_low_i,
                    'target_measured': daily_low_i + daily_measured_moves['BullAmplitude'].values[i] if daily_measured_moves is not None else np.nan
                })
                last_fired_zone = this_zone
                last_fired_extreme = daily_low_i

    # --- 2. Map Episodes to LTF for Entry ---
    ltf_highs = ohlc_ltf['high'].values
    ltf_lows = ohlc_ltf['low'].values
    ltf_closes = ohlc_ltf['close'].values
    ltf_opens = ohlc_ltf['open'].values
    ltf_times = ohlc_ltf.index.values

    for ep in daily_episodes:
        ep_date = ep['date']
        # Find entry within 2 days of the episode
        ep_start_idx = np.searchsorted(ltf_times, np.datetime64(ep_date))
        end_idx = np.searchsorted(ltf_times, np.datetime64(ep_date + pd.Timedelta(days=2)))
        end_idx = min(end_idx, n_ltf)
        
        # Chronological Lock: Find the exact 15M candle that formed the sweep extreme
        ep_end_idx = np.searchsorted(ltf_times, np.datetime64(ep_date + pd.Timedelta(days=1)))
        ep_end_idx = min(ep_end_idx, n_ltf)
        
        sweep_idx = ep_start_idx
        found_sweep = False
        for k in range(ep_start_idx, ep_end_idx):
            if ep['type'] == 'bear':
                if ltf_highs[k] >= ep['sweep_extreme'] * 0.9999:
                    sweep_idx = k
                    found_sweep = True
                    break
            else:
                if ltf_lows[k] <= ep['sweep_extreme'] * 1.0001:
                    sweep_idx = k
                    found_sweep = True
                    break
                    
        start_idx = sweep_idx if found_sweep else ep_start_idx
        end_idx = min(end_idx, n_ltf)
        
        if end_idx - start_idx < 10:
            continue
            
        ctop = ep['cons_top']
        cbot = ep['cons_bot']
        sweep_extreme = ep['sweep_extreme']
        
        if ep['type'] == 'bear':
            # FALSE BULL FLAG (Short Trap) -> Breakdown -> Bearish OB -> Short
            ob_bot, ob_top = np.nan, np.nan
            entry_idx = -1
            
            for i in range(start_idx + 2, end_idx - 2):
                # Find local swing low
                if ltf_lows[i] < ltf_lows[i-1] and ltf_lows[i] < ltf_lows[i-2] and ltf_lows[i] < ltf_lows[i+1] and ltf_lows[i] < ltf_lows[i+2]:
                    swing_low = ltf_lows[i]
                    # Find breakdown
                    for j in range(i + 3, end_idx):
                        if ltf_closes[j] < swing_low:
                            # Breakdown! Find last up-candle (Bearish OB)
                            ob_cand_idx = -1
                            for k in range(j-1, i, -1):
                                if ltf_closes[k] > ltf_opens[k]:
                                    ob_cand_idx = k
                                    break
                            if ob_cand_idx != -1:
                                ob_top = max(ltf_opens[ob_cand_idx], ltf_closes[ob_cand_idx])
                                ob_bot = min(ltf_opens[ob_cand_idx], ltf_closes[ob_cand_idx])
                                
                                # Find first return to OB
                                for m in range(j + 1, end_idx):
                                    if ltf_highs[m] >= ob_bot:
                                        entry_idx = m
                                        break
                            break
                    if entry_idx != -1:
                        break
            
            if entry_idx != -1:
                false_bull_flag[entry_idx] = True
                trap_entry[entry_idx] = ltf_opens[entry_idx]
                trap_stop_loss[entry_idx] = sweep_extreme
                trap_cons_top_arr[entry_idx] = ctop
                trap_cons_bot_arr[entry_idx] = cbot
                ts_target_measured[entry_idx] = ep['target_measured']

        elif ep['type'] == 'bull':
            # FALSE BEAR FLAG (Long Trap) -> Breakout -> Bullish OB -> Long
            ob_bot, ob_top = np.nan, np.nan
            entry_idx = -1
            
            for i in range(start_idx + 2, end_idx - 2):
                # Find local swing high
                if ltf_highs[i] > ltf_highs[i-1] and ltf_highs[i] > ltf_highs[i-2] and ltf_highs[i] > ltf_highs[i+1] and ltf_highs[i] > ltf_highs[i+2]:
                    swing_high = ltf_highs[i]
                    # Find breakout
                    for j in range(i + 3, end_idx):
                        if ltf_closes[j] > swing_high:
                            # Breakout! Find last down-candle (Bullish OB)
                            ob_cand_idx = -1
                            for k in range(j-1, i, -1):
                                if ltf_closes[k] < ltf_opens[k]:
                                    ob_cand_idx = k
                                    break
                            if ob_cand_idx != -1:
                                ob_top = max(ltf_opens[ob_cand_idx], ltf_closes[ob_cand_idx])
                                ob_bot = min(ltf_opens[ob_cand_idx], ltf_closes[ob_cand_idx])
                                
                                # Find first return to OB
                                for m in range(j + 1, end_idx):
                                    if ltf_lows[m] <= ob_top:
                                        entry_idx = m
                                        break
                            break
                    if entry_idx != -1:
                        break
            
            if entry_idx != -1:
                false_bear_flag[entry_idx] = True
                trap_entry[entry_idx] = ltf_opens[entry_idx]
                trap_stop_loss[entry_idx] = sweep_extreme
                trap_cons_top_arr[entry_idx] = ctop
                trap_cons_bot_arr[entry_idx] = cbot
                ts_target_measured[entry_idx] = ep['target_measured']

    return pd.DataFrame({
        'false_bull_flag': false_bull_flag,
        'false_bear_flag': false_bear_flag,
        'trap_entry': trap_entry,
        'trap_stop_loss': trap_stop_loss,
        'trap_target_measured': ts_target_measured,
        'trap_cons_top': trap_cons_top_arr,
        'trap_cons_bottom': trap_cons_bot_arr,
    }, index=ohlc_ltf.index)


def calculate_path_obstruction(current_price: float, target_price: float, swing_hl: pd.DataFrame) -> int:
    """
    ICT Video 7: Price-Space Obstruction Counter.
    Counts structural pivots located geometrically between current_price and target_price.
    """
    if swing_hl.empty: return 0
    
    # Normalize swings
    if "type" in swing_hl.columns:
        swing_hl = swing_hl.copy()
        swing_hl["HighLow"] = swing_hl["type"].map({"HIGH": 1, "LOW": -1})
        swing_hl["Level"] = swing_hl["p"]
        
    valid_swings = swing_hl[swing_hl["HighLow"].notna()]
    levels = valid_swings["Level"].values
    types = valid_swings["HighLow"].values
    
    count = 0
    is_long = target_price > current_price
    
    for j in range(len(levels)):
        lv = levels[j]
        t = types[j]
        
        if is_long:
            # We only care about swing HIGHS in a bullish run (resistance)
            if t == 1 and current_price < lv < target_price:
                count += 1
        else:
            # We only care about swing LOWS in a bearish run (resistance)
            if t == -1 and target_price < lv < current_price:
                count += 1
                
    return count


class PriceDeliveryStateMachine:
    """
    ICT Price Delivery State Machine (Layer 5).
    
    Tracks: Consolidation -> Expansion -> Retracement -> Reversal
    
    States PERSIST — once assigned, a state holds until a valid transition fires.
    UNKNOWN only exists before the very first consolidation is detected.
    """
    
    def process(
        self,
        ohlc: pd.DataFrame,
        consolidation: pd.DataFrame,
        expansion: pd.DataFrame,
        displacement: pd.DataFrame = None,
        liquidity: pd.DataFrame = None,
        reversals: pd.DataFrame = None,
        htf_context: dict = None,
        swing_hl: pd.DataFrame = None,
    ) -> pd.DataFrame:
        """
        Video 3 Institutional Logging Engine.
        Transitioned from a predictive state machine to a passive logging system.
        Logs interactions with Speed (Displacement) and Clean Liquidity (Magnets).
        """
        n = len(ohlc)
        
        # Output columns for Logging
        states = []
        sovereign_envs = []
        killzones = []
        days_of_week = []
        targets = []
        speed_interactions = np.full(n, np.nan)
        clean_sweeps = np.full(n, np.nan)
        weekly_h_day = [None] * n
        weekly_l_day = [None] * n
        bars_since_fvg = 999 # Initialize to a large value
        active_bias = 0
        consec_lrr = 0
        consec_hrr = 0
        
        # Internal tracking
        current_state = PriceDeliveryState.UNKNOWN
        current_env = "HRR"
        
        # Localize to New York Time for logging
        try:
            if ohlc.index.tz is None:
                ohlc_ny = ohlc.index.tz_localize("UTC").tz_convert("America/New_York")
            else:
                ohlc_ny = ohlc.index.tz_convert("America/New_York")
        except:
            ohlc_ny = ohlc.index

        days = ohlc_ny.day_name()
        
        # Killzone Logic (STRICT INSTITUTIONAL TIMINGS)
        def get_killzone(timestamp):
            hour = timestamp.hour + timestamp.minute / 60
            if 19 <= hour:          return "Asian"         # 7:00 PM - 12:00 AM
            elif 2 <= hour < 5:     return "London Open"   # 2:00 AM - 5:00 AM
            elif 7 <= hour < 9:     return "NY Open"       # 7:00 AM - 9:00 AM
            elif 10 <= hour < 11:   return "London Close"  # 10:00 AM - 11:00 AM
            else:                   return "Other"

        # Target state persistence
        current_target = None
        target_bias = 0
        
        for i in range(n):
            current_time = ohlc_ny[i]
            kz = get_killzone(current_time)
            killzones.append(kz)
            days_of_week.append(days[i])
            
            row_cons = consolidation.iloc[i]
            row_exp  = expansion.iloc[i]
            is_consolidating = not pd.isna(row_cons["Consolidation"]) and row_cons["Consolidation"] != 0
            has_expansion    = not pd.isna(row_exp["Expansion"]) and row_exp["Expansion"] != 0
            
            # ── Step 1: Update Basic State (Observation Only) ──────────
            if is_consolidating:
                current_state = PriceDeliveryState.CONSOLIDATION
            elif has_expansion:
                current_state = PriceDeliveryState.EXPANSION
                active_bias = row_exp["Expansion"] # 1 for Bullish, -1 for Bearish
            
            # --- VIDEO 7 REBUILD: LRR/HRR CLASSIFICATION ---
            c_price = ohlc['close'].iloc[i]
            
            # Rule 1: Target selection - locked, only updates on mitigation or bias change
            if swing_hl is not None and active_bias != 0:
                if current_target is None or target_bias != active_bias:
                    historical_swings = swing_hl[swing_hl['ts'] < ohlc.index[i]]
                    if active_bias == 1:
                        # Bullish: nearest swing HIGH above price
                        highs = historical_swings[(historical_swings['HighLow'] == 1) & (historical_swings['Level'] > c_price)]
                        if not highs.empty:
                            current_target = highs.iloc[-1]['Level']
                            target_bias = 1
                        else:
                            current_target = None
                    elif active_bias == -1:
                        # Bearish: nearest swing LOW below price
                        lows = historical_swings[(historical_swings['HighLow'] == -1) & (historical_swings['Level'] < c_price)]
                        if not lows.empty:
                            current_target = lows.iloc[-1]['Level']
                            target_bias = -1
                        else:
                            current_target = None
                else:
                    # Target is locked. Check for mitigation.
                    if target_bias == 1 and c_price >= current_target:
                        historical_swings = swing_hl[swing_hl['ts'] < ohlc.index[i]]
                        highs = historical_swings[(historical_swings['HighLow'] == 1) & (historical_swings['Level'] > c_price)]
                        if not highs.empty:
                            current_target = highs.iloc[-1]['Level']
                        else:
                            current_target = None
                    elif target_bias == -1 and c_price <= current_target:
                        historical_swings = swing_hl[swing_hl['ts'] < ohlc.index[i]]
                        lows = historical_swings[(historical_swings['HighLow'] == -1) & (historical_swings['Level'] < c_price)]
                        if not lows.empty:
                            current_target = lows.iloc[-1]['Level']
                        else:
                            current_target = None

            # Rule 2: Obstruction count - ALL swings between price and locked target
            path_is_clear = False
            if current_target is not None and swing_hl is not None:
                historical_swings_subset = swing_hl[swing_hl['ts'] < ohlc.index[i]]
                count = calculate_path_obstruction(c_price, current_target, historical_swings_subset)
                
                if count <= 2:
                    path_is_clear = True
            
            target = current_target # pass to downstream dataframe logging

            # C. Momentum Check (48-bar FVG fuel)
            if has_expansion: bars_since_fvg = 0
            else: bars_since_fvg += 1
            momentum_valid = (bars_since_fvg <= 48)
            
            # Final LRR Check (Raw Environment)
            is_run_state = current_state in [PriceDeliveryState.EXPANSION, PriceDeliveryState.REVERSAL]
            # LRR requires Run State + Clear Path + Fresh Momentum
            raw_env = "HRR"
            if is_run_state and path_is_clear and momentum_valid:
                raw_env = "LRR"
                
            # --- VIDEO 7 REBUILD STEP 3: HYSTERESIS SMOOTHING ---
            if raw_env == "LRR":
                consec_lrr += 1
                consec_hrr = 0
            else:
                consec_hrr += 1
                consec_lrr = 0
                
            if current_env == "HRR" and consec_lrr >= 8:
                current_env = "LRR"
            elif current_env == "LRR" and consec_hrr >= 8:
                current_env = "HRR"
            
            # ── Step 2: Log Speed (Displacement) Interactions ──────────
            if displacement is not None:
                if not pd.isna(displacement["Displacement"].iloc[i]):
                    speed_interactions[i] = displacement["Displacement"].iloc[i]
            
            # ── Step 3: Log Clean Liquidity (Magnets) ──────────
            if reversals is not None:
                row_rev = reversals.iloc[i]
                if not pd.isna(row_rev["Sweep_Cleanliness"]):
                    clean_sweeps[i] = row_rev["Sweep_Cleanliness"]
            
            states.append(current_state.value)
            sovereign_envs.append(current_env)
            targets.append(target)

        # ── Step 5: Weekly High/Low Attribution ──────────
        ohlc_copy = ohlc.copy()
        ohlc_copy["kz"] = killzones
        ohlc_copy["day"] = days_of_week
        
        ohlc_copy["week"] = ohlc_copy.index.isocalendar().week
        for week_id, group in ohlc_copy.groupby("week"):
            if len(group) == 0: continue
            
            w_high_idx = group["high"].idxmax()
            w_low_idx  = group["low"].idxmin()
            
            w_high_day = group.loc[w_high_idx, "day"]
            w_high_kz  = group.loc[w_high_idx, "kz"]
            w_low_day  = group.loc[w_low_idx, "day"]
            w_low_kz   = group.loc[w_low_idx, "kz"]
            
            indices = ohlc_copy.index.get_indexer(group.index)
            for idx in indices:
                weekly_h_day[idx] = f"{w_high_day} ({w_high_kz})"
                weekly_l_day[idx] = f"{w_low_day} ({w_low_kz})"

        results = pd.DataFrame({
            'State': states,
            'DayOfWeek': days_of_week,
            'Killzone': killzones,
            'Displacement_Spd': speed_interactions,
            'Sweep_Cleanliness': clean_sweeps,
            'Weekly_H_Day': weekly_h_day,
            'Weekly_L_Day': weekly_l_day,
            'SovereignEnv': sovereign_envs,
            'Target': targets
        }, index=ohlc.index)

        return results

def institutional_cascade_signals(
    ohlc_ltf: pd.DataFrame,
    reversals_ltf: pd.DataFrame,
    daily_ob: pd.DataFrame,
    daily_ohlc: pd.DataFrame,
    weekly_ob: pd.DataFrame,
    weekly_ohlc: pd.DataFrame,
    monthly_ob_df: pd.DataFrame,
    fvg_df: pd.DataFrame = None,
    smt_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    ICT Month 3, Video 4: Formal 4-Tier Institutional Cascade.
    
    This engine enforces strict fractal nesting of structural arrays:
    Monthly Zone -> Weekly OB (overlapping monthly) -> Daily OB (overlapping weekly) -> LTF Execution.

    Parameters
    ----------
    ohlc_ltf       : Execution timeframe (e.g., 4H or 1H)
    reversals_ltf  : Reversals detected on the LTF
    daily_ob       : Daily Order Blocks
    daily_ohlc     : Daily OHLC
    weekly_ob      : Weekly Order Blocks
    weekly_ohlc    : Weekly OHLC
    monthly_ob_df  : Monthly Range OB dataset
    fvg_df         : FVG dataframe on LTF (optional)
    
    Returns
    -------
    pd.DataFrame with 'turtle_soup_bull' and 'turtle_soup_bear' indicating valid cascade setups.
    """
    n = len(ohlc_ltf)
    bull_flags    = np.zeros(n, dtype=bool)
    bear_flags    = np.zeros(n, dtype=bool)
    ts_entry_price = np.full(n, np.nan)
    ts_ob_tops    = np.full(n, np.nan)
    ts_ob_bots    = np.full(n, np.nan)
    ts_ob_stops   = np.full(n, np.nan)
    ts_tgt_fvg    = np.full(n, np.nan)
    ts_tgt_macro  = np.full(n, np.nan)

    # 1. Resolve Monthly Zone
    if monthly_ob_df is None or len(monthly_ob_df) == 0:
        return pd.DataFrame({'turtle_soup_bull': bull_flags, 'turtle_soup_bear': bear_flags}, index=ohlc_ltf.index)

    last_m = monthly_ob_df.iloc[-1]
    m_bull_active = bool(last_m.get('monthly_bull_ob_active', False))
    m_bear_active = bool(last_m.get('monthly_bear_ob_active', False))
    m_bull_low = float(last_m.get('monthly_down_ob_low', np.nan))
    m_bull_high = float(last_m.get('monthly_down_ob_high', np.nan))
    m_bear_low = float(last_m.get('monthly_up_ob_low', np.nan))
    m_bear_high = float(last_m.get('monthly_up_ob_high', np.nan))

    rev_vals = reversals_ltf['Reversal'].values
    c_prices = ohlc_ltf['close'].values

    # Build active Weekly OBs that overlap the Monthly zone
    valid_weekly_bull = []
    valid_weekly_bear = []

    for i in range(len(weekly_ob)):
        w_ob = weekly_ob.iloc[i]
        w_bar = weekly_ohlc.iloc[i]
        if pd.isna(w_ob['OB']): continue
        if not pd.isna(w_ob['MitigatedIndex']) and w_ob['MitigatedIndex'] > 0: continue
        
        # Bullish Weekly OB -> MUST overlap Bullish Monthly OB
        if w_ob['OB'] == 1.0 and m_bull_active:
            w_top = float(w_ob['Top'])
            w_bot = float(w_bar['open'])
            if not (w_bot > m_bull_high or w_top < m_bull_low): # overlap check
                valid_weekly_bull.append((w_ob, w_bar, w_top, w_bot))
                
        # Bearish Weekly OB -> MUST overlap Bearish Monthly OB
        elif w_ob['OB'] == -1.0 and m_bear_active:
            w_top = float(w_bar['open'])
            w_bot = float(w_ob['Bottom'])
            if not (w_bot > m_bear_high or w_top < m_bear_low):
                valid_weekly_bear.append((w_ob, w_bar, w_top, w_bot))

    # Build active Daily OBs that overlap a valid Weekly OB
    valid_daily_bull = []
    valid_daily_bear = []
    
    for i in range(len(daily_ob)):
        d_ob = daily_ob.iloc[i]
        d_bar = daily_ohlc.iloc[i]
        if pd.isna(d_ob['OB']): continue
        if not pd.isna(d_ob['MitigatedIndex']) and d_ob['MitigatedIndex'] > 0: continue
        
        if d_ob['OB'] == 1.0:
            d_top = float(d_ob['Top'])
            d_bot = float(d_bar['open'])
            for w_ob, w_bar, w_top, w_bot in valid_weekly_bull:
                if not (d_bot > w_top or d_top < w_bot): # overlap
                    valid_daily_bull.append((d_ob, d_bar, d_top, d_bot))
                    break
                    
        elif d_ob['OB'] == -1.0:
            d_top = float(d_bar['open'])
            d_bot = float(d_ob['Bottom'])
            for w_ob, w_bar, w_top, w_bot in valid_weekly_bear:
                if not (d_bot > w_top or d_top < w_bot): # overlap
                    valid_daily_bear.append((d_ob, d_bar, d_top, d_bot))
                    break

    for i in range(n):
        rev = rev_vals[i]
        c = c_prices[i]
        
        # SMT Bias Filter
        smt_bias = 'NEUTRAL'
        if smt_df is not None:
            # get the daily smt bias for the current 4H candle
            # ohlc_ltf.index[i] gives us the current timestamp
            current_date = str(ohlc_ltf.index[i].date())[:10]
            try:
                smt_bias = smt_df.loc[:current_date].iloc[-1]['smt_bias']
            except (KeyError, IndexError):
                pass

        if rev == 1.0 and valid_daily_bull and smt_bias != 'BEARISH':
            for d_ob, d_bar, d_top, d_bot in valid_daily_bull:
                if d_bot <= c <= d_top:
                    bull_flags[i] = True
                    ts_ob_tops[i] = d_top
                    ts_ob_bots[i] = d_bot
                    ts_entry_price[i] = d_bot
                    ts_ob_stops[i] = (d_bot + float(d_bar['close'])) / 2.0
                    ts_tgt_macro[i] = m_bear_high # Monthly Ceiling for Bullish setups
                    
                    if fvg_df is not None:
                        bull_fvgs = fvg_df[(fvg_df['FVG'] == 1.0) & (fvg_df['MitigatedIndex'] > i) & (fvg_df['Bottom'] > c)]
                        if len(bull_fvgs) > 0:
                            ts_tgt_fvg[i] = float(bull_fvgs['Bottom'].min())
                    break
                    
        elif rev == -1.0 and valid_daily_bear and smt_bias != 'BULLISH':
            for d_ob, d_bar, d_top, d_bot in valid_daily_bear:
                if d_bot <= c <= d_top:
                    bear_flags[i] = True
                    ts_ob_tops[i] = d_top
                    ts_ob_bots[i] = d_bot
                    ts_entry_price[i] = d_top
                    ts_ob_stops[i] = (d_top + float(d_bar['close'])) / 2.0
                    ts_tgt_macro[i] = m_bull_low # Monthly Floor for Bearish setups
                    
                    if fvg_df is not None:
                        bear_fvgs = fvg_df[(fvg_df['FVG'] == -1.0) & (fvg_df['MitigatedIndex'] > i) & (fvg_df['Top'] < c)]
                        if len(bear_fvgs) > 0:
                            ts_tgt_fvg[i] = float(bear_fvgs['Top'].max())
                    break

    return pd.DataFrame({
        'turtle_soup_bull': bull_flags,
        'turtle_soup_bear': bear_flags,
        'ts_ob_top': ts_ob_tops,
        'ts_ob_bottom': ts_ob_bots,
        'ts_entry_price': ts_entry_price,
        'ts_ob_stop': ts_ob_stops,
        'ts_target_fvg': ts_tgt_fvg,
        'ts_target_near': ts_tgt_macro, 
    }, index=ohlc_ltf.index)
