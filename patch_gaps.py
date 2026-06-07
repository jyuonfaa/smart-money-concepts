"""
patch_gaps.py — Fix Gap 1 (FVG close-in) and Gap 2 (bias filter wiring).

Gap 1: Replace naive FVG window-check with proper OB candle + FVG void + close-in
       detection on the benchmark (DXY), exactly as ICT describes on p.222.

Gap 2: Append smt_apply_bias_filter() classmethod that gates ob() / ny_midnight_open()
       signals through the SMT bias, as ICT specifies on p.226.
"""

smc_path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(smc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── STEP 1: find & remove the old smt_divergence block ───────────────────────
START_MARKER = '\n    def smt_divergence('
start_idx = content.find(START_MARKER)
if start_idx == -1:
    raise RuntimeError("Cannot locate 'def smt_divergence(' in smc.py")

# Walk forward to find the next top-level method definition (4-space indent @classmethod or def)
# so we know where smt_divergence ends.
search_from = start_idx + len(START_MARKER)
import re
next_method = re.search(r'\n    @classmethod\n    def |\n    def [a-z]', content[search_from:])
if next_method:
    end_idx = search_from + next_method.start()
else:
    end_idx = len(content)   # smt_divergence is the last thing in the file

# Cut out the old method
content = content[:start_idx] + content[end_idx:]

# ── STEP 2: build the corrected smt_divergence ───────────────────────────────
new_smt_divergence = r'''
    @classmethod
    def smt_divergence(
        cls,
        asset_ohlc,
        benchmark_ohlc,
        asset_swings,
        correlation: str = "inverse",
        lookaround_bars: int = 5,
        fvg_df=None,
        liquidity_df=None,
    ):
        """
        ICT Month 3, Video 5 — Institutional Market Structure (SMT Divergence).

        Detects ALL FOUR non-symmetrical divergence scenarios between a primary
        asset and its correlated/inversely-correlated benchmark, as well as
        symmetrical trend-confirmation conditions.

        Gap 1 fix (p.222): FVG confirmation now performs the full ICT sequence:
            (1) locate the specific opposing OB candle on the benchmark
            (2) detect the FVG void it creates
            (3) verify price has since "closed in" to that void
        If fvg_df is supplied it is used instead (backward-compat override).

        Gap 2 fix (p.226): Use smt_apply_bias_filter() to gate ob() /
        ny_midnight_open() signals through the returned smt_bias column.

        Parameters
        ----------
        asset_ohlc      : OHLC of the primary foreign currency (e.g. AUDUSD)
        benchmark_ohlc  : OHLC of the benchmark (DXY / USDCHF for inverse)
        asset_swings    : swing highs/lows from smc.swing_highs_lows_v4()
        correlation     : "inverse" (DXY) | "positive" (GBPUSD/EURUSD)
        lookaround_bars : bars either side of a swing timestamp to search extremes
        fvg_df          : optional pre-computed FVG df (backward-compat override)
        liquidity_df    : optional Liquidity df for sweep-gate confirmation

        Returns
        -------
        pd.DataFrame — columns:
            smt_bias, smt_bullish_div, smt_bearish_div,
            smt_bullish_div_bm, smt_bearish_div_bm,
            smt_trend_confirmed, smt_trend_direction,
            smt_swept_high, smt_swept_low,
            smt_confirmed, smt_at_liquidity
        """
        import pandas as pd
        import numpy as np

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
            df['smt_bias'] = 'NEUTRAL'
            return df.drop(columns=['smt_bias_event'])

        bm = benchmark_ohlc

        # ── Structural window helpers ─────────────────────────────────────────
        def _win_max(target, ts):
            try:
                i = target.index.get_loc(ts) if ts in target.index \
                    else target.index.get_indexer([ts], method='nearest')[0]
                return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['high'].max()
            except Exception:
                return np.nan

        def _win_min(target, ts):
            try:
                i = target.index.get_loc(ts) if ts in target.index \
                    else target.index.get_indexer([ts], method='nearest')[0]
                return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['low'].min()
            except Exception:
                return np.nan

        def _bh(ts): return _win_max(bm, ts)
        def _bl(ts): return _win_min(bm, ts)
        def _ah(ts): return _win_max(asset_ohlc, ts)
        def _al(ts): return _win_min(asset_ohlc, ts)

        asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
        asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

        bm_swings = cls.swing_highs_lows_v4(benchmark_ohlc)
        bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
        bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

        # ── Divergence detection ──────────────────────────────────────────────
        if correlation == "inverse":
            # Scenario A — Asset LL + BM fails HH → BULLISH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    h0, h1 = _bh(t0), _bh(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bullish_div']  = True
                        df.loc[t1, 'smt_swept_low']    = float(p1)
                        df.loc[t1, 'smt_bias_event']   = 'BULLISH'

            # Scenario B — Asset HH + BM fails LL → BEARISH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    l0, l1 = _bl(t0), _bl(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bearish_div']  = True
                        df.loc[t1, 'smt_swept_high']   = float(p1)
                        df.loc[t1, 'smt_bias_event']   = 'BEARISH'

            # Scenario C — BM LL + Asset fails HH → BEARISH
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # Scenario D — BM HH + Asset fails LL → BULLISH
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BULLISH'

            # Symmetrical Bullish — DXY LL + Asset HH → trend continues up
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 > ah0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BULLISH'
                        df.loc[t1, 'smt_bias_event']      = 'BULLISH'

            # Symmetrical Bearish — DXY HH + Asset LL → trend continues down
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 < al0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BEARISH'
                        df.loc[t1, 'smt_bias_event']      = 'BEARISH'

        elif correlation == "positive":
            # Scenario A — Asset HH + BM fails HH → BEARISH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    h0, h1 = _bh(t0), _bh(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_bias_event']  = 'BEARISH'

            # Scenario B — Asset LL + BM fails LL → BULLISH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    l0, l1 = _bl(t0), _bl(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_bias_event']  = 'BULLISH'

            # Scenario C — BM HH + Asset fails HH → BEARISH
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # Scenario D — BM LL + Asset fails LL → BULLISH
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BULLISH'

            # Symmetrical Bullish — Asset HH + BM HH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    h0, h1 = _bh(t0), _bh(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 > h0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BULLISH'
                        df.loc[t1, 'smt_bias_event']      = 'BULLISH'

            # Symmetrical Bearish — Asset LL + BM LL
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    l0, l1 = _bl(t0), _bl(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 < l0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BEARISH'
                        df.loc[t1, 'smt_bias_event']      = 'BEARISH'

        # Forward-fill bias from event markers
        df['smt_bias'] = df['smt_bias_event'].ffill().fillna('NEUTRAL')

        # ── GAP 1 FIX: FVG void "closed in" confirmation (ICT p.222) ─────────
        # ICT: "Once the void right after that down candle is closed in,
        #       we know there's underlying strength."
        #
        # Sequence (bearish example):
        #   1. Locate the last bearish OB candle on the benchmark near each divergence
        #   2. Detect the FVG void formed around it (prev_low > next_high gap)
        #   3. Confirm price subsequently trades INTO (closes in) that FVG zone
        #
        # If fvg_df is passed by the caller, use it instead (backward-compat).

        def _ob_fvg_closed_in(bm_df, ts, direction):
            """
            Returns True if the OB candle + FVG void + close-in sequence is
            present on the benchmark around timestamp 'ts'.
            direction: 'BEARISH' -> find last bearish (close < open) candle
                       'BULLISH' -> find last bullish (close > open) candle
            """
            center_i = (bm_df.index.get_loc(ts) if ts in bm_df.index
                        else bm_df.index.get_indexer([ts], method='nearest')[0])

            # Search window: up to lookaround_bars before the divergence point
            start_i = max(1, center_i - lookaround_bars)
            window = bm_df.iloc[start_i:center_i + 1]

            if direction == 'BEARISH':
                ob_mask = window['close'] < window['open']  # bearish candle
            else:
                ob_mask = window['close'] > window['open']  # bullish candle

            ob_candles = window[ob_mask]
            if ob_candles.empty:
                return False

            # Most recent qualifying OB candle
            ob_ts = ob_candles.index[-1]
            ob_i  = bm_df.index.get_loc(ob_ts)
            if ob_i < 1 or ob_i + 2 >= len(bm_df):
                return False

            prev_c = bm_df.iloc[ob_i - 1]
            next_c = bm_df.iloc[ob_i + 1]

            if direction == 'BEARISH':
                # Bearish FVG void: prev_candle.low > next_candle.high
                fvg_top    = prev_c['low']
                fvg_bottom = next_c['high']
            else:
                # Bullish FVG void: next_candle.low > prev_candle.high
                fvg_top    = next_c['low']
                fvg_bottom = prev_c['high']

            if fvg_bottom >= fvg_top:
                return False  # No actual gap — FVG does not exist

            # "Closed in" = any subsequent candle overlaps the FVG zone
            future = bm_df.iloc[ob_i + 2:]
            if future.empty:
                return False
            return bool(((future['high'] >= fvg_bottom) & (future['low'] <= fvg_top)).any())

        if fvg_df is not None and not fvg_df.empty and 'FVG' in fvg_df.columns:
            # Backward-compat: caller supplied a pre-computed FVG dataframe
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

        # ── LIQUIDITY SWEEP CONFIRMATION (ICT: must sweep an Old High/Low) ─────
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

        return df.drop(columns=['smt_bias_event'])
'''

# ── STEP 3: build smt_apply_bias_filter (Gap 2) ──────────────────────────────
new_bias_filter = r'''
    @classmethod
    def smt_apply_bias_filter(cls, signal_df, smt_df, signal_type):
        """
        ICT Month 3, Video 5, p.226 — Execution Layer Bias Wiring.

        Gates any signal DataFrame through the SMT macro bias so that only
        signals aligned with the institutional directional bias are returned.

        "If you are a short-term trader, you could be looking to sell short at
        every 60-minute or 4-hour bearish order block."
        "If you are a day trader, you could be selling above the opening price
        above the midnight candle in New York."

        Usage examples
        --------------
        # Short-term (OB-based):
        ob_df   = smc.ob(ohlc)
        smt_df  = smc.smt_divergence(ohlc, dxy, swings)
        # Keep only BEARISH OBs when macro bias is BEARISH:
        bearish_obs = smc.smt_apply_bias_filter(ob_df[ob_df['OB']==-1], smt_df, 'BEARISH')

        # Day-trader (midnight-open based):
        mo_df   = smc.ny_midnight_open(ohlc)
        # Keep only SELL signals when macro bias is BEARISH:
        sells   = smc.smt_apply_bias_filter(mo_df[mo_df['direction']=='SELL'], smt_df, 'BEARISH')

        Parameters
        ----------
        signal_df   : DataFrame with DatetimeIndex — any signal output (ob, ny_midnight_open, etc.)
        smt_df      : output of smt_divergence() — must contain 'smt_bias' column
        signal_type : 'BULLISH' — only keep signals where smt_bias == 'BULLISH'
                      'BEARISH' — only keep signals where smt_bias == 'BEARISH'

        Returns
        -------
        Filtered signal_df containing only bias-aligned rows.
        """
        import pandas as pd

        if signal_df is None or signal_df.empty:
            return signal_df
        if smt_df is None or 'smt_bias' not in smt_df.columns:
            return signal_df

        # Align bias to every signal timestamp using forward-fill (bias persists
        # until overridden by a new divergence event — ICT p.224)
        combined_idx = signal_df.index.union(smt_df.index)
        bias_series = (
            smt_df['smt_bias']
            .reindex(combined_idx)
            .ffill()
            .reindex(signal_df.index)
            .fillna('NEUTRAL')
        )

        return signal_df[bias_series == signal_type]
'''

# ── STEP 4: append both methods to the (now cleaned) file content ─────────────
content = content.rstrip()   # trim trailing whitespace / blank lines

with open(smc_path, 'w', encoding='utf-8') as f:
    f.write(content)
    f.write(new_smt_divergence)
    f.write(new_bias_filter)
    f.write('\n')   # ensure file ends with newline

print("Done. smt_divergence (Gap 1) and smt_apply_bias_filter (Gap 2) written.")
