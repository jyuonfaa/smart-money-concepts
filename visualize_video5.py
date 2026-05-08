"""
ICT Video 4: TRIPLE TIMEFRAME FRACTAL AUDIT
Daily (Anchor) | 4H (Interbank) | 15M (Surgical)
"""
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
import uuid

def calculate_ote_status(df, extreme_ts, ote62, p_origin, p_extreme, mode):
    post_swing = df.loc[extreme_ts:]
    if post_swing.empty: return "ACTIVE"
    has_entered = False
    for _, row in post_swing.iterrows():
        if mode == 'BULLISH' and row['close'] < p_origin: return "INVALIDATED"
        if mode == 'BEARISH' and row['close'] > p_origin: return "INVALIDATED"
        if mode == 'BULLISH':
            if row['low'] <= ote62: has_entered = True
            if has_entered and row['high'] > p_extreme: return "MITIGATED"
        else:
            if row['high'] >= ote62: has_entered = True
            if has_entered and row['low'] < p_extreme: return "MITIGATED"
    return "IN_ZONE" if (ote62 <= df['close'].iloc[-1] <= p_extreme if mode=='BEARISH' else p_extreme >= df['close'].iloc[-1] >= ote62) else "ACTIVE"

def run_video5_premium():
    symbol = "EURUSD=X"
    output_name = "ICT_VIDEO_5_PREMIUM.html"

    print(f"Generating Premium Transposition Audit...")
    df_1d  = yf.download(symbol, period="1y", interval="1d", progress=False)
    df_4h  = yf.download(symbol, period="1mo", interval="1h", progress=False) # Resample to 4H
    df_15m = yf.download(symbol, period="7d", interval="15m", progress=False)

    def clean_df(df, resample=None):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if resample:
            df = df.resample(resample).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    df_1d, df_4h, df_15m = clean_df(df_1d), clean_df(df_4h, "4h"), clean_df(df_15m)

    # --- LOGIC ---
    d_swings = smc.swing_highs_lows_v4(df_1d)
    all_otes = []
    for i in range(1, len(d_swings)):
        p1, p5 = d_swings.iloc[i-1], d_swings.iloc[i]
        mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
        r = abs(p5['p'] - p1['p'])
        o62 = p5['p'] - 0.62*r if mode == 'BULLISH' else p5['p'] + 0.62*r
        o79 = p5['p'] - 0.79*r if mode == 'BULLISH' else p5['p'] + 0.79*r
        o705 = p5['p'] - 0.705*r if mode == 'BULLISH' else p5['p'] + 0.705*r
        status = calculate_ote_status(df_1d, p5['ts'], o62, p1['p'], p5['p'], mode)
        
        all_otes.append({
            'mode': mode, 'ts': p5['ts'], 'conf_ts': p5['conf_ts'], 
            '62': o62, '705': o705, '79': o79, 'target': p5['p'], # Target is always the extreme of the impulse (p5)
            'status': status, 'label': f"D1 OTE [{p5['ts'].strftime('%b %d')}]"
        })

        # --- VIDEO 5: PREMIUM STOP RUN (WIDER SWING) ---
        # If the immediate setup was invalidated (stops run), check if the wider swing holds.
        if status == "INVALIDATED" and i >= 3:
            p_minus_2 = d_swings.iloc[i-3] # Prior Major Swing Extreme
            if p_minus_2['type'] == p1['type']:
                is_wider = (mode == 'BEARISH' and p_minus_2['p'] > p1['p']) or (mode == 'BULLISH' and p_minus_2['p'] < p1['p'])
                if is_wider:
                    r_wide = abs(p5['p'] - p_minus_2['p'])
                    o62_w = p5['p'] - 0.62*r_wide if mode == 'BULLISH' else p5['p'] + 0.62*r_wide
                    o79_w = p5['p'] - 0.79*r_wide if mode == 'BULLISH' else p5['p'] + 0.79*r_wide
                    o705_w = p5['p'] - 0.705*r_wide if mode == 'BULLISH' else p5['p'] + 0.705*r_wide
                    
                    status_w = calculate_ote_status(df_1d, p5['ts'], o62_w, p_minus_2['p'], p5['p'], mode)
                    all_otes.append({
                        'mode': mode, 'ts': p5['ts'], 'conf_ts': p5['conf_ts'], 
                        '62': o62_w, '705': o705_w, '79': o79_w, 'target': p5['p'], 
                        'status': status_w, 'label': f"STOP RUN OTE [{p5['ts'].strftime('%b %d')}]"
                    })

    # --- FIX 2: MAXIMUM 3 ACTIVE ZONES ---
    active_otes = [o for o in all_otes if o['status'] in ['ACTIVE', 'IN_ZONE']]
    display_otes = sorted(active_otes, key=lambda x: x['conf_ts'], reverse=True)[:3]

    # --- CONSOLE VERIFICATION ---
    print("\n" + "="*40)
    print(f"VERIFICATION: OTE DYNAMICS")
    print(f"Total Swing Pairs Found:  {len(all_otes)}")
    print(f"Currently Active/Open:    {len(active_otes)}")
    print(f"Selected for Display:     {len(display_otes)}")
    for o in display_otes:
        print(f" -> {o['label']} (Confirmed: {o['conf_ts'].strftime('%Y-%m-%d')})")
    print("="*40 + "\n")

    # --- VISUALS ---
    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.03, row_heights=[0.3, 0.3, 0.4],
                        subplot_titles=("DAILY (Setup Anchor)", "4H (Interbank Transposition)", "15M (Surgical Execution)"))

    # Plot Candlesticks
    for i, df_plot in enumerate([df_1d, df_4h, df_15m]):
        fig.add_trace(go.Candlestick(x=df_plot.index.strftime('%Y-%m-%d %H:%M:%S'), open=df_plot['open'], high=df_plot['high'], low=df_plot['low'], close=df_plot['close'], name=f"P{i+1}"), row=i+1, col=1)

    # Transpose Selected Daily OTEs to ALL panes (Fix 1: Axis-Safe Anchoring)
    for ote in display_otes:
        color = "rgba(0, 255, 0, 0.15)" if ote['mode'] == 'BULLISH' else "rgba(255, 0, 0, 0.15)"
        target_color = "#26a69a" if ote['mode'] == 'BULLISH' else "#ef5350"
        for r in [1, 2, 3]:
            # Clip to visible data range of each pane to prevent axis stretching
            df_curr = [df_1d, df_4h, df_15m][r-1]
            start_ts = max(ote['conf_ts'], df_curr.index[0])
            x0_str = start_ts.strftime('%Y-%m-%d %H:%M:%S')
            x_end_str = df_curr.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            
            fig.add_shape(type="rect", x0=x0_str, x1=x_end_str, y0=ote['79'], y1=ote['62'], fillcolor=color, line_width=1 if r>1 else 0, line_dash="dash", row=r, col=1)
            fig.add_shape(type="line", x0=x0_str, x1=x_end_str, y0=ote['705'], y1=ote['705'], line=dict(color="Gold", width=2, dash="dash"), row=r, col=1)
            # Profit Target (Liquidity Pool) - Axis-Safe Anchoring
            fig.add_shape(type="line", x0=x0_str, x1=x_end_str, y0=ote['target'], y1=ote['target'], line=dict(color=target_color, width=2, dash="dot"), row=r, col=1)
            fig.add_annotation(x=x_end_str, y=ote['target'], text="<b>Draw on Liquidity</b>", showarrow=False, font=dict(color=target_color, size=10), xanchor="right", yanchor="bottom", row=r, col=1)

    # --- EXACT ARCHITECTURE FIX: GLOBAL ALTERNATION + TEMPORAL COOLDOWN ---
    # (Existing logic remains)
    m15_swings = smc.swing_highs_lows_v4(df_15m)
    all_candidates = []
    zone_cooldowns = {}

    for _, row in m15_swings.iterrows():
        for i, ote in enumerate(active_otes):
            if min(ote['62'], ote['79']) <= row['p'] <= max(ote['62'], ote['79']):
                cooldown_key = (i, row['type'])
                if cooldown_key in zone_cooldowns:
                    if row['ts'] - zone_cooldowns[cooldown_key] < pd.Timedelta(hours=2):
                        continue
                all_candidates.append((row['ts'], row['p'], row['type'], i, row['label']))
                zone_cooldowns[cooldown_key] = row['ts']
                break 

    all_candidates.sort(key=lambda x: x[0])
    last_type = None
    final_signals = []

    for candidate in all_candidates:
        ts, price, sig_type, zone_id, label = candidate
        if sig_type != last_type:
            final_signals.append(candidate)
            last_type = sig_type

    # Render
    for candidate in final_signals:
        ts, price, sig_type, zone_id, label = candidate
        c = "#26a69a" if sig_type == "LOW" else "#ef5350"
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        fig.add_annotation(x=ts_str, y=price, text=f"<b>{label}</b>", showarrow=True, arrowhead=2, ay=80 if sig_type=="LOW" else -80, font=dict(color=c, size=10), row=3, col=1)

    # --- INSTITUTIONAL SEQUENCE AUDIT ---
    print("\n" + "="*40)
    print("INSTITUTIONAL SEQUENCE AUDIT (15M)")
    print(f"{'TIMESTAMP':<20} | {'TYPE':<5} | {'PRICE':<8} | {'ZONE'}")
    print("-" * 50)
    for ts, p, t, z, l in final_signals:
        print(f"{ts.strftime('%Y-%m-%d %H:%M'):<20} | {t:<5} | {p:<8.4f} | {active_otes[z]['label']}")
    print("="*40 + "\n")

    # Step 5 — Verify
    print("VERIFICATION: DEFINITIVE FIX")
    plotted_signals = [a for a in fig.layout.annotations if "Confirmed" in a.text]
    plotted_sequence = ["H" if "High" in a.text else "L" for a in plotted_signals]
    assert len(plotted_signals) == len(final_signals)
    for i in range(1, len(plotted_sequence)):
        assert plotted_sequence[i] != plotted_sequence[i-1]
    print(f"Plotted count: {len(plotted_signals)}")
    print(f"Chart sequence: {plotted_sequence}")
    print("ASSERTION PASSED: Chart is 100% alternating.")
    print("="*40 + "\n")

    for r in [1, 2, 3]:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[17, 17], pattern="hour")], row=r, col=1)
    
    fig.update_layout(height=1600, template="plotly_dark", title="ICT VIDEO 5: PREMIUM TRANSPOSITION AUDIT", showlegend=False, xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False, xaxis3_rangeslider_visible=False)
    fig.write_html(output_name)
    try:
        fig.write_image(r"C:\Users\ESTHER\.gemini\antigravity\brain\5d443e5f-6d00-473d-a0cc-ec741fd891c7\premium_audit_visual.png")
        print(f"Visual saved to artifacts: premium_audit_visual.png")
    except Exception as e:
        print(f"Warning: Could not save image: {e}")
    print(f"\n[DONE] PREMIUM AUDIT SUCCESS: OPEN '{output_name}'")

if __name__ == "__main__":
    run_video5_premium()
