import pandas as pd
from smartmoneyconcepts.smc import smc, triad_divergence

def run_triad_analysis():
    print("Loading MACRO data (DXY, ZB, ZN, ZF)...")
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

    # ── Build USDX Daily Order Blocks as POI proxy ───────────────────────────
    # ICT taught the Triad is only checked when DXY hits an OB/Liquidity Pool/FVG.
    # smc.ob() requires swing_highs_lows() output (HighLow column format).
    print("Computing USDX Order Blocks (POI gate)...")
    dxy_swings_v1 = smc.swing_highs_lows(dxy, swing_length=5)
    dxy_ob = smc.ob(dxy, dxy_swings_v1)
    usdx_pois = dxy_ob[dxy_ob['OB'].notna()][['Top', 'Bottom']].rename(
        columns={'Top': 'top', 'Bottom': 'bottom'}
    )

    print("\n" + "="*60)
    print("MODE 1: EXPLORATION (No POI gate — all swings, usdx_pois=None)")
    print("="*60)
    div_all = triad_divergence(dxy, triad, dxy_swings, lookaround_bars=5, usdx_pois=None)
    bullish_all = div_all[div_all['triad_bullish_div']]
    bearish_all = div_all[div_all['triad_bearish_div']]
    print(f"Bullish Triad Divergences: {len(bullish_all)}")
    for date, row in bullish_all.iterrows():
        print(f"  - {date.date()}: {row['triad_diverging_assets']}")
    print(f"Bearish Triad Divergences: {len(bearish_all)}")
    for date, row in bearish_all.iterrows():
        print(f"  - {date.date()}: {row['triad_diverging_assets']}")

    print("\n" + "="*60)
    print("MODE 2: POI-GATED (Only swings at USDX Order Blocks — ICT correct method)")
    print("="*60)
    div_poi = triad_divergence(dxy, triad, dxy_swings, lookaround_bars=5, usdx_pois=usdx_pois)
    bullish_poi = div_poi[div_poi['triad_bullish_div']]
    bearish_poi = div_poi[div_poi['triad_bearish_div']]
    print(f"Bullish Triad Divergences at POI: {len(bullish_poi)}")
    for date, row in bullish_poi.iterrows():
        print(f"  - {date.date()}: {row['triad_diverging_assets']}")
    print(f"Bearish Triad Divergences at POI: {len(bearish_poi)}")
    for date, row in bearish_poi.iterrows():
        print(f"  - {date.date()}: {row['triad_diverging_assets']}")

    noise_removed = (len(bullish_all) + len(bearish_all)) - (len(bullish_poi) + len(bearish_poi))
    print(f"\nNoise removed by POI gate: {noise_removed} signals filtered out")

if __name__ == "__main__":
    run_triad_analysis()
