import pandas as pd
import numpy as np
import plotly.graph_objects as go
from smartmoneyconcepts import smc
import os
import sys

out_dir = r"C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3\scratch"
os.makedirs(out_dir, exist_ok=True)

print("=" * 70)
print("VISUAL AUDIT: MONTH 4 VIDEO 4 -- MITIGATION BLOCK")
print("=" * 70)

print("\n[1] Loading AUDUSD 2016 Daily data...")
PATH = "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv"
df_raw = pd.read_csv(PATH, sep=";", names=["date", "open", "high", "low", "close", "volume"], index_col=False)
df_raw["date"] = pd.to_datetime(df_raw["date"], format="%Y%m%d %H%M%S")
df_raw.set_index("date", inplace=True)
df_daily = df_raw.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()

print("\n[2] Running detectors and checking indices...")
swings_daily = smc.swing_highs_lows(df_daily, swing_length=5)
fvg_daily = smc.fvg(df_daily)

print(f"   swing_highs_lows.index type: {type(swings_daily.index)}")
print(f"   fvg_df.index type:           {type(fvg_daily.index)}")

# Patch FVG index for the detector
if isinstance(fvg_daily.index, pd.RangeIndex):
    fvg_daily.index = df_daily.index

mb_daily = smc._mitigation_blocks(df_daily, swings_daily, fvg_daily)
print(f"   mb_daily.index type:         {type(mb_daily.index)}")
print(f"   Matches ohlc index?:         {mb_daily.index.equals(df_daily.index)}")

active = mb_daily[mb_daily["MB"] == 1.0]

def create_plot(df, active_df, title, x_start=None, x_end=None):
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Price')])
    
    shapes = []
    annotations = []
    
    for i, (ts, row) in enumerate(active_df.iterrows()):
        # Find global block number by matching timestamps
        idx_num = list(active.index).index(ts) + 1 if ts in active.index else i + 1
        start_date = ts
        
        if pd.isna(row["Invalidated"]):
            # Live block
            ts_idx = df.index.get_loc(ts)
            end_idx = min(ts_idx + 30, len(df)-1)
            end_date = df.index[end_idx]
            color = "rgba(0, 255, 0, 0.3)" # Green
            line_color = "green"
            status = "Live"
        else:
            # Invalidated
            inv_idx = int(row["Invalidated"])
            end_date = df.index[inv_idx]
            color = "rgba(255, 0, 0, 0.3)" # Red
            line_color = "red"
            status = "Invalidated"
            
        sd_str = str(start_date)
        ed_str = str(end_date)
        
        # ABody (Rectangle)
        shapes.append(dict(
            type="rect", x0=sd_str, y0=row["ABodyBottom"], x1=ed_str, y1=row["ABodyTop"],
            fillcolor=color, line=dict(width=0), layer="below"
        ))
        
        # AWickHigh (Stop Level)
        shapes.append(dict(
            type="line", x0=sd_str, y0=row["AWickHigh"], x1=ed_str, y1=row["AWickHigh"],
            line=dict(color=line_color, width=2, dash="dot")
        ))
        
        # FVG Target
        if not pd.isna(row["FVGTarget"]):
            shapes.append(dict(
                type="line", x0=sd_str, y0=row["FVGTarget"], x1=ed_str, y1=row["FVGTarget"],
                line=dict(color="blue", width=2, dash="dash")
            ))
            
        annotations.append(dict(
            x=sd_str, y=row["AWickHigh"],
            text=f"MB #{idx_num} ({status})", showarrow=True, arrowhead=1, ax=0, ay=-40
        ))
        
    fig.update_layout(shapes=shapes, annotations=annotations, title=title, xaxis_rangeslider_visible=False)
    if x_start and x_end:
        fig.update_xaxes(range=[str(x_start), str(x_end)])
        
    return fig

print("\n[3] Generating charts...")
try:
    # Block 2 (Clean)
    b2_ts = active.index[1]
    b2_start = df_daily.index[max(0, df_daily.index.get_loc(b2_ts) - 15)]
    b2_end = df_daily.index[min(len(df_daily)-1, df_daily.index.get_loc(b2_ts) + 40)]
    fig_b2 = create_plot(df_daily, active.iloc[[1]], "Block #2 (Clean Baseline)", b2_start, b2_end)
    fig_b2.write_image(os.path.join(out_dir, "mb_block2.png"), width=1200, height=800)
    print("   -> Saved Block #2 PNG")
    
    # Block 3 (Doji)
    b3_ts = active.index[2]
    b3_start = df_daily.index[max(0, df_daily.index.get_loc(b3_ts) - 15)]
    b3_end = df_daily.index[min(len(df_daily)-1, df_daily.index.get_loc(b3_ts) + 40)]
    fig_b3 = create_plot(df_daily, active.iloc[[2]], "Block #3 (Near-Doji)", b3_start, b3_end)
    fig_b3.write_image(os.path.join(out_dir, "mb_block3.png"), width=1200, height=800)
    print("   -> Saved Block #3 PNG")

except Exception as e:
    print(f"   !! Failed to generate PNGs. Error: {e}")
