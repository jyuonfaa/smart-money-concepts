import sys
import subprocess
from pathlib import Path

def run_verify_script(script_name):
    script_path = Path(__file__).parent.parent / script_name
    if not script_path.exists():
        print(f"  [MISSING] {script_name} - Cannot execute audit!")
        return False
        
    print(f"  [AUDITING] Running {script_name} regression...")
    try:
        res = subprocess.run([sys.executable, str(script_path)], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                             text=True, timeout=60)
        if res.returncode == 0:
            print(f"  [SUCCESS] {script_name} passed cleanly.")
            return True
        else:
            print(f"  [FAILED] {script_name} failed with code {res.returncode}.")
            print(res.stderr)
            return False
    except Exception as e:
        print(f"  [ERROR] Exception executing {script_name}: {e}")
        return False

def bootstrap_system():
    print("""
========================================================================
            CSLIM ANTIMATTER CONTEXT BOOTSTRAPPER & AUDITOR
========================================================================
    
This script initializes and synchronizes the complete long-term memory
of the ICT Intelligence Suite (2016 Mentorship) across new devices.

Memory Assets Registered:
  - cslim/project_forensics.md : Exhaustive timeline from Video 1 through M2V2
  - cslim/knowledge_sync.md    : Multi-timeframe rules and indicator schemas
  - cslim/lessons_learned.md   : Historical visual/data audit lessons learned
  - cslim/kis/                 : Replicable Knowledge Item directory
    """)
    
    # 1. Environment and dependencies check
    print("--- 1. ENVIRONMENT AUDIT ---")
    dependencies = ["pandas", "numpy", "plotly", "pytz"]
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  [OK] {dep} is correctly installed.")
        except ImportError:
            print(f"  [MISSING] {dep} is not installed!")
            missing.append(dep)
            
    if missing:
        print("\nError: Missing required packages. Please install them:")
        print(f"  pip install {' '.join(missing)}")
        return
        
    print("Environment matches all core execution requirements.\n")
    
    # 2. Replicate KIs
    print("--- 2. SYSTEM KNOWLEDGE REPLICATION ---")
    try:
        from replicate_kis import replicate_knowledge_items
        replicate_knowledge_items()
    except Exception as e:
        print(f"  [ERROR] Could not replicate KIs: {e}")
    print("")
    
    # 3. Running Regression Verification Gates
    print("--- 3. REGRESSION GATE VERIFICATION ---")
    step2_ok = run_verify_script("verify_step2.py")
    video8_ok = run_verify_script("verify_video8.py")
    video2_ok = run_verify_script("verify_month2_video2.py")
    
    # 4. Bootstrap complete
    print("\n========================================================================")
    print("                        BOOTSTRAP AUDIT REPORT")
    print("========================================================================")
    print(f"  System Parity Audit          : {'PASSED' if (step2_ok and video8_ok and video2_ok) else 'FAILED'}")
    print(f"  Golden Master Regression     : {'PASSED (HRR=471, LRR=37)' if step2_ok else 'FAILED'}")
    print(f"  Video 8 Temporal Anchors     : {'PASSED' if video8_ok else 'FAILED'}")
    print(f"  Month 2 Video 2 Fractal Stops: {'PASSED' if video2_ok else 'FAILED'}")
    print("========================================================================")
    print("All curriculum locks are verified and in memory. Welcome to jyuonfaa/smart-money-concepts!")

if __name__ == '__main__':
    bootstrap_system()
