"""
ICT Month 3 Video 8 - Market Maker Trap
Instrument: GBPUSD | Period: Oct-Nov 2025
Output: visualize_video8_gbpusd_2025.html
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from smartmoneyconcepts.smc import smc


def run():
    print("=== M3V8 Market Maker Trap | GBPUSD Oct-Nov 2025 ===")

    # 1. Fetch 1H data
    print("Fetching GBPUSD 1H from yfinance...")
    raw = yf.download("GBPUSD=X", start="2025-10-01", end="2025-11-30",
                      interval="1h", auto_adjust=True, progress=False)
    if raw.empty:
        print("ERROR: No data returned.")
        return
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.columns = [c.lower() for c in raw.columns]
    raw.index = pd.to_datetime(raw.index, utc=True).tz_localize(None)
    # Truncate to second precision to avoid Plotly nanosecond rendering bugs
    raw.index = raw.index.floor("s")
    gbp_1h = raw[["open", "high", "low", "close", "volume"]].dropna()
    print("  Loaded", len(gbp_1h), "1H candles")

    # 2. Resample to Daily
    gbp_daily = gbp_1h.resample("D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna()

    # 3. 1H Swings
    print("Detecting 1H swings...")
    raw_swings = smc.swing_highs_lows(gbp_1h, swing_length=5)
    # raw_swings has the same index as gbp_1h; explicitly pull timestamps from gbp_1h to avoid
    # integer-index issues if swing_highs_lows resets the index internally
    valid_mask = raw_swings["HighLow"].notna()
    valid_ts   = gbp_1h.index[valid_mask]                        # actual DatetimeIndex entries
    valid_hl   = raw_swings["HighLow"][valid_mask].values
    valid_lvl  = raw_swings["Level"][valid_mask].values
    swings_1h  = pd.DataFrame({
        "ts":   valid_ts,
        "type": ["HIGH" if v == 1 else "LOW" for v in valid_hl],
        "p":    valid_lvl,
    })

    # 4. Detect False H&S Patterns
    print("Detecting False H&S patterns...")
    patterns = smc.false_hns_patterns(gbp_1h, swings_1h)
    print("  Detected", len(patterns), "total False H&S patterns")

    # 5. Daily HTF OB Engine (zero-lookahead)
    daily_swings = smc.swing_highs_lows(gbp_daily, swing_length=3)
    obs = smc.ob(gbp_daily, daily_swings)

    htf_bias    = pd.Series(0.0,    index=gbp_1h.index)
    htf_poi_top = pd.Series(np.nan, index=gbp_1h.index)
    htf_poi_btm = pd.Series(np.nan, index=gbp_1h.index)
    daily_bias  = pd.Series(0.0,    index=gbp_daily.index)
    daily_top   = pd.Series(np.nan, index=gbp_daily.index)
    daily_btm   = pd.Series(np.nan, index=gbp_daily.index)

    current_bias = 0.0
    active_ob_top = None
    active_ob_btm = None
    active_ob_idx = 0
    pending_bias = 0.0
    pending_ob_top = None
    pending_ob_btm = None
    pending_ob_idx = 0

    for i in range(len(gbp_daily)):
        idx   = gbp_daily.index[i]
        high  = gbp_daily["high"].iloc[i]
        low   = gbp_daily["low"].iloc[i]
        close = gbp_daily["close"].iloc[i]

        # Record state BEFORE today (zero lookahead)
        daily_bias.loc[idx] = current_bias
        daily_top.loc[idx]  = active_ob_top
        daily_btm.loc[idx]  = active_ob_btm

        # All OBs enter pending unconditionally
        ob_val = obs["OB"].iloc[i]
        if pd.notna(ob_val) and ob_val != 0:
            open_price = gbp_daily["open"].iloc[i]
            ob_t = high       if ob_val == 1.0 else open_price
            ob_b = open_price if ob_val == 1.0 else low
            pending_bias    = ob_val
            pending_ob_top  = ob_t
            pending_ob_btm  = ob_b
            pending_ob_idx  = i

        # Confirm pending OB via next-day close
        if pending_bias == 1:
            if close > pending_ob_top:
                current_bias  = 1
                active_ob_top = pending_ob_top
                active_ob_btm = pending_ob_btm
                active_ob_idx = pending_ob_idx
                pending_bias  = 0
            elif close < pending_ob_btm:
                pending_bias = 0
        elif pending_bias == -1:
            if close < pending_ob_btm:
                current_bias  = -1
                active_ob_top = pending_ob_top
                active_ob_btm = pending_ob_btm
                active_ob_idx = pending_ob_idx
                pending_bias  = 0
            elif close > pending_ob_top:
                pending_bias = 0

        # Breaker flip
        if current_bias == 1 and active_ob_btm is not None:
            if close < active_ob_btm:
                prior_high = gbp_daily["high"].iloc[max(0, active_ob_idx - 10):active_ob_idx].max() if active_ob_idx > 0 else np.inf
                rally_high = gbp_daily["high"].iloc[active_ob_idx:i + 1].max()
                if rally_high > prior_high:
                    current_bias = -1
                else:
                    active_ob_top = None
                    active_ob_btm = None
                    current_bias  = 0.0
        elif current_bias == -1 and active_ob_top is not None:
            if close > active_ob_top:
                prior_low = gbp_daily["low"].iloc[max(0, active_ob_idx - 10):active_ob_idx].min() if active_ob_idx > 0 else -np.inf
                drop_low  = gbp_daily["low"].iloc[active_ob_idx:i + 1].min()
                if drop_low < prior_low:
                    current_bias = 1
                else:
                    active_ob_top = None
                    active_ob_btm = None
                    current_bias  = 0.0

    # Map daily bias onto 1H index
    for idx in gbp_1h.index:
        d = pd.Timestamp(idx.date())
        if d in daily_bias.index:
            htf_bias.loc[idx]    = daily_bias.loc[d]
            htf_poi_top.loc[idx] = daily_top.loc[d]
            htf_poi_btm.loc[idx] = daily_btm.loc[d]

    # 6. Execute signals
    print("Executing bar-by-bar sweeps on 1H...")
    signals = smc.hns_signals(gbp_1h, patterns, htf_bias, htf_poi_top, htf_poi_btm)
    buys  = signals[signals["signal"] == 1]
    sells = signals[signals["signal"] == -1]
    print("Total executions fired:", len(buys) + len(sells))
    print("  Buys:", len(buys), " | Sells:", len(sells))
    for ts, row in signals[signals["signal"] != 0].iterrows():
        print("  ", ts, "|", row["trigger_type"], "| TP1:", round(row["target_1"], 5), "| TP2:", round(row["target_2"], 5))

    # 7. Visualization
    print("Building chart...")
    fig = go.Figure()

    # Helper: convert any timestamp/index to plain ISO string for Plotly
    def px(t):
        return pd.Timestamp(t).strftime("%Y-%m-%d %H:%M:%S")

    x_1h = [px(t) for t in gbp_1h.index]

    fig.add_trace(go.Candlestick(
        x=x_1h,
        open=gbp_1h["open"], high=gbp_1h["high"],
        low=gbp_1h["low"],   close=gbp_1h["close"],
        name="GBPUSD 1H",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ))

    # Daily POI zones
    poi_segments = []
    prev_t, prev_b, prev_bias_seg, seg_start = None, None, None, None
    for idx in gbp_1h.index:
        t    = htf_poi_top.loc[idx] if idx in htf_poi_top.index else np.nan
        b    = htf_poi_btm.loc[idx] if idx in htf_poi_btm.index else np.nan
        bias = htf_bias.loc[idx]    if idx in htf_bias.index    else 0
        if pd.notna(t) and pd.notna(b):
            if t != prev_t or b != prev_b:
                if seg_start is not None:
                    poi_segments.append((seg_start, idx, prev_t, prev_b, prev_bias_seg))
                seg_start = idx
                prev_t, prev_b, prev_bias_seg = t, b, bias
        else:
            if seg_start is not None:
                poi_segments.append((seg_start, idx, prev_t, prev_b, prev_bias_seg))
                seg_start = None
                prev_t, prev_b, prev_bias_seg = None, None, None
    if seg_start is not None:
        poi_segments.append((seg_start, gbp_1h.index[-1], prev_t, prev_b, prev_bias_seg))

    for (x0, x1, yt, yb, bias) in poi_segments:
        fill = "rgba(0,210,110,0.18)"  if bias == 1 else "rgba(220,50,50,0.18)"
        edge = "rgba(0,210,110,0.7)"   if bias == 1 else "rgba(220,50,50,0.7)"
        fig.add_trace(go.Scatter(
            x=[px(x0), px(x1), px(x1), px(x0), px(x0)], y=[yb, yb, yt, yt, yb],
            fill="toself", fillcolor=fill,
            line=dict(color=edge, width=1.5),
            mode="lines", showlegend=False, hoverinfo="skip"
        ))

    # Swing markers
    highs_1h = swings_1h[swings_1h["type"] == "HIGH"]
    lows_1h  = swings_1h[swings_1h["type"] == "LOW"]
    fig.add_trace(go.Scatter(
        x=[px(t) for t in highs_1h["ts"]], y=highs_1h["p"], mode="markers",
        marker=dict(color="lime", symbol="triangle-down", size=7), name="1H Swing High"
    ))
    fig.add_trace(go.Scatter(
        x=[px(t) for t in lows_1h["ts"]], y=lows_1h["p"], mode="markers",
        marker=dict(color="tomato", symbol="triangle-up", size=7), name="1H Swing Low"
    ))

    # H&S pattern neckline geometry
    for _, pat in patterns.iterrows():
        trap_ts = pat["trap_ts"]
        t1, t2, p1, p2 = pat["t1"], pat["t2"], pat["p1"], pat["p2"]
        color = "rgba(0,210,110,0.5)" if pat["trap_type"] == 1 else "rgba(220,50,50,0.5)"
        for level, start in [(p1, t1), (p2, t2)]:
            fig.add_trace(go.Scatter(
                x=[px(start), px(trap_ts)], y=[level, level],
                mode="lines", line=dict(color=color, width=2, dash="dot"),
                showlegend=False, hoverinfo="skip"
            ))

    # BUY executions
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=[px(t) for t in buys.index],
            y=gbp_1h.loc[buys.index, "low"] * 0.9998,
            mode="markers",
            marker=dict(color="cyan", symbol="triangle-up", size=16,
                        line=dict(width=2, color="white")),
            hovertext=buys["trigger_type"],
            name="BUY - Turtle Soup"
        ))
        for idx, row in buys.iterrows():
            x_end = px(gbp_1h.index[-1])
            if pd.notna(row["target_1"]):
                fig.add_trace(go.Scatter(
                    x=[px(idx), x_end], y=[row["target_1"], row["target_1"]],
                    mode="lines", line=dict(color="cyan", width=1, dash="dot"), showlegend=False
                ))
            if pd.notna(row["target_2"]):
                fig.add_trace(go.Scatter(
                    x=[px(idx), x_end], y=[row["target_2"], row["target_2"]],
                    mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False
                ))

    # SELL executions
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=[px(t) for t in sells.index],
            y=gbp_1h.loc[sells.index, "high"] * 1.0002,
            mode="markers",
            marker=dict(color="magenta", symbol="triangle-down", size=16,
                        line=dict(width=2, color="white")),
            hovertext=sells["trigger_type"],
            name="SELL - Turtle Soup"
        ))
        for idx, row in sells.iterrows():
            x_end = px(gbp_1h.index[-1])
            if pd.notna(row["target_1"]):
                fig.add_trace(go.Scatter(
                    x=[px(idx), x_end], y=[row["target_1"], row["target_1"]],
                    mode="lines", line=dict(color="magenta", width=1, dash="dot"), showlegend=False
                ))
            if pd.notna(row["target_2"]):
                fig.add_trace(go.Scatter(
                    x=[px(idx), x_end], y=[row["target_2"], row["target_2"]],
                    mode="lines", line=dict(color="magenta", width=2, dash="dash"), showlegend=False
                ))

    fig.update_layout(
        title="ICT Month 3 Video 8 - Market Maker Trap | GBPUSD 1H | Oct-Nov 2025 | Daily POI Zones",
        yaxis_title="Price",
        xaxis_title="Date",
        xaxis_type="date",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=860,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    out = "visualize_video8_gbpusd_2025.html"
    fig.write_html(out)
    print("Saved to", out)


if __name__ == "__main__":
    run()
