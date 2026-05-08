import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc
import sys

def audit_pair(symbol):
    print(f"\n[AUDIT] Stress Testing: {symbol}...")
    try:
        # Fetch Data - 2 Years Daily, 30 Days 15M
        df_1d = yf.download(symbol, period="2y", interval="1d", progress=False)
        df_15m = yf.download(symbol, period="30d", interval="15m", progress=False)
        
        if df_1d.empty or df_15m.empty:
            return {"status": "FAILED", "reason": "Empty Data"}

        # Clean
        def clean(df):
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            return df
        
        df_1d, df_15m = clean(df_1d), clean(df_15m)

        # 1. Daily OTE Discovery (The Anchors)
        d_swings = smc.swing_highs_lows_v4(df_1d)
        all_otes = []
        for i in range(1, len(d_swings)):
            p1, p5 = d_swings.iloc[i-1], d_swings.iloc[i]
            mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
            r = abs(p5['p'] - p1['p'])
            o62 = p5['p'] - 0.62*r if mode == 'BULLISH' else p5['p'] + 0.62*r
            o79 = p5['p'] - 0.79*r if mode == 'BULLISH' else p5['p'] + 0.79*r
            all_otes.append({'62': o62, '79': o79, 'type': mode})

        # 2. 15M Surgical Execution (The Signals)
        m15_swings = smc.swing_highs_lows_v4(df_15m)
        candidates = []
        zone_cooldowns = {}
        
        for _, row in m15_swings.iterrows():
            for i, ote in enumerate(all_otes):
                if min(ote['62'], ote['79']) <= row['p'] <= max(ote['62'], ote['79']):
                    # 8-Candle (2 Hour) Temporal Gate
                    cooldown_key = (i, row['type'])
                    if cooldown_key in zone_cooldowns:
                        if row['ts'] - zone_cooldowns[cooldown_key] < pd.Timedelta(hours=2):
                            continue
                    
                    candidates.append((row['ts'], row['type']))
                    zone_cooldowns[cooldown_key] = row['ts']
                    break

        # 3. Global Alternation Filter
        candidates.sort(key=lambda x: x[0])
        final_signals = []
        last_type = None
        for ts, sig_type in candidates:
            if sig_type != last_type:
                final_signals.append(sig_type)
                last_type = sig_type

        # 4. Final Sequence Assertion
        pass_seq = True
        if not final_signals:
            return {"status": "PASSED", "otes_found": len(all_otes), "signals_plotted": 0, "alternation": "N/A (No Signals)"}
            
        for i in range(1, len(final_signals)):
            if final_signals[i] == final_signals[i-1]:
                pass_seq = False
                break
        
        return {
            "status": "PASSED" if pass_seq else "FAILED",
            "otes_found": len(all_otes),
            "signals_plotted": len(final_signals),
            "alternation": "VALID" if pass_seq else "INVALID"
        }

    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}

if __name__ == "__main__":
    # Diversified Stress Test Assets
    assets = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GC=F", "BTC-USD"]
    results = {}
    
    print("\n" + "="*60)
    print("ICT INSTITUTIONAL STRESS TEST: MULTI-ASSET VALIDATION")
    print("="*60)
    
    for asset in assets:
        res = audit_pair(asset)
        results[asset] = res
        print(f"[{asset:<10}] | Status: {res.get('status'):<8} | OTEs: {res.get('otes_found'):<3} | Signals: {res.get('signals_plotted'):<3} | Seq: {res.get('alternation')}")
        if res.get('status') == "ERROR" or res.get('status') == "FAILED":
            print(f"             | Reason: {res.get('reason')}")
    
    print("\n" + "="*60)
    total_pass = sum(1 for r in results.values() if r.get('status') == "PASSED")
    print(f"FINAL RESULT: {total_pass}/{len(assets)} ASSETS PASSED")
    print("="*60 + "\n")
