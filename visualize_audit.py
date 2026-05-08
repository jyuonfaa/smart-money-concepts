import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine
from mtf_engine import MTFEngine
import numpy as np

def generate_verification_plot():
    symbol = "EURUSD=X"
    print("Fetching data for visualization...")
    # Fetch 3 days of data for detail
    ohlc = yf.download(symbol, interval="15m", period="5d", progress=False)
    if isinstance(ohlc.columns, pd.MultiIndex):
        ohlc.columns = ohlc.columns.get_level_values(0)
    ohlc.columns = [c.lower() for c in ohlc.columns]
    
    # Localize to New York
    ohlc.index = ohlc.index.tz_convert("America/New_York")
    
    # Run SMC Logic
    swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
    cons = smc.consolidation(ohlc, prd=10, conslen=5)
    exp = smc.expansion(ohlc, cons)
    disp = smc.displacement(ohlc)
    liq = smc.liquidity(ohlc, swing_hl)
    
    # Plotting
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Filter for the last 2 days (May 5-6) for clarity
    plot_df = ohlc.loc['2026-05-05':'2026-05-06']
    plot_cons = cons.loc['2026-05-05':'2026-05-06']
    plot_disp = disp.loc['2026-05-05':'2026-05-06']
    plot_liq = liq.loc['2026-05-05':'2026-05-06']
    
    # Draw Candlesticks
    for i in range(len(plot_df)):
        row = plot_df.iloc[i]
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        # Wick
        ax.plot([plot_df.index[i], plot_df.index[i]], [row['low'], row['high']], color=color, linewidth=1)
        # Body
        body_bottom = min(row['open'], row['close'])
        body_height = abs(row['open'] - row['close'])
        rect = plt.Rectangle((mdates.date2num(plot_df.index[i]) - 0.005, body_bottom), 0.01, body_height, color=color, alpha=0.8)
        ax.add_patch(rect)
        
        # Highlight Speed (Displacement)
        if not np.isnan(plot_disp['Displacement'].iloc[i]):
            ax.add_patch(plt.Rectangle((mdates.date2num(plot_df.index[i]) - 0.008, row['low']), 0.016, row['high']-row['low'], color='#bb86fc', alpha=0.3))

    # Draw Consolidation Boxes (Body-Based)
    for i in range(len(plot_cons)):
        if not np.isnan(plot_cons['Consolidation'].iloc[i]):
            # Find how long it lasted
            start_idx = plot_cons.index[i]
            top = plot_cons['Top'].iloc[i]
            bottom = plot_cons['Bottom'].iloc[i]
            # Draw box until it changes or ends
            ax.add_patch(plt.Rectangle((mdates.date2num(start_idx), bottom), 0.01, top-bottom, color='#2196f3', alpha=0.05))

    # Draw Clean Liquidity Levels
    for i in range(len(plot_liq)):
        if plot_liq['IsTooClean'].iloc[i] == 1:
            ax.axhline(y=plot_liq['Level'].iloc[i], color='#ffd700', linestyle='--', linewidth=1, alpha=0.6)
            ax.text(plot_df.index[0], plot_liq['Level'].iloc[i], " CLEAN LIQUIDITY ", color='#ffd700', fontsize=8, verticalalignment='bottom')

    # Formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    ax.set_title(f"EUR/USD 15M - ICT Video 3 Verification (New York Time)", color='white', fontsize=14)
    ax.grid(color='#333333', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig("verification_chart.png", dpi=200)
    print("Chart saved as verification_chart.png")

if __name__ == "__main__":
    generate_verification_plot()
