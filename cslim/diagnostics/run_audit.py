"""
Comprehensive programmatic audit of all 24 functions and all month 2/3 verify scripts.
"""
import os
import subprocess
import re
import pandas as pd

# PART A Functions list to check
functions = [
    ("ob", ["ob", "_ob"]),
    ("liquidity", ["liquidity", "_liquidity"]),
    ("sessions", ["sessions", "_sessions"]),
    ("consolidation", ["consolidation", "_consolidation"]),
    ("expansion", ["expansion", "_expansion"]),
    ("displacement", ["displacement", "_displacement"]),
    ("swing_highs_lows_v4", ["swing_highs_lows_v4", "_swing_highs_lows_v4"]),
    ("identify_order_block", ["identify_order_block", "_identify_order_block"]),
    ("market_protraction", ["market_protraction", "_market_protraction"]),
    ("breaker_blocks", ["breaker_blocks", "_breaker_blocks"]),
    ("macro_swing_grading", ["macro_swing_grading", "_macro_swing_grading"]),
    ("smt_divergence", ["smt_divergence", "_smt_divergence"]),
    ("smt_apply_bias_filter", ["smt_apply_bias_filter", "_smt_apply_bias_filter"]),
    ("false_hns_patterns / _find_head_and_shoulders", ["_find_head_and_shoulders", "false_hns_patterns", "_false_hns_patterns"]),
    ("_hns_signals", ["_hns_signals"]),
    ("_filter_quarterly_swings", ["_filter_quarterly_swings"]),
    ("_macro_bond_bias", ["_macro_bond_bias"]),
    ("_macro_pair_bias", ["_macro_pair_bias"]),
    ("_macro_ob_alignment", ["_macro_ob_alignment"]),
    ("_trendline_phantoms", ["_trendline_phantoms"]),
    ("_phantom_signals", ["_phantom_signals"]),
    ("previous_high_low", ["previous_high_low", "_previous_high_low"]),
    ("retracements", ["retracements", "_retracements"]),
    ("sequence_void / void_scanner", ["sequence_void", "void_scanner", "_sequence_void", "_void_scanner"])
]

# Load smc.py content to check presence of definitions
smc_path = "smartmoneyconcepts/smc.py"
smc_content = ""
if os.path.exists(smc_path):
    with open(smc_path, "r", encoding="utf-8") as f:
        smc_content = f.read()

print("PART A: FUNCTION SWEEP RESULTS")
print(f"{'Function Target':<45} | {'Status/Location':<50} | {'Def Match'}")
print("-" * 110)

for display_name, search_names in functions:
    found_in_smc = False
    found_in_other = []
    
    # Check smc.py first
    for name in search_names:
        # Check standard def or assignment like smc.name = ...
        if re.search(rf"\bdef\s+{name}\b", smc_content) or re.search(rf"\bsmc\.{name}\s*=", smc_content):
            found_in_smc = True
            matched_name = name
            break
            
    # Check all other py files in workspace
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root or "smartmoneyconcepts.egg-info" in root:
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            # Skip core files if we are looking for orphans
            if path == os.path.join(".", "smartmoneyconcepts", "smc.py"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                for name in search_names:
                    if re.search(rf"\bdef\s+{name}\b", content):
                        found_in_other.append(path.replace(".\\", ""))
            except Exception:
                pass
                
    if found_in_smc:
        location = "FOUND IN smc.py"
        match_info = f"Matches '{matched_name}'"
    elif found_in_other:
        location = f"FOUND ONLY IN ORPHAN FILE ({', '.join(found_in_other[:2])})"
        match_info = "Defined in orphan file"
    else:
        location = "NOT FOUND ANYWHERE"
        match_info = "No definition"
        
    print(f"{display_name:<45} | {location:<50} | {match_info}")

print("\n" + "="*80 + "\n")

# PART B: Verify Scripts Execution
print("PART B: VERIFY SCRIPTS STATUS")
print(f"{'Script Name':<30} | {'Status':<15} | {'Console Output / Error'}")
print("-" * 110)

verify_scripts = []
for m in [2, 3]:
    for v in range(1, 9):
        verify_scripts.append(f"verify_month{m}_video{v}.py")

for script in verify_scripts:
    if not os.path.exists(script):
        # Check if audit_ variant exists for month3 video1
        if script == "verify_month3_video1.py" and os.path.exists("audit_month3_video1.py"):
            script_to_run = "audit_month3_video1.py"
        else:
            print(f"{script:<30} | {'FILE NOT FOUND':<15} | N/A")
            continue
    else:
        script_to_run = script
        
    # Run the script and capture status
    try:
        res = subprocess.run(["python", script_to_run], capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            status = "PASS"
            # Get last line or summary
            lines = [l.strip() for l in res.stdout.split("\n") if l.strip()]
            summary = lines[-1] if lines else "Ran successfully"
            print(f"{script_to_run:<30} | {status:<15} | {summary}")
        else:
            status = "FAIL"
            # Get last error line
            err_lines = [l.strip() for l in res.stderr.split("\n") if l.strip()]
            err_msg = err_lines[-1] if err_lines else "Exited with non-zero code"
            print(f"{script_to_run:<30} | {status:<15} | {err_msg}")
    except subprocess.TimeoutExpired:
        print(f"{script_to_run:<30} | {'TIMEOUT':<15} | Script execution took too long")
    except Exception as e:
        print(f"{script_to_run:<30} | {'ERROR':<15} | {str(e)}")
