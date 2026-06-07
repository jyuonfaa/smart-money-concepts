import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts import smc
import pytz

def run_video8_visualization():
    print("Generating Video 8 Market Protraction Visual Masterpiece...")
    
    # 1. Load data
    csv_path = "tests/test_data/EURUSD/EURUSD_15M.csv"
    df = pd.read_csv(csv_path)
    
    date_col = 'Date' if 'Date' in df.columns else 'date'
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    
    # Run the detector on a rich subset first
    df_all = df.loc['2023-09-01':'2023-10-05'].copy()
    result = smc.market_protraction(df_all, threshold_pips=0.0005)
    
    # 2. Convert index to New York time for clean local clock plotting
    result.index = result.index.tz_localize('UTC').tz_convert('America/New_York')
    
    # Select the perfect focal window for high-resolution visual audit (Sept 18 to Sept 23)
    target_start = pd.Timestamp("2023-09-18 00:00:00").tz_localize('America/New_York')
    target_end = pd.Timestamp("2023-09-23 23:59:59").tz_localize('America/New_York')
    df_plot = result.loc[target_start:target_end].copy()
    
    # 3. Build Plotly Chart
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot['open'],
        high=df_plot['high'],
        low=df_plot['low'],
        close=df_plot['close'],
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350',
        increasing_fillcolor='#26a69a',
        decreasing_fillcolor='#ef5350',
        name='EURUSD 15M'
    ))
    
    # Draw vertical dashed lines for each daily anchor crossing
    unique_dates = sorted(list(set(df_plot.index.date)))
    ny_tz = pytz.timezone('America/New_York')
    
    for D in unique_dates:
        d_str = D.strftime('%Y-%m-%d')
        d_prev = D - pd.Timedelta(days=1)
        d_prev_str = d_prev.strftime('%Y-%m-%d')
        
        # We draw anchor lines for ASIA (8PM NY of prev day), MIDNIGHT (00:00 NY), and NY_OPEN (7AM NY)
        anchors = [
            {'name': 'ASIA', 'dt': pd.Timestamp(f"{d_prev_str} 20:00:00").tz_localize(ny_tz), 'color': '#ab47bc'}, # Purple
            {'name': 'MIDNIGHT', 'dt': pd.Timestamp(f"{d_str} 00:00:00").tz_localize(ny_tz), 'color': '#29b6f6'}, # Blue
            {'name': 'NY_OPEN', 'dt': pd.Timestamp(f"{d_str} 07:00:00").tz_localize(ny_tz), 'color': '#ff9800'}    # Orange
        ]
        
        for anchor in anchors:
            dt = anchor['dt']
            # Only draw if the line is within our plotted viewport
            if target_start <= dt <= target_end:
                fig.add_vline(
                    x=dt,
                    line_width=1.5,
                    line_dash="dash",
                    line_color=anchor['color'],
                    opacity=0.6
                )
                
                # Add a tiny text label at the very top of each line for the user
                fig.add_annotation(
                    x=dt,
                    y=df_plot['high'].max() + 0.0005,
                    text=anchor['name'],
                    showarrow=False,
                    font=dict(color=anchor['color'], size=8),
                    textangle=-90,
                    yshift=10
                )
                
    # Add annotated markers for the detected protractions
    signals = df_plot[df_plot['protraction_dir'] != 0]
    for ts, row in signals.iterrows():
        anchor = row['protraction_anchor']
        direction = "BULLISH" if row['protraction_dir'] == 1 else "BEARISH"
        color = "#ffeb3b" if row['protraction_dir'] == 1 else "#00e5ff" # Gold for Bullish, Cyan for Bearish
        
        if row['protraction_dir'] == 1:
            # Bullish protraction runs up: point to high
            y_val = row['high']
            ay_val = -50
            arrow_side = "bottom"
        else:
            # Bearish protraction runs down: point to low
            y_val = row['low']
            ay_val = 50
            arrow_side = "top"
            
        fig.add_annotation(
            x=ts,
            y=y_val,
            ax=0,
            ay=ay_val,
            text=f"{anchor}<br>{direction}",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor=color,
            bgcolor="rgba(11, 15, 25, 0.95)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
            font=dict(color="white", size=10, family="Outfit, sans-serif"),
            align="center"
        )
        
    # Styling configuration for absolute premium aesthetics
    fig.update_layout(
        title=dict(
            text="ICT VIDEO 8: MARKET PROTRACTION TEMPORAL PROJECTION [EURUSD 15M]",
            font=dict(size=20, color="#ffffff", family="Outfit, sans-serif"),
            x=0.05,
            y=0.95
        ),
        xaxis=dict(
            title=dict(text="Date & Time (New York Local Time)", font=dict(color="#ffffff")),
            tickfont=dict(color="#b0bec5"),
            gridcolor="#263238",
            rangeslider=dict(visible=False),
            type='date'
        ),
        yaxis=dict(
            title=dict(text="Price", font=dict(color="#ffffff")),
            tickfont=dict(color="#b0bec5"),
            gridcolor="#263238",
            tickformat='.5f'
        ),
        plot_bgcolor="#0b0f19",
        paper_bgcolor="#0b0f19",
        margin=dict(l=60, r=40, t=100, b=60),
        height=800,
        showlegend=False
    )
    
    output_html = "ICT_VIDEO_8_MARKET_PROTRACTION.html"
    fig.write_html(output_html)
    print(f"Masterpiece saved successfully to {output_html}")

if __name__ == "__main__":
    run_video8_visualization()
