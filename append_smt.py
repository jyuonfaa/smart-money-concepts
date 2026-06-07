"""
Append smt_divergence to smc.py class.
Run from d:\C.Slim\ict-intelligence directory.
"""

smc_path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(smc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Guard: don't double-append
if 'smt_divergence' in content:
    print("smt_divergence already present — nothing to do.")
else:
    method_code = '''
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
        ICT Month 3, Video 5: Institutional Market Structure (SMT Divergence).

        Detects ALL FOUR scenarios of non-symmetrical price delivery between
        a primary asset and a correlated/inversely correlated benchmark.

        Parameters
        ----------
        asset_ohlc      : OHLC of the primary foreign currency (e.g. AUDUSD)
        benchmark_ohlc  : OHLC of the benchmark (DXY / USDCHF for inverse; GBPUSD for positive)
        asset_swings    : Swing highs/lows from smc.swing_highs_lows_v4()
        correlation     : "inverse" (DXY) | "positive" (GBPUSD/EURUSD)
        lookaround_bars : bars either side of a swing timestamp to search for extremes
        fvg_df          : optional FVG dataframe for displacement confirmation
        liquidity_df    : optional Liquidity dataframe for sweep confirmation

        Returns
        -------
        pd.DataFrame with columns:
            smt_bias, smt_bullish_div, smt_bearish_div,
            smt_bullish_div_bm, smt_bearish_div_bm,
            smt_trend_confirmed, smt_trend_direction,
            smt_swept_high, smt_swept_low,
            smt_confirmed, smt_at_liquidity
        """
        import pandas as pd
        import numpy as np

        df = pd.DataFrame(index=asset_ohlc.index)
        df['smt_bias']             = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
        df['smt_bullish_div']      = False
        df['smt_bearish_div']      = False
        df['smt_bullish_div_bm']   = False
        df['smt_bearish_div_bm']   = False
        df['smt_trend_confirmed']  = False
        df['smt_trend_direction']  = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
        df['smt_swept_high']       = np.nan
        df['smt_swept_low']        = np.nan
        df['smt_confirmed']        = False
        df['smt_at_liquidity']     = False
        df['smt_bias_event']       = pd.Series(np.nan, index=asset_ohlc.index, dtype='object')

        if len(asset_swings) < 2 or benchmark_ohlc is None or len(benchmark_ohlc) == 0:
            df['smt_bias'] = 'NEUTRAL'
            return df.drop(columns=['smt_bias_event'])

        bm = benchmark_ohlc

        def _get_window_max(target_df, ts):
            try:
                if ts not in target_df.index:
                    i = target_df.index.get_indexer([ts], method='nearest')[0]
                else:
                    i = target_df.index.get_loc(ts)
                s = max(0, i - lookaround_bars)
                e = min(len(target_df), i + lookaround_bars + 1)
                return target_df.iloc[s:e]['high'].max()
            except Exception:
                return np.nan

        def _get_window_min(target_df, ts):
            try:
                if ts not in target_df.index:
                    i = target_df.index.get_indexer([ts], method='nearest')[0]
                else:
                    i = target_df.index.get_loc(ts)
                s = max(0, i - lookaround_bars)
                e = min(len(target_df), i + lookaround_bars + 1)
                return target_df.iloc[s:e]['low'].min()
            except Exception:
                return np.nan

        def _bm_high(ts):  return _get_window_max(bm, ts)
        def _bm_low(ts):   return _get_window_min(bm, ts)
        def _ah(ts):       return _get_window_max(asset_ohlc, ts)
        def _al(ts):       return _get_window_min(asset_ohlc, ts)

        asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
        asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

        bm_swings = cls.swing_highs_lows_v4(benchmark_ohlc)
        bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
        bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

        if correlation == "inverse":
            # Scenario A — Asset-led Bullish: Asset LL + DXY fails HH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    h0, h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_swept_low']   = float(p1)
                        df.loc[t1, 'smt_bias_event']  = 'BULLISH'

            # Scenario B — Asset-led Bearish: Asset HH + DXY fails LL
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    l0, l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_swept_high']  = float(p1)
                        df.loc[t1, 'smt_bias_event']  = 'BEARISH'

            # Scenario C — BM-led Bearish: DXY LL + Asset fails HH
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # Scenario D — BM-led Bullish: DXY HH + Asset fails LL
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BULLISH'

            # Symmetrical Bullish: DXY LL + Asset HH — trend continues up
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 > ah0:
                        df.loc[t1, 'smt_trend_confirmed']  = True
                        df.loc[t1, 'smt_trend_direction']  = 'BULLISH'
                        df.loc[t1, 'smt_bias_event']       = 'BULLISH'

            # Symmetrical Bearish: DXY HH + Asset LL — trend continues down
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 < al0:
                        df.loc[t1, 'smt_trend_confirmed']  = True
                        df.loc[t1, 'smt_trend_direction']  = 'BEARISH'
                        df.loc[t1, 'smt_bias_event']       = 'BEARISH'

        elif correlation == "positive":
            # Scenario A — Asset HH + Benchmark fails HH => BEARISH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    h0, h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                        df.loc[t1, 'smt_bearish_div']  = True
                        df.loc[t1, 'smt_bias_event']   = 'BEARISH'

            # Scenario B — Asset LL + Benchmark fails LL => BULLISH
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    l0, l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                        df.loc[t1, 'smt_bullish_div']  = True
                        df.loc[t1, 'smt_bias_event']   = 'BULLISH'

            # Scenario C — BM HH + Asset fails HH => BEARISH
            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bp1 > bp0:
                    ah0, ah1 = _ah(t0), _ah(t1)
                    if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BEARISH'

            # Scenario D — BM LL + Asset fails LL => BULLISH
            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bp1 < bp0:
                    al0, al1 = _al(t0), _al(t1)
                    if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event']     = 'BULLISH'

            # Symmetrical Bullish: Asset HH + BM HH
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:
                    h0, h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(h0) or pd.isna(h1)) and h1 > h0:
                        df.loc[t1, 'smt_trend_confirmed']  = True
                        df.loc[t1, 'smt_trend_direction']  = 'BULLISH'
                        df.loc[t1, 'smt_bias_event']       = 'BULLISH'

            # Symmetrical Bearish: Asset LL + BM LL
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:
                    l0, l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(l0) or pd.isna(l1)) and l1 < l0:
                        df.loc[t1, 'smt_trend_confirmed']  = True
                        df.loc[t1, 'smt_trend_direction']  = 'BEARISH'
                        df.loc[t1, 'smt_bias_event']       = 'BEARISH'

        # Forward-fill bias from event markers
        df['smt_bias'] = df['smt_bias_event'].ffill().fillna('NEUTRAL')

        # ── FVG DISPLACEMENT CONFIRMATION (ICT: wait for FVG/void to close in) ─
        if fvg_df is not None and not fvg_df.empty and 'FVG' in fvg_df.columns:
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
            df['smt_confirmed'] = True

        # ── LIQUIDITY SWEEP CONFIRMATION (ICT: must sweep an Old High/Low) ─────
        if (liquidity_df is not None
                and not liquidity_df.empty
                and 'Level' in liquidity_df.columns
                and 'Swept' in liquidity_df.columns):
            # Bearish SMT: must have swept a Bullish liquidity pool (Old High, Liquidity==1)
            for ts in df[~df['smt_swept_high'].isna()].index:
                i = df.index.get_indexer([ts], method='nearest')[0]
                bull_sw = liquidity_df[liquidity_df['Liquidity'] == 1]['Swept']
                bull_sw = bull_sw[(bull_sw > 0) & (~pd.isna(bull_sw))]
                if any((bull_sw >= max(0, i - lookaround_bars)) & (bull_sw <= i + lookaround_bars)):
                    df.loc[ts, 'smt_at_liquidity'] = True
            # Bullish SMT: must have swept a Bearish liquidity pool (Old Low, Liquidity==-1)
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

    with open(smc_path, 'a', encoding='utf-8') as f:
        f.write(method_code)
    print("smt_divergence appended to smc.py")
