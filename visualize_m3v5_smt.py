import os
import pathlib
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts.smc import smc, _smt_divergence

def main():
    # 1. Load GBPUSD Daily 2016 and invert raw prices
    gbp_path = "tests/test_data/MACRO/GBPUSD_Daily_2016.csv"
    gbp = pd.read_csv(gbp_path)
    gbp_date_col = "date" if "date" in gbp.columns else "Date"
    gbp[gbp_date_col] = pd.to_datetime(gbp[gbp_date_col])
    gbp.set_index(gbp_date_col, inplace=True)

    # Invert the raw CSV: open=1/open, close=1/close, high=1/low, low=1/high
    raw_open = gbp["open"].copy()
    raw_close = gbp["close"].copy()
    raw_high = gbp["high"].copy()
    raw_low = gbp["low"].copy()

    gbp["open"] = 1.0 / raw_open
    gbp["close"] = 1.0 / raw_close
    gbp["high"] = 1.0 / raw_low
    gbp["low"] = 1.0 / raw_high

    # 2. Load DXY Daily 2016
    dxy_path = "tests/test_data/MACRO/DXY_Daily_2016.csv"
    dxy = pd.read_csv(dxy_path)
    dxy_date_col = "date" if "date" in dxy.columns else "Date"
    dxy[dxy_date_col] = pd.to_datetime(dxy[dxy_date_col])
    dxy.set_index(dxy_date_col, inplace=True)

    # 3. Detect swings and compute SMT divergence
    swings = smc.swing_highs_lows_v4(gbp)
    smt_res = _smt_divergence(gbp, dxy, swings, correlation="inverse")

    # 4. Filter events where smt_bias_event is not null
    events = smt_res[smt_res["smt_bias_event"].notna()].copy()

    # Classify event types
    # Trend confirmed: smt_trend_confirmed is True
    # Divergence: divergence flags (bullish/bearish div, asset or benchmark led)
    def classify_event(row):
        bias = row["smt_bias_event"]  # 'BULLISH' or 'BEARISH'
        is_trend = bool(row["smt_trend_confirmed"])
        if is_trend:
            return f"Trend-Confirmed {bias.capitalize()}"
        else:
            return f"{bias.capitalize()} Divergence"

    events["event_category"] = events.apply(classify_event, axis=1)

    # Console print of event count by type
    print("=== SMT Event Counts by Type ===")
    counts = events["event_category"].value_counts()
    for cat, cnt in counts.items():
        print(f"  {cat}: {cnt}")
    print(f"Total SMT Events: {len(events)}")
    print("================================")

    # 5. Build two stacked panels sharing x-axis
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[
            "GBPUSD Daily 2016 (Inverted: open=1/open, close=1/close, high=1/low, low=1/high)",
            "DXY Daily 2016 (US Dollar Index Benchmark)"
        ]
    )

    # Candlestick colors matching visualize_video8.py
    inc_color = "#26a69a"
    dec_color = "#ef5350"

    # Panel 1: GBPUSD
    fig.add_trace(
        go.Candlestick(
            x=gbp.index,
            open=gbp["open"],
            high=gbp["high"],
            low=gbp["low"],
            close=gbp["close"],
            increasing_line_color=inc_color,
            decreasing_line_color=dec_color,
            increasing_fillcolor=inc_color,
            decreasing_fillcolor=dec_color,
            name="GBPUSD Daily",
            showlegend=False
        ),
        row=1,
        col=1
    )

    # Panel 2: DXY
    fig.add_trace(
        go.Candlestick(
            x=dxy.index,
            open=dxy["open"],
            high=dxy["high"],
            low=dxy["low"],
            close=dxy["close"],
            increasing_line_color=inc_color,
            decreasing_line_color=dec_color,
            increasing_fillcolor=inc_color,
            decreasing_fillcolor=dec_color,
            name="DXY Daily",
            showlegend=False
        ),
        row=2,
        col=1
    )

    # Mark events on GBPUSD panel
    # Separate divergence markers vs trend-confirmed markers:
    # 1. Bullish Divergence: Green triangle-up below low
    # 2. Bearish Divergence: Red triangle-down above high
    # 3. Trend-Confirmed Bullish: Cyan diamond below low
    # 4. Trend-Confirmed Bearish: Magenta diamond above high

    bull_divs = events[events["event_category"] == "Bullish Divergence"]
    bear_divs = events[events["event_category"] == "Bearish Divergence"]
    bull_trends = events[events["event_category"] == "Trend-Confirmed Bullish"]
    bear_trends = events[events["event_category"] == "Trend-Confirmed Bearish"]

    if len(bull_divs) > 0:
        fig.add_trace(
            go.Scatter(
                x=bull_divs.index,
                y=[gbp.loc[ts, "low"] for ts in bull_divs.index],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=13, color="#00e676", line=dict(width=1, color="#ffffff")),
                text=["BULL DIV"] * len(bull_divs),
                textposition="bottom center",
                textfont=dict(size=10, color="#00e676"),
                name="Bullish Divergence",
                showlegend=True
            ),
            row=1,
            col=1
        )

    if len(bear_divs) > 0:
        fig.add_trace(
            go.Scatter(
                x=bear_divs.index,
                y=[gbp.loc[ts, "high"] for ts in bear_divs.index],
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=13, color="#ff1744", line=dict(width=1, color="#ffffff")),
                text=["BEAR DIV"] * len(bear_divs),
                textposition="top center",
                textfont=dict(size=10, color="#ff1744"),
                name="Bearish Divergence",
                showlegend=True
            ),
            row=1,
            col=1
        )

    if len(bull_trends) > 0:
        fig.add_trace(
            go.Scatter(
                x=bull_trends.index,
                y=[gbp.loc[ts, "low"] for ts in bull_trends.index],
                mode="markers+text",
                marker=dict(symbol="diamond", size=11, color="#00e5ff", line=dict(width=1, color="#ffffff")),
                text=["TREND UP"] * len(bull_trends),
                textposition="bottom center",
                textfont=dict(size=10, color="#00e5ff"),
                name="Trend-Confirmed Bullish",
                showlegend=True
            ),
            row=1,
            col=1
        )

    if len(bear_trends) > 0:
        fig.add_trace(
            go.Scatter(
                x=bear_trends.index,
                y=[gbp.loc[ts, "high"] for ts in bear_trends.index],
                mode="markers+text",
                marker=dict(symbol="diamond", size=11, color="#e040fb", line=dict(width=1, color="#ffffff")),
                text=["TREND DOWN"] * len(bear_trends),
                textposition="top center",
                textfont=dict(size=10, color="#e040fb"),
                name="Trend-Confirmed Bearish",
                showlegend=True
            ),
            row=1,
            col=1
        )

    fig.update_layout(
        title="ICT Month 3, Video 5 — SMT Divergence Visual Projection (GBPUSD Daily vs DXY Daily 2016)",
        template="plotly_dark",
        height=950,
        margin=dict(l=60, r=60, t=80, b=60),
        xaxis=dict(rangeslider=dict(visible=False)),
        xaxis2=dict(rangeslider=dict(visible=False)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    output_html = os.path.expandvars(r"%USERPROFILE%\m3v5_smt_visual.html")
    fig.write_html(output_html, include_plotlyjs="cdn")
    print(f"Visual HTML saved: {output_html}")

    # Generate screenshot for visual confirmation
    screenshot_path = os.path.expandvars(r"%USERPROFILE%\m3v5_smt_visual.png")
    fig.write_image(screenshot_path, width=1400, height=950, scale=1.5)
    print(f"Screenshot image saved: {screenshot_path}")

if __name__ == "__main__":
    main()
