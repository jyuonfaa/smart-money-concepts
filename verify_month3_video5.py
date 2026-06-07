import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def run_smt_verification():
    print("Loading AUDUSD and Synthetic DXY data...")
    
    chunks = []
    for chunk in pd.read_csv(
        'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
        sep=';', names=['date','open','high','low','close','volume'],
        index_col=False, chunksize=50_000
    ):
        chunk['date'] = pd.to_datetime(chunk['date'], format='%Y%m%d %H%M%S')
        chunk.set_index('date', inplace=True)
        daily_chunk = chunk.resample('1D').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        chunks.append(daily_chunk)
    aud_daily = pd.concat(chunks).groupby(level=0).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    
    dxy_daily = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DXY_Daily_2016.csv', index_col='date', parse_dates=True)
    
    print("Calculating Swings and SMT Divergence (ALL 4 ICT Scenarios)...")
    aud_swings = smc.swing_highs_lows_v4(aud_daily)
    smt_df = smc.smt_divergence(aud_daily, dxy_daily, aud_swings, correlation="inverse")
    
    # Extract all signal types
    bullish_asset  = smt_df[smt_df['smt_bullish_div']]
    bearish_asset  = smt_df[smt_df['smt_bearish_div']]
    bullish_bm     = smt_df[smt_df['smt_bullish_div_bm']]
    bearish_bm     = smt_df[smt_df['smt_bearish_div_bm']]
    trend_bull     = smt_df[(smt_df['smt_trend_confirmed']) & (smt_df['smt_trend_direction'] == 'BULLISH')]
    trend_bear     = smt_df[(smt_df['smt_trend_confirmed']) & (smt_df['smt_trend_direction'] == 'BEARISH')]
    
    print(f"\n--- ICT Video 5: All SMT Scenarios ---")
    print(f"Scenario A (Asset-led Bullish)  : {len(bullish_asset):3d} — Asset Lower Low, DXY fails Higher High")
    print(f"Scenario B (Asset-led Bearish)  : {len(bearish_asset):3d} — Asset Higher High, DXY fails Lower Low")
    print(f"Scenario C (BM-led Bearish)     : {len(bearish_bm):3d}  — DXY Lower Low, Asset fails Higher High")
    print(f"Scenario D (BM-led Bullish)     : {len(bullish_bm):3d}  — DXY Higher High, Asset fails Lower Low")
    print(f"Symmetrical Bullish Confirm     : {len(trend_bull):3d}  — DXY LL + Asset HH (trend continues up)")
    print(f"Symmetrical Bearish Confirm     : {len(trend_bear):3d}  — DXY HH + Asset LL (trend continues down)")
    print(f"--------------------------------------")
    print(f"Total SMT Signals               : {len(bullish_asset)+len(bearish_asset)+len(bullish_bm)+len(bearish_bm):3d}")
    print(f"Total Trend Confirmations       : {len(trend_bull)+len(trend_bear):3d}")

    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=("US Dollar Index (DXY) - Synthetic", "AUD/USD (Foreign Currency)"))
                        
    fig.add_trace(go.Candlestick(x=dxy_daily.index, open=dxy_daily['open'], high=dxy_daily['high'], low=dxy_daily['low'], close=dxy_daily['close'], name='DXY'), row=1, col=1)
    fig.add_trace(go.Candlestick(x=aud_daily.index, open=aud_daily['open'], high=aud_daily['high'], low=aud_daily['low'], close=aud_daily['close'], name='AUDUSD'), row=2, col=1)
    
    # ── SCENARIO A: Asset-led Bullish (Asset LL, DXY fails HH) — GREEN solid
    for ts, _ in bullish_asset.iterrows():
        lows = aud_swings[aud_swings['type'] == 'LOW']
        prev = lows[lows['ts'] < ts]
        if not prev.empty:
            prev_ts = prev.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=aud_daily.loc[prev_ts]['low'], x1=ts, y1=aud_daily.loc[ts]['low'], line=dict(color="Lime", width=2), row=2, col=1)
            try:
                h0 = dxy_daily.loc[str(prev_ts.date())[:10]:str((prev_ts + pd.Timedelta(days=3)).date())[:10]]['high'].max()
                h1 = dxy_daily.loc[str(ts.date())[:10]:str((ts + pd.Timedelta(days=3)).date())[:10]]['high'].max()
                fig.add_shape(type="line", x0=prev_ts, y0=h0, x1=ts, y1=h1, line=dict(color="Lime", width=2), row=1, col=1)
                fig.add_annotation(x=ts, y=aud_daily.loc[ts]['low'], text="A: SMT Bullish<br>(Asset-led)", showarrow=True, arrowhead=1, ay=50, font=dict(color="Lime"), row=2, col=1)
            except KeyError:
                pass

    # ── SCENARIO B: Asset-led Bearish (Asset HH, DXY fails LL) — RED solid
    for ts, _ in bearish_asset.iterrows():
        highs = aud_swings[aud_swings['type'] == 'HIGH']
        prev = highs[highs['ts'] < ts]
        if not prev.empty:
            prev_ts = prev.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=aud_daily.loc[prev_ts]['high'], x1=ts, y1=aud_daily.loc[ts]['high'], line=dict(color="Red", width=2), row=2, col=1)
            try:
                l0 = dxy_daily.loc[str(prev_ts.date())[:10]:str((prev_ts + pd.Timedelta(days=3)).date())[:10]]['low'].min()
                l1 = dxy_daily.loc[str(ts.date())[:10]:str((ts + pd.Timedelta(days=3)).date())[:10]]['low'].min()
                fig.add_shape(type="line", x0=prev_ts, y0=l0, x1=ts, y1=l1, line=dict(color="Red", width=2), row=1, col=1)
                fig.add_annotation(x=ts, y=aud_daily.loc[ts]['high'], text="B: SMT Bearish<br>(Asset-led)", showarrow=True, arrowhead=1, ay=-50, font=dict(color="Red"), row=2, col=1)
            except KeyError:
                pass

    # ── SCENARIO C: BM-led Bearish (DXY LL, Asset fails HH) — ORANGE dashed
    for ts, _ in bearish_bm.iterrows():
        bm_swings = smc.swing_highs_lows_v4(dxy_daily)
        bm_lows = bm_swings[bm_swings['type'] == 'LOW']
        prev = bm_lows[bm_lows['ts'] < ts]
        if not prev.empty:
            prev_ts = prev.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=dxy_daily.loc[prev_ts]['low'], x1=ts, y1=dxy_daily.loc[ts]['low'], line=dict(color="Orange", width=2, dash="dash"), row=1, col=1)
            fig.add_annotation(x=ts, y=aud_daily.asof(ts)['high'], text="C: SMT Bearish<br>(BM-led)", showarrow=True, arrowhead=1, ay=-50, font=dict(color="Orange"), row=2, col=1)

    # ── SCENARIO D: BM-led Bullish (DXY HH, Asset fails LL) — CYAN dashed
    for ts, _ in bullish_bm.iterrows():
        bm_swings = smc.swing_highs_lows_v4(dxy_daily)
        bm_highs = bm_swings[bm_swings['type'] == 'HIGH']
        prev = bm_highs[bm_highs['ts'] < ts]
        if not prev.empty:
            prev_ts = prev.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=dxy_daily.loc[prev_ts]['high'], x1=ts, y1=dxy_daily.loc[ts]['high'], line=dict(color="Cyan", width=2, dash="dash"), row=1, col=1)
            fig.add_annotation(x=ts, y=aud_daily.asof(ts)['low'], text="D: SMT Bullish<br>(BM-led)", showarrow=True, arrowhead=1, ay=50, font=dict(color="Cyan"), row=2, col=1)

    fig.update_layout(
        title="Month 3 Video 5: SMT Divergence — All 4 ICT Scenarios",
        template="plotly_dark", height=900,
        xaxis_rangeslider_visible=False, xaxis2_rangeslider_visible=False
    )
    
    out_file = "ICT_MONTH3_VIDEO5_SMT_DIVERGENCE.html"
    fig.write_html(out_file)
    print(f"\n[SUCCESS] Generated SMT visualization: {out_file}")

    # ── GAP 1 VERIFICATION: FVG void "closed in" confirmation ────────────────
    confirmed    = smt_df[smt_df['smt_confirmed']]
    not_confirmed = smt_df[
        (smt_df['smt_bias_event'].notna() if 'smt_bias_event' in smt_df.columns
         else (smt_df['smt_bullish_div'] | smt_df['smt_bearish_div'] |
               smt_df['smt_bullish_div_bm'] | smt_df['smt_bearish_div_bm']))
        & (~smt_df['smt_confirmed'])
    ]
    print(f"\n--- GAP 1: FVG Void Close-In Confirmation ---")
    print(f"SMT signals with FVG void confirmed (OB+void+close-in): {len(confirmed)}")
    print(f"SMT signals WITHOUT FVG void confirmation (sucker plays filtered): {len(not_confirmed)}")

    # ── GAP 2 VERIFICATION: bias filter gates ob() signals ───────────────────
    print(f"\n--- GAP 2: SMT Bias Filter (p.226 Execution Layer) ---")
    if 'volume' not in aud_daily.columns:
        aud_daily['volume'] = 1.0
    _ob_swings = smc.swing_highs_lows(aud_daily)
    ob_df = smc.ob(aud_daily, _ob_swings)
    if ob_df is not None and not ob_df.empty and 'OB' in ob_df.columns:
        bearish_obs_all    = ob_df[ob_df['OB'] == -1]
        bullish_obs_all    = ob_df[ob_df['OB'] == 1]
        bearish_obs_gated  = smc.smt_apply_bias_filter(bearish_obs_all, smt_df, 'BEARISH')
        bullish_obs_gated  = smc.smt_apply_bias_filter(bullish_obs_all, smt_df, 'BULLISH')
        print(f"Total Bearish OBs (raw)                 : {len(bearish_obs_all)}")
        print(f"Bearish OBs passing SMT BEARISH bias    : {len(bearish_obs_gated)}  ← short entries")
        print(f"Total Bullish OBs (raw)                 : {len(bullish_obs_all)}")
        print(f"Bullish OBs passing SMT BULLISH bias    : {len(bullish_obs_gated)}  ← long entries")
        reduction_pct = (1 - (len(bearish_obs_gated) + len(bullish_obs_gated)) /
                         max(1, len(bearish_obs_all) + len(bullish_obs_all))) * 100
        print(f"Signal noise reduction                  : {reduction_pct:.1f}% filtered out")
    else:
        print("  ob() not available on this OHLC — skipping OB gate test")

if __name__ == "__main__":
    run_smt_verification()
