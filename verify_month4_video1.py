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

    # ── Build USDX POIs (Order Blocks, FVGs, Liquidity) (Gap 4 Fix) ──────────
    print("Computing USDX POIs (OBs, FVGs, Liquidity Pools)...")
    dxy_swings_v1 = smc.swing_highs_lows(dxy, swing_length=5)
    
    # 1. Order Blocks
    dxy_ob = smc.ob(dxy, dxy_swings_v1)
    pois_ob = dxy_ob[dxy_ob['OB'].notna()][['Top', 'Bottom']].rename(
        columns={'Top': 'top', 'Bottom': 'bottom'}
    )
    
    # 2. Fair Value Gaps
    dxy_fvg = smc.fvg(dxy)
    pois_fvg = dxy_fvg[dxy_fvg['FVG'].notna()][['Top', 'Bottom']].rename(
        columns={'Top': 'top', 'Bottom': 'bottom'}
    )
    
    # 3. Liquidity Pools
    dxy_liq = smc.liquidity(dxy, dxy_swings_v1)
    pois_liq = dxy_liq[dxy_liq['Liquidity'].notna()][['Level']].copy()
    pois_liq['top'] = pois_liq['Level']
    pois_liq['bottom'] = pois_liq['Level']
    pois_liq = pois_liq[['top', 'bottom']]
    
    usdx_pois = pd.concat([pois_ob, pois_fvg, pois_liq]).dropna()

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

    print("\n" + "="*60)
    print("MODE 3: CHAINED SMT (Gap 5 Fix) — Triad + Currency-Pair SMT")
    print("="*60)
    try:
        eur = pd.read_csv("tests/test_data/MACRO/EURUSD_Daily_2016.csv")
        eur['date'] = pd.to_datetime(eur['date'])
        eur.set_index('date', inplace=True)

        gbp = pd.read_csv("tests/test_data/MACRO/GBPUSD_Daily_2016.csv")
        gbp['date'] = pd.to_datetime(gbp['date'])
        gbp.set_index('date', inplace=True)
        
        # Calculate standard SMT divergence between EUR and GBP (Positive correlation)
        eur_swings = smc.swing_highs_lows_v4(eur)
        # Using smt_divergence from Month 3 Video 5
        # Since EUR and GBP are positively correlated, GBP is benchmark
        from smartmoneyconcepts.smc import _smt_divergence
        smt_df = _smt_divergence(
            ohlc=eur, 
            benchmark_ohlc=gbp, 
            asset_swings=eur_swings, 
            correlation="positive", 
            lookaround_bars=5
        )
        
        # Cross-reference
        # If DXY makes a Bearish Triad (USDX HH, bonds fail to make LL)
        # We expect EUR/GBP to be making Lower Lows.
        # Wait, if DXY makes a HH, EURUSD makes a LL. Bearish Triad means DXY is likely to reverse down.
        # So EURUSD is hitting a LL, and we look for Bullish SMT between EUR and GBP.
        print("Checking for days where Triad Divergence + Currency SMT overlap (±3 days)...")
        found = False
        for date, row in div_poi.iterrows():
            if row['triad_bullish_div'] or row['triad_bearish_div']:
                start_date = date - pd.Timedelta(days=3)
                end_date = date + pd.Timedelta(days=3)
                mask = (smt_df.index >= start_date) & (smt_df.index <= end_date)
                smt_window = smt_df[mask]
                
                if smt_window['smt_bullish_div'].any() or smt_window['smt_bearish_div'].any():
                    found = True
                    smt_types = []
                    if smt_window['smt_bullish_div'].any(): smt_types.append("Bullish Pair SMT")
                    if smt_window['smt_bearish_div'].any(): smt_types.append("Bearish Pair SMT")
                    
                    triad_type = "Bullish" if row['triad_bullish_div'] else "Bearish"
                    print(f"  - {date.date()}: {triad_type} Triad Div CONFIRMED BY {','.join(smt_types)} (EUR/GBP)")
        
        if not found:
            print("  No overlapping setups found in 2016.")

    except Exception as e:
        print(f"Could not load currency pair data or calculate SMT: {e}")

if __name__ == "__main__":
    run_triad_analysis()
