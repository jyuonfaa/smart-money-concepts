import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from datetime import datetime

class MTFEngine:
    # Video 3: Strict Lookback Windows
    CONFIG = {
        "1d":  {"window": 365, "unit": "D"}, # 12 Months
        "4h":  {"window": 90,  "unit": "D"}, # 3 Months
        "1h":  {"window": 21,  "unit": "D"}, # 3 Weeks
        "15m": {"window": 4,   "unit": "D"}, # 3-4 Days
    }

    def __init__(self, ohlc_dict):
        self.ohlc_dict = ohlc_dict
        self.results = {}
        
        print("\n--- MTF Engine: Video 3 Institutional Logging ---")
        for tf, ohlc in self.ohlc_dict.items():
            # Validate Lookback (Warning only, as data might be slightly less)
            days_available = (ohlc.index[-1] - ohlc.index[0]).days
            required = self.CONFIG.get(tf, {}).get("window", 0)
            if days_available < required:
                print(f"WARNING: {tf} has only {days_available} days. Video 3 requires {required} days.")

            print(f"Logging {tf} Price Action...")
            
            # 1. Swings
            swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
            
            # 2. Consolidation (Body-based as per smc.py update)
            cons = smc.consolidation(ohlc, prd=10, conslen=5)
            
            # 3. Displacement (Speed - Statistical)
            speed = smc.displacement(ohlc)
            
            # 4. Clean Liquidity (Equal Highs/Lows)
            liq = smc.liquidity(ohlc, swing_hl)
            # 5. Temporal Tagging (Localize to NY Time first)
            ohlc_ny = ohlc.copy()
            try:
                if ohlc_ny.index.tz is None:
                    ohlc_ny.index = ohlc_ny.index.tz_localize("UTC").tz_convert("America/New_York")
                else:
                    ohlc_ny.index = ohlc_ny.index.tz_convert("America/New_York")
            except:
                pass 

            temporal = self._tag_temporal_data(ohlc_ny, swing_hl)
            
            self.results[tf] = {
                "ohlc": ohlc,
                "swing_hl": swing_hl,
                "consolidations": cons,
                "speed": speed,
                "liquidity": liq,
                "temporal": temporal
            }

    def _tag_temporal_data(self, ohlc, swing_hl):
        """Video 3: Note what killzone and day weekly/daily highs/lows form in."""
        temporal = pd.DataFrame(index=ohlc.index)
        temporal["day_of_week"] = ohlc.index.day_name()
        
        # Killzone Detection - canonical single-pass (confirmed timings)
        def get_killzone(timestamp):
            hour = timestamp.hour + timestamp.minute / 60
            if 19 <= hour:          return "Asian"         # 7:00 PM - 12:00 AM
            elif 2 <= hour < 5:     return "London Open"   # 2:00 AM - 5:00 AM
            elif 7 <= hour < 9:     return "NY Open"       # 7:00 AM - 9:00 AM
            elif 10 <= hour < 11:   return "London Close"  # 10:00 AM - 11:00 AM
            else:                   return "Other"

        temporal["killzone"] = ohlc.index.map(get_killzone)
        return temporal

    def get_htf_context(self, current_time):
        """
        Returns the transposed context (Daily -> 4H -> 1H) for execution.
        Includes Speed Zones and Clean Liquidity Magnets.
        """
        context = {
            "transposed_levels": [],
            "htf_state": {}
        }
        
        for tf in ["1d", "4h", "1h"]:
            if tf not in self.results: continue
            
            # Fetch data up to current_time (Anti-Lookahead)
            res = self.results[tf]
            past_idx = res["ohlc"].index <= current_time
            
            if not any(past_idx): continue
            
            # Transpose OHLC and Equilibrium
            latest_bar = res["ohlc"][past_idx].iloc[-1]
            context["htf_state"][tf] = {
                "high": latest_bar["high"],
                "low": latest_bar["low"],
                "equilibrium": (latest_bar["high"] + latest_bar["low"]) / 2
            }

            # Transpose latest Speed Zone
            latest_speed = res["speed"][past_idx].iloc[-1]
            if latest_speed["Displacement"] != 0:
                context["transposed_levels"].append({
                    "type": "Speed Zone",
                    "tf": tf,
                    "direction": latest_speed["Displacement"],
                    "price": latest_bar["close"]
                })

            # Transpose Clean Liquidity
            latest_liq = res["liquidity"][past_idx].iloc[-1]
            if latest_liq["IsTooClean"] == 1:
                context["transposed_levels"].append({
                    "type": "Clean Liquidity",
                    "tf": tf,
                    "level": latest_liq["Level"]
                })
                
        return context
