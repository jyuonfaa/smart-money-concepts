import re

file_path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The new method
new_method = """    @classmethod
    def smt_divergence(
        cls,
        asset_ohlc: pd.DataFrame,
        benchmark_ohlc: pd.DataFrame,
        asset_swings: pd.DataFrame,
        correlation: str = "inverse",
        lookaround_bars: int = 5,
        fvg_df: pd.DataFrame = None,
        liquidity_df: pd.DataFrame = None,
    ) -> pd.DataFrame:
        \"\"\"
        ICT Month 3, Video 5: Institutional Market Structure (SMT Divergence).

        Detects ALL FOUR scenarios of non-symmetrical price delivery between
        a primary asset and a correlated/inversely correlated benchmark.
        \"\"\"
        df = pd.DataFrame(index=asset_ohlc.index)
        df['smt_bias']             = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
        df['smt_bullish_div']      = False   # Asset-led: Asset LL, Benchmark fails HH (inverse)
        df['smt_bearish_div']      = False   # Asset-led: Asset HH, Benchmark fails LL (inverse)
        df['smt_bullish_div_bm']   = False   # Benchmark-led: Benchmark HH, Asset fails LL (inverse)
        df['smt_bearish_div_bm']   = False   # Benchmark-led: Benchmark LL, Asset fails HH (inverse)
        df['smt_trend_confirmed']  = False   # True when both assets move symmetrically
        df['smt_trend_direction']  = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
        df['smt_swept_high']       = np.nan  
        df['smt_swept_low']        = np.nan  
        df['smt_confirmed']        = False   # FVG validation
        df['smt_at_liquidity']     = False   # Liquidity sweep validation
        df['smt_bias_event']       = pd.Series(np.nan, index=asset_ohlc.index, dtype='object')

        if len(asset_swings) < 2 or benchmark_ohlc is None or len(benchmark_ohlc) == 0:
            df['smt_bias'] = 'NEUTRAL'
            return df.drop(columns=['smt_bias_event'])

        bm = benchmark_ohlc

        def _get_window_max(target_df, ts):
            try:
                if ts not in target_df.index:
                    idx = target_df.index.get_indexer([ts], method='nearest')[0]
                else:
                    idx = target_df.index.get_loc(ts)
                start = max(0, idx - lookaround_bars)
                end = min(len(target_df), idx + lookaround_bars + 1)
                return target_df.iloc[start:end]['high'].max()
            except Exception:
                return np.nan

        def _get_window_min(target_df, ts):
            try:
                if ts not in target_df.index:
                    idx = target_df.index.get_indexer([ts], method='nearest')[0]
                else:
                    idx = target_df.index.get_loc(ts)
                start = max(0, idx - lookaround_bars)
                end = min(len(target_df), idx + lookaround_bars + 1)
                return target_df.iloc[start:end]['low'].min()
            except Exception:
                return np.nan

        def _bm_high(ts): return _get_window_max(bm, ts)
        def _bm_low(ts): return _get_window_min(bm, ts)
        def _asset_high(ts): return _get_window_max(asset_ohlc, ts)
        def _asset_low(ts): return _get_window_min(asset_ohlc, ts)

        asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
        asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

        bm_swings = cls.swing_highs_lows_v4(benchmark_ohlc)
        bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
        bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

        if correlation == "inverse":
            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:  # Asset Lower Low
                    bm_h0, bm_h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(bm_h0) or pd.isna(bm_h1)) and bm_h1 < bm_h0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_swept_low']   = float(p1)
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:  # Asset Higher High
                    bm_l0, bm_l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(bm_l0) or pd.isna(bm_l1)) and bm_l1 > bm_l0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_swept_high']  = float(p1)
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bm_p0, bm_p1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bm_p1 < bm_p0:  # Benchmark Lower Low
                    a_h0, a_h1 = _asset_high(t0), _asset_high(t1)
                    if not (pd.isna(a_h0) or pd.isna(a_h1)) and a_h1 < a_h0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bm_p0, bm_p1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bm_p1 > bm_p0:  # Benchmark Higher High
                    a_l0, a_l1 = _asset_low(t0), _asset_low(t1)
                    if not (pd.isna(a_l0) or pd.isna(a_l1)) and a_l1 > a_l0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bm_p0, bm_p1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bm_p1 < bm_p0:  # DXY made a Lower Low
                    a_h0, a_h1 = _asset_high(t0), _asset_high(t1)
                    if not (pd.isna(a_h0) or pd.isna(a_h1)) and a_h1 > a_h0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BULLISH'
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bm_p0, bm_p1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bm_p1 > bm_p0:  # DXY made a Higher High
                    a_l0, a_l1 = _asset_low(t0), _asset_low(t1)
                    if not (pd.isna(a_l0) or pd.isna(a_l1)) and a_l1 < a_l0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BEARISH'
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

        elif correlation == "positive":
            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:  # Asset Higher High
                    bm_h0, bm_h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(bm_h0) or pd.isna(bm_h1)) and bm_h1 < bm_h0:
                        df.loc[t1, 'smt_bearish_div'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:  # Asset Lower Low
                    bm_l0, bm_l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(bm_l0) or pd.isna(bm_l1)) and bm_l1 > bm_l0:
                        df.loc[t1, 'smt_bullish_div'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(bm_highs)):
                t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
                bm_p0, bm_p1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
                if bm_p1 > bm_p0:
                    a_h0, a_h1 = _asset_high(t0), _asset_high(t1)
                    if not (pd.isna(a_h0) or pd.isna(a_h1)) and a_h1 < a_h0:
                        df.loc[t1, 'smt_bearish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

            for i in range(1, len(bm_lows)):
                t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
                bm_p0, bm_p1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
                if bm_p1 < bm_p0:
                    a_l0, a_l1 = _asset_low(t0), _asset_low(t1)
                    if not (pd.isna(a_l0) or pd.isna(a_l1)) and a_l1 > a_l0:
                        df.loc[t1, 'smt_bullish_div_bm'] = True
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(asset_highs)):
                t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
                p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
                if p1 > p0:  # Asset Higher High
                    bm_h0, bm_h1 = _bm_high(t0), _bm_high(t1)
                    if not (pd.isna(bm_h0) or pd.isna(bm_h1)) and bm_h1 > bm_h0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BULLISH'
                        df.loc[t1, 'smt_bias_event'] = 'BULLISH'

            for i in range(1, len(asset_lows)):
                t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
                p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
                if p1 < p0:  # Asset Lower Low
                    bm_l0, bm_l1 = _bm_low(t0), _bm_low(t1)
                    if not (pd.isna(bm_l0) or pd.isna(bm_l1)) and bm_l1 < bm_l0:
                        df.loc[t1, 'smt_trend_confirmed'] = True
                        df.loc[t1, 'smt_trend_direction'] = 'BEARISH'
                        df.loc[t1, 'smt_bias_event'] = 'BEARISH'

        df['smt_bias'] = df['smt_bias_event'].ffill().fillna('NEUTRAL')

        # ── FVG CONFIRMATION ─────────────────────────────────────────
        if fvg_df is not None and not fvg_df.empty and 'FVG' in fvg_df.columns:
            for ts in df[df['smt_bias_event'] == 'BULLISH'].index:
                idx = df.index.get_indexer([ts], method='nearest')[0]
                end_idx = min(len(df), idx + lookaround_bars + 1)
                # Look for a bullish FVG (FVG == 1) in the window
                if (fvg_df.iloc[idx:end_idx]['FVG'] == 1).any():
                    df.loc[ts, 'smt_confirmed'] = True

            for ts in df[df['smt_bias_event'] == 'BEARISH'].index:
                idx = df.index.get_indexer([ts], method='nearest')[0]
                end_idx = min(len(df), idx + lookaround_bars + 1)
                # Look for a bearish FVG (FVG == -1) in the window
                if (fvg_df.iloc[idx:end_idx]['FVG'] == -1).any():
                    df.loc[ts, 'smt_confirmed'] = True
        else:
            # If no FVG df provided, assume confirmed to maintain backwards compatibility
            df['smt_confirmed'] = True

        # ── LIQUIDITY CONFIRMATION ───────────────────────────────────
        if liquidity_df is not None and not liquidity_df.empty and 'Level' in liquidity_df.columns and 'Swept' in liquidity_df.columns:
            # Bearish SMT is valid if a Bullish Liquidity Pool (Old High) was recently SWEPT
            for ts in df[~df['smt_swept_high'].isna()].index:
                idx = df.index.get_indexer([ts], method='nearest')[0]
                bull_sweeps = liquidity_df[liquidity_df['Liquidity'] == 1]['Swept']
                bull_sweeps = bull_sweeps[(bull_sweeps > 0) & (~pd.isna(bull_sweeps))]
                
                if any((bull_sweeps >= max(0, idx - lookaround_bars)) & (bull_sweeps <= idx + lookaround_bars)):
                    df.loc[ts, 'smt_at_liquidity'] = True

            # Bullish SMT is valid if a Bearish Liquidity Pool (Old Low) was recently SWEPT
            for ts in df[~df['smt_swept_low'].isna()].index:
                idx = df.index.get_indexer([ts], method='nearest')[0]
                bear_sweeps = liquidity_df[liquidity_df['Liquidity'] == -1]['Swept']
                bear_sweeps = bear_sweeps[(bear_sweeps > 0) & (~pd.isna(bear_sweeps))]
                
                if any((bear_sweeps >= max(0, idx - lookaround_bars)) & (bear_sweeps <= idx + lookaround_bars)):
                    df.loc[ts, 'smt_at_liquidity'] = True
        else:
            # Maintain backward compatibility
            df['smt_at_liquidity'] = True

        return df.drop(columns=['smt_bias_event'])
"""

# Extract the old method using regex
pattern = re.compile(r'    @classmethod\n    def smt_divergence\([\s\S]*?        return df\.drop\(columns=\[\'smt_bias_event\'\]\)\n', re.MULTILINE)
if not pattern.search(content):
    pattern = re.compile(r'    @classmethod\n    def smt_divergence\([\s\S]*?        return df\n\n', re.MULTILINE)

new_content = pattern.sub(new_method, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Updated smc.py")
