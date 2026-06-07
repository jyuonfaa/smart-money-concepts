code_to_append = r'''
# ================================================================
# SMT DIVERGENCE — module-level functions (bypass @apply decorator)
# ICT Month 3, Video 5 — Institutional Market Structure, pp.216–226
#
# CRITICAL: These are intentionally at MODULE LEVEL (zero indent),
# OUTSIDE the smc class. Monkey-patched onto smc at the bottom.
# Do NOT move inside the class — @apply(inputvalidator) would wrap
# them and break the calling convention on Python 3.11+.
# ================================================================


def _smt_divergence(
    ohlc,
    benchmark_ohlc,
    asset_swings,
    correlation="inverse",
    lookaround_bars=5,
    fvg_df=None,
    liquidity_df=None,
):
    """
    ICT Month 3, Video 5 — Institutional Market Structure (SMT Divergence).

    Detects all four non-symmetrical divergence scenarios between a primary
    asset and its correlated/inversely-correlated benchmark, plus symmetrical
    trend-confirmation conditions.

    Gap 1 (p.222): FVG void on benchmark confirmed as closed-in.
    Gap 2 (p.226): Use smt_apply_bias_filter() to gate ob()/ny_midnight_open().

    Parameters
    ----------
    ohlc            : OHLC of the primary asset (e.g. AUDUSD)
    benchmark_ohlc  : OHLC of the benchmark (DXY for inverse correlation)
    asset_swings    : output of smc.swing_highs_lows_v4() on ohlc
                      Required columns: 'type' ('HIGH'/'LOW'), 'ts', 'p'
    correlation     : "inverse" (DXY) | "positive" (e.g. GBPUSD vs EURUSD)
    lookaround_bars : bars either side of a swing to search for extremes
    fvg_df          : optional pre-computed FVG df (backward-compat)
    liquidity_df    : optional Liquidity df for sweep-gate confirmation

    Returns
    -------
    pd.DataFrame indexed like ohlc. Columns:
        smt_bias, smt_bullish_div, smt_bearish_div,
        smt_bullish_div_bm, smt_bearish_div_bm,
        smt_trend_confirmed, smt_trend_direction,
        smt_swept_high, smt_swept_low,
        smt_confirmed, smt_at_liquidity, smt_bias_event
    """
    asset_ohlc = ohlc

    df = pd.DataFrame(index=asset_ohlc.index)
    df['smt_bias']            = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
    df['smt_bullish_div']     = False
    df['smt_bearish_div']     = False
    df['smt_bullish_div_bm']  = False
    df['smt_bearish_div_bm']  = False
    df['smt_trend_confirmed'] = False
    df['smt_trend_direction'] = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
    df['smt_swept_high']      = np.nan
    df['smt_swept_low']       = np.nan
    df['smt_confirmed']       = False
    df['smt_at_liquidity']    = False
    df['smt_bias_event']      = pd.Series(np.nan, index=asset_ohlc.index, dtype='object')

    if len(asset_swings) < 2 or benchmark_ohlc is None or len(benchmark_ohlc) == 0:
        return df

    bm = benchmark_ohlc

    # ── Price window helpers (tolerate index mismatches via nearest lookup) ──
    def _win_max(target, ts):
        try:
            i = (target.index.get_loc(ts) if ts in target.index
                 else target.index.get_indexer([ts], method='nearest')[0])
            return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['high'].max()
        except Exception:
            return np.nan

    def _win_min(target, ts):
        try:
            i = (target.index.get_loc(ts) if ts in target.index
                 else target.index.get_indexer([ts], method='nearest')[0])
            return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['low'].min()
        except Exception:
            return np.nan

    def _bh(ts): return _win_max(bm, ts)
    def _bl(ts): return _win_min(bm, ts)
    def _ah(ts): return _win_max(asset_ohlc, ts)
    def _al(ts): return _win_min(asset_ohlc, ts)

    # ── Safe write helper ────────────────────────────────────────────────────
    # BM-led scenarios (C, D, Symmetrical) use DXY timestamps. If that date
    # is missing from the AUDUSD index, df.loc[dxy_ts] creates a spurious row.
    # This helper maps any timestamp to the nearest existing df row instead.
    def _set(ts, col, val):
        if ts in df.index:
            df.loc[ts, col] = val
        else:
            i = df.index.get_indexer([ts], method='nearest')[0]
            df.iloc[i, df.columns.get_loc(col)] = val

    asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
    asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

    bm_swings = smc.swing_highs_lows_v4(bm)
    bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
    bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

    # ── Divergence detection ─────────────────────────────────────────────────
    if correlation == "inverse":

        # A — Asset LL + BM fails HH → BULLISH
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                    _set(t1, 'smt_bullish_div', True)
                    _set(t1, 'smt_swept_low',   float(p1))
                    _set(t1, 'smt_bias_event',  'BULLISH')

        # B — Asset HH + BM fails LL → BEARISH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                    _set(t1, 'smt_bearish_div', True)
                    _set(t1, 'smt_swept_high',  float(p1))
                    _set(t1, 'smt_bias_event',  'BEARISH')

        # C — BM LL + Asset fails HH → BEARISH
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                    _set(t1, 'smt_bearish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BEARISH')

        # D — BM HH + Asset fails LL → BULLISH
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                    _set(t1, 'smt_bullish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BULLISH')

        # Symmetrical Bullish — DXY LL + Asset HH → trend up continues
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 > ah0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BULLISH')
                    _set(t1, 'smt_bias_event',      'BULLISH')

        # Symmetrical Bearish — DXY HH + Asset LL → trend down continues
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 < al0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BEARISH')
                    _set(t1, 'smt_bias_event',      'BEARISH')

    elif correlation == "positive":

        # A — Asset HH + BM fails HH → BEARISH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                    _set(t1, 'smt_bearish_div', True)
                    _set(t1, 'smt_bias_event',  'BEARISH')

        # B — Asset LL + BM fails LL → BULLISH
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                    _set(t1, 'smt_bullish_div', True)
                    _set(t1, 'smt_bias_event',  'BULLISH')

        # C — BM HH + Asset fails HH → BEARISH
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                    _set(t1, 'smt_bearish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BEARISH')

        # D — BM LL + Asset fails LL → BULLISH
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                    _set(t1, 'smt_bullish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BULLISH')

        # Symmetrical Bullish — Asset HH + BM HH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 > h0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BULLISH')
                    _set(t1, 'smt_bias_event',      'BULLISH')

        # Symmetrical Bearish — Asset LL + BM LL
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 < l0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BEARISH')
                    _set(t1, 'smt_bias_event',      'BEARISH')

    # Forward-fill bias from event markers (persists until next signal)
    df['smt_bias'] = df['smt_bias_event'].ffill().fillna('NEUTRAL')

    # ── GAP 1: FVG void "closed in" confirmation (ICT p.222) ─────────────────
    # ICT: "Once the void right after that down candle is closed in,
    #       we know there is underlying strength."
    # Sequence: (1) find last opposing-direction candle on benchmark near signal,
    #           (2) detect the FVG gap formed with surrounding candles,
    #           (3) confirm price later trades back into that gap zone.
    def _ob_fvg_closed_in(bm_df, ts, direction):
        center_i = (bm_df.index.get_loc(ts) if ts in bm_df.index
                    else bm_df.index.get_indexer([ts], method='nearest')[0])
        start_i = max(1, center_i - lookaround_bars)
        window  = bm_df.iloc[start_i:center_i + 1]

        if direction == 'BEARISH':
            ob_mask = window['close'] < window['open']   # down candle = OB candidate
        else:
            ob_mask = window['close'] > window['open']   # up candle = OB candidate

        ob_candles = window[ob_mask]
        if ob_candles.empty:
            return False

        ob_loc = bm_df.index.get_loc(ob_candles.index[-1])
        # Defensive: get_loc may return slice/array on non-unique index
        if isinstance(ob_loc, slice):
            ob_loc = ob_loc.start
        elif not isinstance(ob_loc, (int, np.integer)):
            ob_loc = int(np.where(ob_loc)[0][0])

        if ob_loc < 1 or ob_loc + 2 >= len(bm_df):
            return False

        prev_c = bm_df.iloc[ob_loc - 1]
        next_c = bm_df.iloc[ob_loc + 1]

        if direction == 'BEARISH':
            fvg_top, fvg_bot = float(prev_c['low']), float(next_c['high'])
        else:
            fvg_top, fvg_bot = float(next_c['low']), float(prev_c['high'])

        if fvg_bot >= fvg_top:
            return False   # no genuine gap

        future = bm_df.iloc[ob_loc + 2:]
        if future.empty:
            return False
        return bool(((future['high'] >= fvg_bot) & (future['low'] <= fvg_top)).any())

    if fvg_df is not None and not fvg_df.empty and 'FVG' in fvg_df.columns:
        # Backward-compat: caller supplied pre-computed FVG dataframe
        for ts in df[df['smt_bias_event'] == 'BULLISH'].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            end = min(len(df), i + lookaround_bars + 1)
            if (fvg_df.iloc[i:end]['FVG'] == 1).any():
                df.loc[ts, 'smt_confirmed'] = True
        for ts in df[df['smt_bias_event'] == 'BEARISH'].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            end = min(len(df), i + lookaround_bars + 1)
            if (fvg_df.iloc[i:end]['FVG'] == -1).any():
                df.loc[ts, 'smt_confirmed'] = True
    else:
        # ICT-native: OB candle + FVG void + close-in on benchmark (p.222)
        for ts in df[df['smt_bias_event'] == 'BEARISH'].index:
            df.loc[ts, 'smt_confirmed'] = _ob_fvg_closed_in(bm, ts, 'BEARISH')
        for ts in df[df['smt_bias_event'] == 'BULLISH'].index:
            df.loc[ts, 'smt_confirmed'] = _ob_fvg_closed_in(bm, ts, 'BULLISH')

    # ── LIQUIDITY SWEEP CONFIRMATION ─────────────────────────────────────────
    if (liquidity_df is not None
            and not liquidity_df.empty
            and 'Level' in liquidity_df.columns
            and 'Swept' in liquidity_df.columns):
        for ts in df[~df['smt_swept_high'].isna()].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            bull_sw = liquidity_df[liquidity_df['Liquidity'] == 1]['Swept']
            bull_sw = bull_sw[(bull_sw > 0) & (~pd.isna(bull_sw))]
            if any((bull_sw >= max(0, i - lookaround_bars)) & (bull_sw <= i + lookaround_bars)):
                df.loc[ts, 'smt_at_liquidity'] = True
        for ts in df[~df['smt_swept_low'].isna()].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            bear_sw = liquidity_df[liquidity_df['Liquidity'] == -1]['Swept']
            bear_sw = bear_sw[(bear_sw > 0) & (~pd.isna(bear_sw))]
            if any((bear_sw >= max(0, i - lookaround_bars)) & (bear_sw <= i + lookaround_bars)):
                df.loc[ts, 'smt_at_liquidity'] = True
    else:
        df['smt_at_liquidity'] = True

    # smt_bias_event is kept in the return — verify_month3_video5.py reads it
    return df


def _smt_apply_bias_filter(signal_df, smt_df, signal_type):
    """
    ICT Month 3, Video 5, p.226 — Execution Layer Bias Wiring.

    Gates a signal DataFrame through the SMT macro bias so that only
    signals aligned with institutional directional intent are returned.

    Usage:
        ob_df = smc.ob(ohlc)
        short_obs = smc.smt_apply_bias_filter(ob_df[ob_df['OB']==-1], smt_df, 'BEARISH')

    Parameters
    ----------
    signal_df   : DataFrame of signals to filter (e.g. bearish Order Blocks)
    smt_df      : output of smt_divergence() — must contain 'smt_bias' column
    signal_type : 'BULLISH' or 'BEARISH'

    Returns
    -------
    Filtered signal_df containing only bias-aligned rows.
    """
    if smt_df is None or 'smt_bias' not in smt_df.columns or signal_df.empty:
        return signal_df

    combined_idx = signal_df.index.union(smt_df.index)
    bias_series = (
        smt_df['smt_bias']
        .reindex(combined_idx)
        .ffill()
        .reindex(signal_df.index)
        .fillna('NEUTRAL')
    )
    return signal_df[bias_series == signal_type]


# ── Attach to smc class ──────────────────────────────────────────────────────
# Runs AFTER @apply(inputvalidator) has already wrapped the class.
# _smt_divergence and _smt_apply_bias_filter are never subject to the decorator.
# Do NOT move these lines above the class definition.
smc.smt_divergence = _smt_divergence
smc.smt_apply_bias_filter = _smt_apply_bias_filter
'''

with open(r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py', 'a', encoding='utf-8') as f:
    f.write('\n' + code_to_append + '\n')
