"""
verify_month2_video4.py — Quality Gate for Month 2 Video 4
"""

import math
from risk_engine import min_rr_for_win_rate, calc_expectancy, calc_position_size

def assert_approx(val, expected, tol=0.01, msg=""):
    if not math.isclose(val, expected, abs_tol=tol):
        raise ValueError(f"FAIL: {msg}. Expected ~{expected}, got {val}")

def run_checks():
    print("--- Video 4 Verification ---")
    
    # 1. min_rr_for_win_rate(0.75) returns approximately 0.333 (±0.01)
    res1 = min_rr_for_win_rate(0.75)
    assert_approx(res1, 0.333, 0.01, "Check 1: min_rr(0.75)")
    print("[PASS] Check 1: min_rr_for_win_rate(0.75) ~ 0.333")
    
    # 2. min_rr_for_win_rate(0.25) returns approximately 3.0 (±0.01)
    res2 = min_rr_for_win_rate(0.25)
    assert_approx(res2, 3.0, 0.01, "Check 2: min_rr(0.25)")
    print("[PASS] Check 2: min_rr_for_win_rate(0.25) ~ 3.0")
    
    # 3. calc_expectancy(0.30, 0.02, 5.0, 5000, 10) returns net_profit=800 and monthly_pct=16.0 (±0.1)
    res3 = calc_expectancy(0.30, 0.02, 5.0, 5000.0, 10)
    assert_approx(res3['net_profit'], 800.0, 0.1, "Check 3: net_profit")
    assert_approx(res3['monthly_pct'], 16.0, 0.1, "Check 3: monthly_pct")
    print("[PASS] Check 3: calc_expectancy Scenario 2 -> $800, 16%")
    
    # 4. calc_expectancy(0.50, 0.01, 5.0, 5000, 10) returns net_profit=1000 and monthly_pct=20.0 (±0.1)
    res4 = calc_expectancy(0.50, 0.01, 5.0, 5000.0, 10)
    assert_approx(res4['net_profit'], 1000.0, 0.1, "Check 4: net_profit")
    assert_approx(res4['monthly_pct'], 20.0, 0.1, "Check 4: monthly_pct")
    print("[PASS] Check 4: calc_expectancy Scenario 5 -> $1000, 20%")
    
    # 5. calc_position_size(5000, 0.01, 20) returns 2.5 (±0.01)
    res5 = calc_position_size(5000.0, 0.01, 20)
    assert_approx(res5, 2.5, 0.01, "Check 5: calc_position_size")
    print("[PASS] Check 5: calc_position_size(5000, 0.01, 20) ~ $2.50")
    
    print("All Video 4 math checks PASSED.")

if __name__ == "__main__":
    run_checks()
