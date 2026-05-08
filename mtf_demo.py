import yfinance as yf
import pandas as pd
from mtf_engine import MTFEngine

print("Downloading Multi-Timeframe Data for EUR/USD...")

# Download data for all timeframes
ohlc_dict = {
    "1mo": yf.download("EURUSD=X", interval="1mo", period="10y", progress=False),
    "1wk": yf.download("EURUSD=X", interval="1wk", period="5y", progress=False),
    "1d":  yf.download("EURUSD=X", interval="1d", period="2y", progress=False),
    "4h":  yf.download("EURUSD=X", interval="4h", period="2mo", progress=False)
}

# Clean up column names from yfinance
for tf, ohlc in ohlc_dict.items():
    if isinstance(ohlc.columns, pd.MultiIndex):
        ohlc.columns = ohlc.columns.get_level_values(0)
    ohlc.columns = [c.lower() for c in ohlc.columns]
    
    # Strip timezone to allow cross-timeframe comparisons
    if ohlc.index.tz is not None:
        ohlc.index = ohlc.index.tz_localize(None)
        
    ohlc_dict[tf] = ohlc[['open', 'high', 'low', 'close', 'volume']]

# Initialize Layer 4
engine = MTFEngine(ohlc_dict)

print("\n--- Layer 4 Level Inheritance Test ---")
print("Simulating live 4H execution engine...\n")

# Get the execution timeframe (4H)
execution_df = ohlc_dict["4h"]

# Let's just look at the last 10 candles of the 4H chart
last_10_candles = execution_df.tail(10)

for current_time, row in last_10_candles.iterrows():
    # Ask Layer 4 for the Higher Timeframe Context
    context = engine.get_htf_context(current_time)
    
    print(f"[{current_time}] 4H Price: {row['close']:.4f}")
    
    # Check what we inherited from the higher timeframes
    if context["inside_1mo_consolidation"]:
        print(f"   -> [Filtered by Monthly] Inside MN Consolidation. EQ: {context['1mo_equilibrium']:.4f}")
        
    if context["inside_1wk_consolidation"]:
        print(f"   -> [Filtered by Weekly] Inside W Consolidation. EQ: {context['1wk_equilibrium']:.4f}")
        
    if context["inside_1d_consolidation"]:
        bias = "PREMIUM (Bearish Bias)" if row['close'] > context['1d_equilibrium'] else "DISCOUNT (Bullish Bias)"
        print(f"   -> [Filtered by Daily] Inside D Consolidation. EQ: {context['1d_equilibrium']:.4f} -> You are in {bias}")
        
    # If not inside any HTF consolidations, we are in an expansion phase!
    if not any([context["inside_1mo_consolidation"], context["inside_1wk_consolidation"], context["inside_1d_consolidation"]]):
        print("   -> [Expansion Phase] Free and clear on all HTFs.")
    print("-" * 60)
