import pandas as pd
from smartmoneyconcepts.smc import smc, triad_divergence

def run_triad_analysis():
    print("Loading MACRO data (DXY, ZB, ZN)...")
    try:
        dxy = pd.read_csv("tests/test_data/MACRO/DXY_Daily_2016.csv")
        dxy['date'] = pd.to_datetime(dxy['date'])
        dxy.set_index('date', inplace=True)

        zb = pd.read_csv("tests/test_data/MACRO/ZB_Daily_2016.csv")
        zb['date'] = pd.to_datetime(zb['date'])
        zb.set_index('date', inplace=True)

        zn = pd.read_csv("tests/test_data/MACRO/ZN_Daily_2016.csv")
        zn['date'] = pd.to_datetime(zn['date'])
        zn.set_index('date', inplace=True)
        zf = pd.read_csv("tests/test_data/MACRO/ZF_Daily_2016.csv")
        zf['date'] = pd.to_datetime(zf['date'])
        zf.set_index('date', inplace=True)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return

    print("Calculating USDX Swing Highs/Lows...")
    dxy_swings = smc.swing_highs_lows_v4(dxy)
    
    triad = {
        '30Y Bond (ZB)': zb,
        '10Y Note (ZN)': zn,
        '5Y Note (ZF)': zf
    }

    print("Analyzing Triad Divergence...")
    triad_div_df = triad_divergence(dxy, triad, dxy_swings, lookaround_bars=5)

    bullish_divs = triad_div_df[triad_div_df['triad_bullish_div']]
    bearish_divs = triad_div_df[triad_div_df['triad_bearish_div']]

    print("\n" + "="*50)
    print("TRIAD DIVERGENCE ANALYSIS (2016)")
    print("="*50)
    
    print(f"\nBullish Triad Divergences (USDX Lower Lows unconfirmed by Triad): {len(bullish_divs)}")
    for date, row in bullish_divs.iterrows():
        print(f" - {date.date()}: Diverging Assets: {row['triad_diverging_assets']}")

    print(f"\nBearish Triad Divergences (USDX Higher Highs unconfirmed by Triad): {len(bearish_divs)}")
    for date, row in bearish_divs.iterrows():
        print(f" - {date.date()}: Diverging Assets: {row['triad_diverging_assets']}")

if __name__ == "__main__":
    run_triad_analysis()
