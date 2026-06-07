"""
verify_month2_video5.py — Quality Gate for Month 2 Video 5
"""

import math
from risk_engine import calc_mitigation_recovery

def assert_approx(val, expected, tol=0.01, msg=""):
    if not math.isclose(val, expected, abs_tol=tol):
        raise ValueError(f"FAIL: {msg}. Expected ~{expected}, got {val}")

def run_checks():
    print("--- Video 5 Verification ---")
    
    # 1. 2% loss followed by 1% risk requires 2.0R to recover
    res1 = calc_mitigation_recovery(0.02, 0.01)
    assert_approx(res1['required_rr'], 2.0, 0.01, "Check 1: mitigation recovery (0.02, 0.01)")
    print("[PASS] Check 1: 2% initial loss at 1% re-entry risk requires 2.0R")
    
    # 2. 3% loss followed by 1% risk requires 3.0R to recover
    res2 = calc_mitigation_recovery(0.03, 0.01)
    assert_approx(res2['required_rr'], 3.0, 0.01, "Check 2: mitigation recovery (0.03, 0.01)")
    print("[PASS] Check 2: 3% initial loss at 1% re-entry risk requires 3.0R")
    
    # 3. 2% loss followed by 2% risk requires 1.0R to recover (doubling down approach, strictly for math verification)
    res3 = calc_mitigation_recovery(0.02, 0.02)
    assert_approx(res3['required_rr'], 1.0, 0.01, "Check 3: mitigation recovery (0.02, 0.02)")
    print("[PASS] Check 3: 2% initial loss at 2% re-entry risk requires 1.0R")

    print("All Video 5 math checks PASSED.")

if __name__ == "__main__":
    run_checks()
