"""
ICT Video 4: GLOBAL INSTITUTIONAL COMPARISON
1-Year Audit across all Major Assets (1H Signals)
"""
import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc

def run_global_audit():
    symbols = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "NZDUSD=X", "USDCAD=X", "GC=F"]
    results = []

    print(f"Generating Global Institutional Audit for {len(symbols)} assets...")

    def clean_tz(df):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    for symbol in symbols:
        try:
            df_1d = yf.download(symbol, period="2y", interval="1d", progress=False)
            df_1h = yf.download(symbol, period="1y", interval="1h", progress=False)
            df_1d, df_1h = clean_tz(df_1d), clean_tz(df_1h)

            d_swings = smc.swing_highs_lows_v4(df_1d)
            h1_swings = smc.swing_highs_lows_v4(df_1h)

            total_sig = len(h1_swings)
            ote_match, kz_match, triple_match = 0, 0, 0

            for _, sig in h1_swings.iterrows():
                hr = sig['ts'].hour
                is_kz = (2 <= hr <= 5) or (8 <= hr <= 11)
                if is_kz: kz_match += 1
                
                past = d_swings[d_swings['ts'] < sig['ts']]
                if len(past) >= 2:
                    p1, p5 = past.iloc[-2], past.iloc[-1]
                    mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
                    r = abs(float(p5['p']) - float(p1['p']))
                    o62, o79 = (float(p5['p'])-0.62*r, float(p5['p'])-0.79*r) if mode=='BULLISH' else (float(p5['p'])+0.62*r, float(p5['p'])+0.79*r)
                    uz, lz = max(o62, o79), min(o62, o79)
                    if lz <= float(sig['p']) <= uz:
                        ote_match += 1
                        if is_kz: triple_match += 1

            results.append({
                'Symbol': symbol.replace("=X", "").replace("GC=F", "GOLD"),
                'Total_1H': total_sig,
                'OTE_Match': f"{ote_match} ({ote_match/total_sig*100:.1f}%)",
                'Triple_Match': triple_match,
                'Setups_Per_Month': round(triple_match/12, 1)
            })
            print(f"[OK] {symbol}")
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

    df_res = pd.DataFrame(results)
    print("\n" + "="*70)
    print("           GLOBAL INSTITUTIONAL COMPARISON (1-YEAR)")
    print("="*70)
    print(df_res.to_string(index=False))
    print("="*70)
    print(f"\nTOTAL OPPORTUNITIES (1H) PER MONTH: {df_res['Triple_Match'].sum()/12:.1f}")
    print(f"ESTIMATED 15M OPPORTUNITIES PER MONTH: {df_res['Triple_Match'].sum()/12 * 4:.1f}")

if __name__ == "__main__":
    run_global_audit()
