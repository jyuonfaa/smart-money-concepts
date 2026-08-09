"""
Run detailed audit for PARTS C, D, E.
"""
import os
import subprocess
import re

print("====================================================================")
print("PART C: EXPANDED SEARCH FOR MISSING FUNCTIONS")
print("====================================================================")

targets = ["measured_moves", "ny_midnight_open", "monthly_range_ob"]

for target in targets:
    found_paths = []
    # Search all .py files in current directory recursively
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root or "smartmoneyconcepts.egg-info" in root:
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Look for def target or assignment target =
                if re.search(rf"\bdef\s+{target}\b", content) or re.search(rf"\b{target}\s*=", content):
                    found_paths.append(path.replace(".\\", ""))
            except Exception:
                pass
    if found_paths:
        print(f"'{target}' FOUND in: {', '.join(found_paths)}")
    else:
        print(f"'{target}' NOT FOUND ANYWHERE")

print("\n====================================================================")
print("PART D: FULL RAW CONSOLE OUTPUT")
print("====================================================================")

part_d_scripts = [
    "verify_month2_video2.py",
    "verify_month2_video3.py",
    "verify_month2_video4.py",
    "verify_month2_video5.py",
    "verify_month3_video6.py"
]

for script in part_d_scripts:
    print(f"\n--- Output of {script} ---")
    if not os.path.exists(script):
        print("FILE NOT FOUND")
        continue
    try:
        res = subprocess.run(["python", script], capture_output=True, text=True, timeout=15)
        print("STDOUT:")
        print(res.stdout if res.stdout else "(empty)")
        if res.stderr:
            print("STDERR:")
            print(res.stderr)
        print(f"Exit Code: {res.returncode}")
    except Exception as e:
        print(f"Execution Error: {e}")

print("\n====================================================================")
print("PART E: ALTERNATIVE FILE SEARCH")
print("====================================================================")

# Search for any candidate files for the missing videos
video_keys = {
    "Month 2 Video 1": ["month2_video1", "m2_v1", "m2v1"],
    "Month 2 Video 6": ["month2_video6", "m2_v6", "m2v6", "video6"],
    "Month 3 Video 7": ["month3_video7", "m3_v7", "m3v7", "video7", "phantom"],
    "Month 3 Video 8": ["month3_video8", "m3_v8", "m3v8", "video8", "protraction", "hns"]
}

for desc, keys in video_keys.items():
    print(f"\nCandidates for {desc}:")
    found_files = []
    for file in os.listdir("."):
        if not file.endswith(".py"):
            continue
        # Skip standard verify scripts if they existed, but they don't
        for key in keys:
            if key in file.lower():
                found_files.append(file)
                break
    if not found_files:
        print("  None found")
    else:
        for file in found_files:
            # Get one line summary by reading first few lines or docstring
            summary = "No description found"
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for _ in range(15):
                        line = f.readline()
                        if not line:
                            break
                        line_stripped = line.strip()
                        if line_stripped.startswith('"""') or line_stripped.startswith('verify') or line_stripped.startswith('#'):
                            summary = line_stripped.strip('"""# ')
                            if summary:
                                break
            except Exception:
                pass
            print(f"  - {file:<35} | Topic/Test: {summary}")
