"""
patch_gaps_v2.py — Fix Gap 1 + Gap 2 without @classmethod conflict.

Root cause: @apply(inputvalidator) wraps bound classmethods into plain functions.
In Python 3.11+, calling the stored bound classmethod object directly raises
TypeError. Fix: use plain methods (no @classmethod) and reference smc directly.
"""
import re

smc_path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(smc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── Remove any previously appended smt_* methods ────────────────────────────
for marker in ['    def smt_divergence(', '    def smt_apply_bias_filter(']:
    idx = content.find(marker)
    if idx != -1:
        # Find the next same-level definition or EOF
        nxt = re.search(r'\n    def [a-z]|\n    @', content[idx + len(marker):])
        end = idx + len(marker) + nxt.start() if nxt else len(content)
        content = content[:idx] + content[end:]

content = content.rstrip()

# ── New smt_divergence (plain method, no @classmethod) ──────────────────────
new_smt_divergence = '''

    def smt_divergence(
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

        Detects ALL FOUR non-symmetrical divergence scenarios between a primary
        asset and its correlated/inversely-correlated benchmark, plus symmetrical
        trend-confirmation conditions.

        Gap 1 fix (p.222): FVG confirmation now performs the full ICT sequence:
            1. Locate the last opposing OB candle on the benchmark near divergence
            2. Detect the FVG void it creates (prev_low > next_high or vice-versa)
            3. Confirm price subsequently "closes in" to that void

        Gap 2 fix (p.226): Use smt_apply_bias_filter() to gate ob() /
        ny_midnight_open() signals through the returned smt_bias.

        Parameters
        ----------
        ohlc            : OHLC of the primary asset (e.g. AUDUSD)
        benchmark_ohlc  : OHLC of the benchmark (DXY / USDCHF for inverse)
        asset_swings    : swing highs/lows from smc.swing_highs_lows_v4()
        correlation     : "inverse" (DXY) | "positive" (GBPUSD/EURUSD)
        lookaround_bars : bars either side of a swing to search for extremes
        fvg_df          : optional pre-computed FVG df (backward-compat override)
        liquidity_df    : optional Liquidity df for sweep-gate confirmation

        Returns
        -------
        pd.DataFrame with columns:
            smt_bias, smt_bullish_div, smt_bearish_div,
            smt_bullish_div_bm, smt_bearish_div_bm,
            smt_trend_confirmed, smt_trend_direction,
            smt_swept_high, smt_swept_low,
            smt_confirmed, smt_at_liquidity
        """
        asset_ohlc = ohlc  # renamed by inputvalidator; keep alias for clarity

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

        # ── Structural window helpers ─────────────────────────────────────
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

        asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
        asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

        bm_swings = smc.swing_highs_lows_v4(bm)
        bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
        bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

        # ── Divergence detection ──────────────────────────────────────────
        if correlation == "inverse":
            # A — Asset LL + BM fails HH → BULLISH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    h0, h1 = _bh(t0), _bh(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_swept_low']   = float(p1)
                        df.loc[t1, 'smt_bias_event']  = 'BULLISH'

            # B — Asset HH + BM fails LL → BEARISH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    l0, l1 = _bl(t0), _bl(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_swept_high']  = float(p1)
                        df.loc[t1, 'smt_bias_event']  = 'BEARISH'

            # C — BM LL + Asset fails HH → BEARISH
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # D — BM HH + Asset fails LL → BULLISH
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BULLISH'

            # Symmetrical Bullish — DXY LL + Asset HH → trend up
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 > ah0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BULLISH'
                        df.loc[t1, 'smt_bias_event']      = 'BULLISH'

            # Symmetrical Bearish — DXY HH + Asset LL → trend down
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
            # A — Asset HH + BM fails HH → BEARISH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    h0, h1 = _bh(t0), _bh(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_bias_event']  = 'BEARISH'

            # B — Asset LL + BM fails LL → BULLISH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    l0, l1 = _bl(t0), _bl(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_bias_event']  = 'BULLISH'

            # C — BM HH + Asset fails HH → BEARISH
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # D — BM LL + Asset fails LL → BULLISH
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

        # ── GAP 1 FIX: FVG void "closed in" confirmation (ICT p.222) ─────
        # ICT: "Once the void right after that down candle is closed in,
        #       we know there is underlying strength."
        # Sequence: (1) find last opposing OB candle on benchmark near signal,
        #           (2) detect the FVG gap it forms with surrounding candles,
        #           (3) confirm price later closes into that gap zone.
        def _ob_fvg_closed_in(bm_df, ts, direction):
            center_i = (bm_df.index.get_loc(ts) if ts in bm_df.index
                        else bm_df.index.get_indexer([ts], method='nearest')[0])
            start_i = max(1, center_i - lookaround_bars)
            window  = bm_df.iloc[start_i:center_i + 1]

            # Locate the last opposing-direction candle (OB candidate)
            if direction == 'BEARISH':
                ob_mask = window['close'] < window['open']   # down candle
            else:
                ob_mask = window['close'] > window['open']   # up candle

            ob_candles = window[ob_mask]
            if ob_candles.empty:
                return False

            ob_i = bm_df.index.get_loc(ob_candles.index[-1])
            if ob_i < 1 or ob_i + 2 >= len(bm_df):
                return False

            prev_c = bm_df.iloc[ob_i - 1]
            next_c = bm_df.iloc[ob_i + 1]

            # FVG zone: gap between candle before and candle after the OB
            if direction == 'BEARISH':
                fvg_top, fvg_bot = prev_c['low'], next_c['high']
            else:
                fvg_top, fvg_bot = next_c['low'], prev_c['high']

            if fvg_bot >= fvg_top:
                return False   # no genuine gap

            # "Closed in" = any future candle overlaps the FVG zone
            future = bm_df.iloc[ob_i + 2:]
            if future.empty:
                return False
            return bool(((future['high'] >= fvg_bot) & (future['low'] <= fvg_top)).any())

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

        # ── LIQUIDITY SWEEP CONFIRMATION ──────────────────────────────────
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

# ── New smt_apply_bias_filter (plain method, no @classmethod) ────────────────
new_bias_filter = '''
    def smt_apply_bias_filter(
        ohlc,
        smt_df,
        signal_type,
    ):
        """
        ICT Month 3, Video 5, p.226 — Execution Layer Bias Wiring.

        Gates any signal DataFrame through the SMT macro bias so that only
        signals aligned with institutional directional intent are returned.

        "If you are a short-term trader, you could be looking to sell short at
         every 60-minute or 4-hour bearish order block."
        "If you are a day trader, you could be selling above the opening price
         above the midnight candle in New York."

        Usage
        -----
        smt_df = smc.smt_divergence(ohlc, dxy, swings)

        # Gate bearish OBs through BEARISH bias (short entries only):
        ob_df = smc.ob(ohlc)
        short_obs = smc.smt_apply_bias_filter(ob_df[ob_df['OB']==-1], smt_df, 'BEARISH')

        # Gate midnight-open sells through BEARISH bias:
        mo_df  = smc.ny_midnight_open(ohlc)
        sells  = smc.smt_apply_bias_filter(mo_df[mo_df['direction']=='SELL'], smt_df, 'BEARISH')

        Parameters
        ----------
        ohlc        : primary asset OHLC (required by inputvalidator; not used internally)
        smt_df      : output of smt_divergence() — must contain 'smt_bias' column
        signal_type : 'BULLISH' or 'BEARISH'

        Returns
        -------
        Filtered ohlc-indexed DataFrame containing only bias-aligned rows.
        """
        if smt_df is None or 'smt_bias' not in smt_df.columns or ohlc.empty:
            return ohlc

        # Forward-fill bias to every bar of the asset OHLC (bias persists until
        # overridden by the next divergence event — ICT p.224)
        combined_idx = ohlc.index.union(smt_df.index)
        bias_series = (
            smt_df['smt_bias']
            .reindex(combined_idx)
            .ffill()
            .reindex(ohlc.index)
            .fillna('NEUTRAL')
        )
        return ohlc[bias_series == signal_type]
'''

with open(smc_path, 'w', encoding='utf-8') as f:
    f.write(content)
    f.write(new_smt_divergence)
    f.write(new_bias_filter)
    f.write('\n')

print("Done.")
