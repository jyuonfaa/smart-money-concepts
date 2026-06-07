"""
risk_engine.py — ICT Month 2, Video 1: Capital Management Layer (Layer 6)

Implements the three ICT rules from "Growing Small Accounts Without High Risk":
  - Stop = midpoint of the OB candle BODY (open to close), verbatim from page 61
  - R multiples 1-5 stacked above/below entry
  - R:R filter gate — signals below min_rr are suppressed before output

One Function, One Job. No visualization. No state. Pure calculation.
"""

# ─── Constants (verbatim from ICT Month 2 Video 1 slides) ───────────────────

# IDEAL standard (B.3 from page 53 slide):
# "Identify Trade Setups that permit three Reward multiples to one Risk or higher"
RR_MIN        = 3.0
RISK_PCT_MAX  = 0.02   # "no more than two percent on average"
MONTHLY_TARGET = 0.06  # "6% per month" target

# MINIMUM VIABLE FLOOR (page 57 slide 2 — "What Should You Focus On Initially?"):
# "It only takes 20 pips per week / It only requires 1.5% risk / It only requires 1:1 Ratio"
# "Account: $1,000 USD — Risk per trade: 1.5% = $15.00 USD"
# "Risk 20 pips from entry price. Profit taken at 20 pips for a 1.5% return."
# → 6% Per Month via Compounding
RISK_PCT_DEFAULT = 0.015   # 1.5% — the working default for beginners (NOT the 2% max)
PIPS_PER_WEEK    = 20      # 20 pip minimum weekly target
RR_MIN_VIABLE    = 1.0     # 1:1 — viable floor when compounding is applied

# PARTIAL EXIT SCHEDULE (page 61 text + page 62 annotated chart):
# "we can reduce our risk or take a partial (three quarters of one percent)"  — at R1
# "After the second multiple is reached, your stop needs to be at breakeven." — after R2
# "we can take a quarter of it off, we could even take a half of it off"      — at R3
# "It ultimately gets to multiple of 5 and clears the buy stops"              — at R5
EXIT_SCHEDULE = {
    1: {"action": "partial",  "close_fraction": 0.75, "note": "Take 3/4 of risk% off — 0.75% banked"},
    2: {"action": "be_stop",  "close_fraction": 0.00, "note": "Hold — stop moves to breakeven at R2"},
    3: {"action": "partial",  "close_fraction": 0.25, "note": "Take 1/4 to 1/2 off — clears Point 4 buy stops"},
    4: {"action": "be_trail", "close_fraction": 0.00, "note": "Trail stop only — close to buy stops at Pts 1&2"},
    5: {"action": "close",    "close_fraction": 1.00, "note": "Full close — buy stops at Points 1&2 cleared"},
}

# VIDEO 3 PARTIAL EXIT SCHEDULE (verbatim, page 72):
# "take half of that position off as we get 3:1"
# "bank a 1% times 3R so we can make 3% on this one trade"
# "still leave the second portion of the trade on aiming for the liquidity pools"
EXIT_SCHEDULE_V3 = {
    3:  {"action": "partial", "close_fraction": 0.50,
         "note": "Take 50% off at 3R — 3% locked on 2% risk account"},
    9:  {"action": "partial", "close_fraction": 0.25,
         "note": "Take 25% off at 9R — 15M pool reached"},
    15: {"action": "close",   "close_fraction": 1.00,
         "note": "Full close at 15R — 1H pool cleared"},
}
BREAKEVEN_TRIGGER_R = 2  # After R2 fills, stop moves to entry price

# Month 2 Video 5 Constants
MITIGATION_REENTRY_RISK_FRACTION = 0.5
MITIGATION_EXIT_R = 2

# MINIMUM SWING SIZE (page 58 + page 57 slide 2):
# "off a daily chart that you are going to get a 20 pip or more price swing"
# "Risk 20 pips from entry price" — stop distance must be at least 20 pips
MIN_SWING_PIPS = 20
PIP_SIZE       = 0.0001  # standard 4-decimal FX pip


def get_exit_schedule() -> dict:
    """
    ICT Month 2, Video 1: Partial Exit Schedule (pages 61–62).

    Returns the verbatim exit instructions keyed by R multiple (1–5).
    Each entry defines what fraction of the position to close at that R level
    and any stop management action required.

    Usage example:
        r_levels = calc_r_multiples(entry, stop)
        schedule = get_exit_schedule()
        for r, price in enumerate(r_levels, start=1):
            print(f"At R{r} ({price:.5f}): {schedule[r]['note']}")
    """
    return EXIT_SCHEDULE


def calc_ob_stop(ob_bar: dict) -> float:
    """
    ICT stop rule — verbatim from Month 2 Video 1, page 61:
    'your stop... puts your stop far below the middle of that down candle'
    'we don't want to see price go down below the midpoint of that down candle (the bullish order block)'

    Stop level = midpoint of the OB candle BODY (open to close).
    NOT the wick. NOT Top/Bottom from smc.ob().

    Parameters
    ----------
    ob_bar : dict or Series with keys 'open', 'close'

    Returns
    -------
    float : stop price level
    """
    return (ob_bar['open'] + ob_bar['close']) / 2.0


def calc_r_multiples(entry: float, stop: float, max_r: int = 5, bullish: bool = True) -> list:
    """
    Calculate R-multiple profit target levels.

    ICT Month 2 Video 1, page 62 annotated chart:
      R Multiple = 1, 2, 3, 4, 5  stacked above (bullish) or below (bearish) entry.
    At R Multiple = 4: stop moves to breakeven.
    At R Multiple = 5: full exit, buy stops cleared.

    IMPORTANT — direction must be passed explicitly via `bullish`.
    Do NOT infer direction from stop < entry: bearish OB candles are sometimes down
    candles whose body midpoint sits below their open, making stop < entry even for
    a SHORT signal — which inverted all SHORT R-levels to point upward.

    Parameters
    ----------
    entry   : float — entry price (bar.open of OB candle)
    stop    : float — stop level (OB body midpoint)
    max_r   : int   — number of R levels to return (default 5)
    bullish : bool  — True = targets above entry, False = targets below entry

    Returns
    -------
    list of floats : [R1_price, R2_price, ..., R5_price]
                     above entry if bullish=True, below entry if bullish=False
    """
    risk = abs(entry - stop)
    if risk == 0:
        return [entry] * max_r

    direction = 1 if bullish else -1
    return [entry + direction * risk * r for r in range(1, max_r + 1)]


def calc_rr(entry: float, stop: float, target: float) -> float:
    """
    Calculate raw reward-to-risk ratio for a given target.

    Parameters
    ----------
    entry  : float
    stop   : float
    target : float

    Returns
    -------
    float : R:R ratio (always positive)
    """
    risk   = abs(entry - stop)
    reward = abs(target - entry)
    if risk == 0:
        return 0.0
    return reward / risk


def filter_rr(signals_df, entry_col: str, stop_col: str, target_col: str,
              min_rr: float = RR_MIN, min_swing_pips: float = MIN_SWING_PIPS):
    """
    Gate signal output by minimum R:R ratio AND minimum swing size.

    ICT Month 2 Video 1:
      - "Identify Trade Setups that permit three Reward multiples to one Risk or higher."
      - "off a daily chart that you are going to get a 20 pip or more price swing"
      - "Risk 20 pips from entry price."

    Parameters
    ----------
    signals_df      : pd.DataFrame — must contain entry_col, stop_col, target_col
    entry_col       : str   — column name for entry price
    stop_col        : str   — column name for stop price
    target_col      : str   — column name for nearest profit target
    min_rr          : float — minimum R:R to pass filter (default 3.0)
    min_swing_pips  : float — minimum stop distance in pips (default 20)

    Returns
    -------
    pd.DataFrame : filtered copy with only signals meeting both min_rr and min_swing_pips
    """
    df = signals_df.copy()
    df['_rr']    = df.apply(
        lambda row: calc_rr(row[entry_col], row[stop_col], row[target_col]),
        axis=1
    )
    df['_swing_pips'] = df.apply(
        lambda row: abs(row[entry_col] - row[stop_col]) / PIP_SIZE,
        axis=1
    )
    passed = df[
        (df['_rr'] >= min_rr) & (df['_swing_pips'] >= min_swing_pips)
    ].drop(columns=['_rr', '_swing_pips'])
    return passed


def min_rr_for_win_rate(win_rate: float) -> float:
    """
    Returns the minimum R:R ratio required to be net profitable
    at a given win rate.
    Formula: min_rr = (1 - win_rate) / win_rate
    Example: win_rate=0.33 -> min_rr = 2.03
    """
    if win_rate <= 0 or win_rate >= 1:
        raise ValueError("win_rate must be strictly between 0 and 1")
    return (1.0 - win_rate) / win_rate


def calc_expectancy(
    accuracy: float,
    risk_pct: float,
    rr_ratio: float,
    account: float,
    n_trades: int = 10
) -> dict:
    """
    Computes the ICT Video 4 expectancy model.
    Returns: {
        'wins': int,
        'losses': int,
        'avg_win_usd': float,
        'avg_loss_usd': float,
        'subtotal_wins': float,
        'subtotal_losses': float,
        'net_profit': float,
        'monthly_pct': float
    }
    Derived from pages 78-81 of ICT Mentorship notes exactly.
    """
    wins = int(accuracy * n_trades)
    losses = n_trades - wins
    
    avg_loss_usd = account * risk_pct
    avg_win_usd = avg_loss_usd * rr_ratio
    
    subtotal_wins = wins * avg_win_usd
    subtotal_losses = losses * avg_loss_usd
    net_profit = subtotal_wins - subtotal_losses
    
    monthly_pct = round((net_profit / account) * 100.0, 2)
    
    return {
        'wins': wins,
        'losses': losses,
        'avg_win_usd': avg_win_usd,
        'avg_loss_usd': avg_loss_usd,
        'subtotal_wins': subtotal_wins,
        'subtotal_losses': subtotal_losses,
        'net_profit': net_profit,
        'monthly_pct': monthly_pct
    }


def calc_position_size(
    account: float,
    risk_pct: float,
    stop_pips: int
) -> float:
    """
    Returns dollar-per-pip position size.
    Formula: (account * risk_pct) / stop_pips
    Example: account=5000, risk_pct=0.01, stop_pips=20 -> $2.50/pip
    """
    if stop_pips <= 0:
        raise ValueError("stop_pips must be greater than 0")
    return (account * risk_pct) / float(stop_pips)


def calc_mitigation_recovery(initial_risk_pct: float, reentry_risk_pct: float) -> dict:
    """
    Computes the R-multiple required on a re-entry trade to fully mitigate an initial loss.
    Based on ICT Month 2 Video 5.
    
    Parameters
    ----------
    initial_risk_pct : float
        Risk percentage of the initial losing trade (e.g. 0.02 for 2%)
    reentry_risk_pct : float
        Risk percentage of the re-entry trade (e.g. 0.01 for 1%)
        
    Returns
    -------
    dict
        'initial_loss_pct': initial risk taken
        'reentry_risk_pct': risk taken on re-entry
        'required_rr': R-multiple required to breakeven
    """
    if reentry_risk_pct <= 0:
        raise ValueError("reentry_risk_pct must be strictly greater than 0")
        
    required_rr = initial_risk_pct / reentry_risk_pct
    
    return {
        'initial_loss_pct': initial_risk_pct,
        'reentry_risk_pct': reentry_risk_pct,
        'required_rr': required_rr
    }
