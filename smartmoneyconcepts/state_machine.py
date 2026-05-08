import pandas as pd
import numpy as np
from enum import Enum


class PriceDeliveryState(Enum):
    CONSOLIDATION = "consolidation"
    EXPANSION     = "expansion"
    RETRACEMENT   = "retracement"
    REVERSAL      = "reversal"
    UNKNOWN       = "unknown"


def detect_reversals(ohlc, swing_hl):
    """
    ICT Reversal / Stop Run Detector.
    
    ICT Month 1, Video 1:
      "Reversal is when price moves the opposite direction. The market makers
       have run a level of stops and a significant move should unfold.
       What to look for: the liquidity pools just above an old price high
       and just below an old price low."
    
    Logic:
      BEARISH REVERSAL — wick pierces above a prior swing high, body closes back below.
      BULLISH REVERSAL — wick pierces below a prior swing low, body closes back above.
      Order Block = the last opposing candle before the reversal candle.
    
    Returns DataFrame with columns:
      Reversal:    1.0 (bullish) / -1.0 (bearish) / NaN
      SweptLevel:  the swing high or low that was swept
      OB_Top:      top of the reversal order block
      OB_Bottom:   bottom of the reversal order block
    """
    n = len(ohlc)
    h = ohlc["high"].values
    l = ohlc["low"].values
    c = ohlc["close"].values
    o = ohlc["open"].values
    
    shl_hl = swing_hl["HighLow"].values
    shl_lv = swing_hl["Level"].values
    
    # Collect swing levels with their bar index
    swing_highs = []  # (index, level)
    swing_lows = []   # (index, level)
    for idx in range(n):
        if shl_hl[idx] == 1.0:
            swing_highs.append((idx, shl_lv[idx]))
        elif shl_hl[idx] == -1.0:
            swing_lows.append((idx, shl_lv[idx]))
    
    reversal = np.full(n, np.nan)
    swept_level = np.full(n, np.nan)
    ob_top = np.full(n, np.nan)
    ob_bottom = np.full(n, np.nan)
    
    # Track which swing levels are still "live" (not yet broken by a close).
    # A level is invalidated when any candle's CLOSE exceeds it,
    # making it a one-shot trigger — exactly like real stop orders.
    sh_valid = [True] * len(swing_highs)
    sl_valid = [True] * len(swing_lows)
    
    for i in range(1, n):
        best_signal = None
        
        # --- BEARISH REVERSAL: sweep above a swing high ---
        for k, (sh_idx, sh_level) in enumerate(swing_highs):
            if not sh_valid[k]:
                continue
            if sh_idx >= i:
                continue
            if i - sh_idx > 200:
                continue
            
            # Check if a prior candle already closed above this level
            # (invalidates the level — stops were already taken)
            # We only need to check the previous candle for efficiency,
            # since we invalidate as we go.
            
            # Wick above swing high, body closes below = stop run + rejection
            if h[i] > sh_level and c[i] < sh_level:
                if best_signal is None or sh_idx > best_signal[0]:
                    best_signal = (sh_idx, sh_level, -1.0, k, 'sh')
            
            # If body closes above, invalidate (stops taken, no rejection)
            if c[i] > sh_level:
                sh_valid[k] = False
        
        # --- BULLISH REVERSAL: sweep below a swing low ---
        for k, (sl_idx, sl_level) in enumerate(swing_lows):
            if not sl_valid[k]:
                continue
            if sl_idx >= i:
                continue
            if i - sl_idx > 200:
                continue
            
            # Wick below swing low, body closes above = stop run + rejection
            if l[i] < sl_level and c[i] > sl_level:
                if best_signal is None or sl_idx > best_signal[0]:
                    best_signal = (sl_idx, sl_level, 1.0, k, 'sl')
            
            # If body closes below, invalidate (stops taken, no rejection)
            if c[i] < sl_level:
                sl_valid[k] = False
        
        if best_signal is not None:
            _, level, direction, k_idx, kind = best_signal
            reversal[i] = direction
            swept_level[i] = level
            
            # Invalidate the swept level (consumed)
            if kind == 'sh':
                sh_valid[k_idx] = False
            else:
                sl_valid[k_idx] = False
            
            # Find the Order Block: last opposing candle before reversal candle
            if direction == -1.0:
                # Bearish reversal → OB is the last BULLISH candle before bar i
                for j in range(i - 1, max(0, i - 30), -1):
                    if c[j] > o[j]:
                        ob_top[i] = h[j]
                        ob_bottom[i] = l[j]
                        break
            else:
                # Bullish reversal → OB is the last BEARISH candle before bar i
                for j in range(i - 1, max(0, i - 30), -1):
                    if c[j] < o[j]:
                        ob_top[i] = h[j]
                        ob_bottom[i] = l[j]
                        break
    
    return pd.DataFrame({
        "Reversal": reversal,
        "SweptLevel": swept_level,
        "OB_Top": ob_top,
        "OB_Bottom": ob_bottom,
    }, index=ohlc.index)


class PriceDeliveryStateMachine:
    """
    ICT Price Delivery State Machine (Layer 5).
    
    Tracks: Consolidation -> Expansion -> Retracement -> Reversal
    
    States PERSIST — once assigned, a state holds until a valid transition fires.
    UNKNOWN only exists before the very first consolidation is detected.
    """
    
    def process(
        self,
        ohlc: pd.DataFrame,
        consolidation: pd.DataFrame,
        expansion: pd.DataFrame,
        displacement: pd.DataFrame = None,
        liquidity: pd.DataFrame = None,
        reversals: pd.DataFrame = None,
        htf_context: dict = None,
    ) -> pd.DataFrame:
        """
        Video 3 Institutional Logging Engine.
        Transitioned from a predictive state machine to a passive logging system.
        Logs interactions with Speed (Displacement) and Clean Liquidity (Magnets).
        """
        n = len(ohlc)
        
        # Output columns for Logging
        states = []
        killzones = []
        days_of_week = []
        speed_interactions = np.full(n, np.nan)
        clean_sweeps = np.full(n, np.nan)
        weekly_h_day = [None] * n
        weekly_l_day = [None] * n
        
        # Internal tracking
        current_state = PriceDeliveryState.UNKNOWN
        
        # Localize to New York Time for logging
        try:
            if ohlc.index.tz is None:
                ohlc_ny = ohlc.index.tz_localize("UTC").tz_convert("America/New_York")
            else:
                ohlc_ny = ohlc.index.tz_convert("America/New_York")
        except:
            ohlc_ny = ohlc.index

        days = ohlc_ny.day_name()
        
        # Killzone Logic (STRICT INSTITUTIONAL TIMINGS)
        def get_killzone(timestamp):
            hour = timestamp.hour + timestamp.minute / 60
            if 19 <= hour:          return "Asian"         # 7:00 PM - 12:00 AM
            elif 2 <= hour < 5:     return "London Open"   # 2:00 AM - 5:00 AM
            elif 7 <= hour < 9:     return "NY Open"       # 7:00 AM - 9:00 AM
            elif 10 <= hour < 11:   return "London Close"  # 10:00 AM - 11:00 AM
            else:                   return "Other"

        for i in range(n):
            current_time = ohlc_ny[i]
            kz = get_killzone(current_time)
            killzones.append(kz)
            days_of_week.append(days[i])
            
            row_cons = consolidation.iloc[i]
            row_exp  = expansion.iloc[i]
            is_consolidating = not pd.isna(row_cons["Consolidation"])
            has_expansion    = not pd.isna(row_exp["Expansion"])
            
            # ── Step 1: Update Basic State (Observation Only) ──────────
            if is_consolidating:
                current_state = PriceDeliveryState.CONSOLIDATION
            elif has_expansion:
                current_state = PriceDeliveryState.EXPANSION
            
            # ── Step 2: Log Speed (Displacement) Interactions ──────────
            if displacement is not None:
                if not pd.isna(displacement["Displacement"].iloc[i]):
                    speed_interactions[i] = displacement["Displacement"].iloc[i]
            
            # ── Step 3: Log Clean Liquidity (Magnets) ──────────
            if liquidity is not None:
                if liquidity["IsTooClean"].iloc[i] == 1:
                    clean_sweeps[i] = liquidity["Level"].iloc[i]

            # ── Step 4: Transposed Level Interactions ──────────
            if htf_context and "transposed_levels" in htf_context:
                for level in htf_context["transposed_levels"]:
                    # Log if price interacts with transposed HTF levels
                    if level["type"] == "Clean Liquidity":
                        if l[i] <= level["level"] <= h[i]:
                            # Price is currently "touching" a transposed clean level
                            pass # We will record this in the final log
            
            states.append(current_state.value)

        # ── Step 5: Weekly High/Low Attribution ──────────
        # Find the High and Low of each week and tag their Day/Killzone
        ohlc_copy = ohlc.copy()
        ohlc_copy["kz"] = killzones
        ohlc_copy["day"] = days_of_week
        
        # Group by ISO week
        ohlc_copy["week"] = ohlc_copy.index.isocalendar().week
        for week_id, group in ohlc_copy.groupby("week"):
            if len(group) == 0: continue
            
            w_high_idx = group["high"].idxmax()
            w_low_idx  = group["low"].idxmin()
            
            w_high_day = group.loc[w_high_idx, "day"]
            w_high_kz  = group.loc[w_high_idx, "kz"]
            w_low_day  = group.loc[w_low_idx, "day"]
            w_low_kz   = group.loc[w_low_idx, "kz"]
            
            # Back-fill this week's data with the formation info
            indices = ohlc_copy.index.get_indexer(group.index)
            for idx in indices:
                weekly_h_day[idx] = f"{w_high_day} ({w_high_kz})"
                weekly_l_day[idx] = f"{w_low_day} ({w_low_kz})"

        return pd.DataFrame({
            "State": states,
            "Killzone": killzones,
            "Day": days_of_week,
            "Speed": speed_interactions,
            "CleanLevel": clean_sweeps,
            "WeeklyHigh": weekly_h_day,
            "WeeklyLow": weekly_l_day,
        }, index=ohlc.index)
