import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc

def annual_opportunity_audit(symbol):
    try:
        # Fetch Data - 1 Year Daily, Max (60d) 15M
        df_1d = yf.download(symbol, period="1y", interval="1d", progress=False)
        df_15m = yf.download(symbol, period="60d", interval="15m", progress=False)
        
        if df_1d.empty or df_15m.empty:
            return None

        def clean(df):
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            return df
        
        df_1d, df_15m = clean(df_1d), clean(df_15m)

        # 1. Identify All Daily OTE Zones for the Year
        d_swings = smc.swing_highs_lows_v4(df_1d)
        year_otes = []
        for i in range(1, len(d_swings)):
            p1, p5 = d_swings.iloc[i-1], d_swings.iloc[i]
            mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
            r = abs(p5['p'] - p1['p'])
            o62 = p5['p'] - 0.62*r if mode == 'BULLISH' else p5['p'] + 0.62*r
            o79 = p5['p'] - 0.79*r if mode == 'BULLISH' else p5['p'] + 0.79*r
            year_otes.append({'62': o62, '79': o79, 'type': mode})

        # 2. Audit 60-Day Surgical Sample
        m15_swings = smc.swing_highs_lows_v4(df_15m)
        setups = []
        zone_cooldowns = {}
        
        for _, row in m15_swings.iterrows():
            for i, ote in enumerate(year_otes):
                if min(ote['62'], ote['79']) <= row['p'] <= max(ote['62'], ote['79']):
                    cooldown_key = (i, row['type'])
                    if cooldown_key in zone_cooldowns:
                        if row['ts'] - zone_cooldowns[cooldown_key] < pd.Timedelta(hours=2):
                            continue
                    setups.append((row['ts'], row['type']))
                    zone_cooldowns[cooldown_key] = row['ts']
                    break

        # 3. Global Alternation (H -> L -> H)
        setups.sort(key=lambda x: x[0])
        final_trades = []
        last_type = None
        for ts, sig_type in setups:
            if sig_type != last_type:
                final_trades.append(sig_type)
                last_type = sig_type

        # 4. Statistics
        days_sampled = (df_15m.index[-1] - df_15m.index[0]).days
        count_60d = len(final_trades)
        annual_projection = int((count_60d / days_sampled) * 365) if days_sampled > 0 else 0
        
        return {
            "symbol": symbol,
            "otes_in_year": len(year_otes),
            "trades_in_60d": count_60d,
            "annual_projection": annual_projection,
            "avg_weekly": round(count_60d / (days_sampled / 7), 1) if days_sampled > 0 else 0
        }

    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

if __name__ == "__main__":
    assets = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GC=F", "BTC-USD"]
    print("\n" + "="*70)
    print("ICT ANNUAL OPPORTUNITY AUDIT: 60-DAY SURGICAL SAMPLE")
    print("="*70)
    print(f"{'ASSET':<10} | {'D1 OTEs':<8} | {'60D TRADES':<12} | {'EST. ANNUAL':<12} | {'WEEKLY'}")
    print("-" * 70)
    
    for asset in assets:
        data = annual_opportunity_audit(asset)
        if data and "error" not in data:
            print(f"{data['symbol']:<10} | {data['otes_in_year']:<8} | {data['trades_in_60d']:<12} | {data['annual_projection']:<12} | {data['avg_weekly']} setups")
    
    print("="*70 + "\n")
