import os
import pathlib
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def main():
    output_path = os.path.expandvars(r"%USERPROFILE%\m3v4_contrarian_visual.html")
    
    configs = [
        {
            "pair": "USDJPY=X",
            "cutoff": "2016-11-01",
            "window_start": "2016-05-01",
            "window_end": "2016-11-01",
            "branch_val": 1.0,
            "branch_name": "bullish",
            "ict_ref": [("Top", 106.28), ("Bottom", 103.26)],
            "price_format": ".4f",
        },
        {
            "pair": "USDCAD=X",
            "cutoff": "2016-11-01",
            "window_start": "2015-12-01",
            "window_end": "2016-11-01",
            "branch_val": 1.0,
            "branch_name": "bullish",
            "ict_ref": [("Top", 1.3807), ("Bottom", 1.3078)],
            "price_format": ".4f",
        },
        {
            "pair": "NZDUSD=X",
            "cutoff": "2016-11-01",
            "window_start": "2016-05-01",
            "window_end": "2016-11-01",
            "branch_val": -1.0,
            "branch_name": "bearish",
            "ict_ref": [("Top", 0.7239), ("Bottom", 0.6983)],
            "price_format": ".4f",
        },
    ]

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.18,
        subplot_titles=[c["pair"] for c in configs]
    )

    console_lines = []

    for idx, cfg in enumerate(configs, start=1):
        pair = cfg["pair"]
        df = yf.download(pair, interval="1mo", auto_adjust=False, start="2014-01-01", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
        
        # Run function through cutoff month only
        df_cut = df[df.index <= cfg["cutoff"]].copy()
        res = smc.monthly_contrarian_range(df_cut)
        
        # Display window
        df_window = df_cut.loc[cfg["window_start"]:cfg["window_end"]].copy()
        res_window = res.loc[cfg["window_start"]:cfg["window_end"]].copy()
        
        # Target branch
        branch_rows = res[res["OB"] == cfg["branch_val"]]
        target_row = branch_rows.iloc[-1]
        ob_dt = target_row.name
        top_val = target_row["Top"]
        btm_val = target_row["Bottom"]
        act_val = target_row["Activated"]
        ob_month_str = ob_dt.strftime("%Y-%m")
        
        console_lines.append(
            f"{pair} | {ob_month_str} | {cfg['branch_name']} | {top_val:{cfg['price_format']}} | {btm_val:{cfg['price_format']}} | {act_val:.1f} | {output_path}"
        )
        
        # Both branches' latest info for panel caption
        bull_rows = res[res["OB"] == 1.0]
        if len(bull_rows) > 0:
            b_l = bull_rows.iloc[-1]
            bull_txt = f"Bullish: Top={b_l['Top']:{cfg['price_format']}}, Bottom={b_l['Bottom']:{cfg['price_format']}}, Activated={b_l['Activated']:.1f}"
        else:
            bull_txt = "Bullish: None"
            
        bear_rows = res[res["OB"] == -1.0]
        if len(bear_rows) > 0:
            br_l = bear_rows.iloc[-1]
            bear_txt = f"Bearish: Top={br_l['Top']:{cfg['price_format']}}, Bottom={br_l['Bottom']:{cfg['price_format']}}, Activated={br_l['Activated']:.1f}"
        else:
            bear_txt = "Bearish: None"
            
        caption_txt = f"Latest status through {cfg['cutoff'][:7]}:  {bull_txt}  |  {bear_txt}"

        # Convert index strings for clear category display
        x_dates = [d.strftime("%Y-%m") for d in df_window.index]
        ob_x_str = ob_dt.strftime("%Y-%m")
        if ob_dt not in df_window.index:
            raise ValueError(f"OB candle month {ob_x_str} for pair {pair} is not in display window ({cfg['window_start']} to {cfg['window_end']})")
        
        # Candlesticks
        fig.add_trace(
            go.Candlestick(
                x=x_dates,
                open=df_window["open"],
                high=df_window["high"],
                low=df_window["low"],
                close=df_window["close"],
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
                increasing_fillcolor="#26a69a",
                decreasing_fillcolor="#ef5350",
                name=f"{pair} Monthly",
                showlegend=False
            ),
            row=idx,
            col=1
        )

        # Label each candlestick with its OPEN price
        for dt_val, row_val in df_window.iterrows():
            d_str = dt_val.strftime("%Y-%m")
            open_p = row_val["open"]
            fig.add_annotation(
                x=d_str,
                y=open_p,
                text=f"O: {open_p:{cfg['price_format']}}",
                showarrow=True,
                arrowhead=1,
                arrowsize=1,
                arrowwidth=1,
                arrowcolor="gray",
                ax=0,
                ay=-25 if row_val["close"] >= open_p else 25,
                font=dict(size=10, color="#eceff1"),
                row=idx,
                col=1
            )

        # Top and Bottom horizontal lines from OB candle to right edge
        # Find index position of ob_dt in window
        x_start_idx = x_dates.index(ob_x_str)
        x_line = x_dates[x_start_idx:]
            
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=[top_val] * len(x_line),
                mode="lines",
                line=dict(color="#29b6f6", width=2),
                name="Top",
                showlegend=False
            ),
            row=idx,
            col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=[btm_val] * len(x_line),
                mode="lines",
                line=dict(color="#ab47bc", width=2),
                name="Bottom",
                showlegend=False
            ),
            row=idx,
            col=1
        )

        # Text "Activated = <value>" next to the OB candle
        ob_high = df_window.loc[ob_dt, "high"]
        fig.add_annotation(
            x=ob_x_str,
            y=ob_high,
            text=f"Activated = {act_val:.1f}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="#ffeb3b",
            ax=0,
            ay=-40,
            font=dict(size=11, color="#ffeb3b", family="Arial Black"),
            bgcolor="rgba(33, 33, 33, 0.8)",
            bordercolor="#ffeb3b",
            borderwidth=1,
            row=idx,
            col=1
        )

        # In the "ICT Ref" margin slot, at each level, draw two labels:
        # the function's value in the line's color ("Top 106.2950" / "Bottom 103.3070"), anchored just ABOVE that level's y,
        # and the ICT label in orange, anchored just BELOW the ICT level's y.
        x_ict_slot = "ICT Ref"

        # Function Top & Bottom labels in the margin slot above each line's y
        fig.add_annotation(
            x=x_ict_slot,
            y=top_val,
            text=f"Top {top_val:{cfg['price_format']}}",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=11, color="#29b6f6"),
            row=idx,
            col=1
        )
        fig.add_annotation(
            x=x_ict_slot,
            y=btm_val,
            text=f"Bottom {btm_val:{cfg['price_format']}}",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=11, color="#ab47bc"),
            row=idx,
            col=1
        )

        # ICT reference markers and labels below the ICT level's y
        for lvl_name, r_val in cfg["ict_ref"]:
            ict_str = f"ICT {r_val}"
            # Small marker
            fig.add_trace(
                go.Scatter(
                    x=[x_ict_slot],
                    y=[r_val],
                    mode="markers",
                    marker=dict(symbol="triangle-left", size=8, color="#ff9800"),
                    name="ICT Ref",
                    showlegend=False
                ),
                row=idx,
                col=1
            )
            # Label anchored just BELOW the ICT level's y
            fig.add_annotation(
                x=x_ict_slot,
                y=r_val,
                text=ict_str,
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font=dict(size=11, color="#ff9800"),
                row=idx,
                col=1
            )

        # One text line under the panel directly under x-axis labels
        fig.add_annotation(
            xref=f"x{idx if idx > 1 else ''} domain",
            yref=f"y{idx if idx > 1 else ''} domain",
            x=0.0,
            y=-0.22,
            text=caption_txt,
            showarrow=False,
            xanchor="left",
            yanchor="top",
            font=dict(size=11, color="#90a4ae"),
            row=idx,
            col=1
        )

    fig.update_layout(
        title="ICT Month 3, Video 4 — Monthly Contrarian Range Visual Audit",
        template="plotly_dark",
        height=1600,
        margin=dict(l=60, r=220, t=80, b=100),
        xaxis=dict(rangeslider=dict(visible=False), type="category"),
        xaxis2=dict(rangeslider=dict(visible=False), type="category"),
        xaxis3=dict(rangeslider=dict(visible=False), type="category")
    )

    fig.write_html(output_path, include_plotlyjs="cdn")

    for line in console_lines:
        print(line)

if __name__ == "__main__":
    main()
