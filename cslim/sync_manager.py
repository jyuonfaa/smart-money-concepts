"""
cslim/sync_manager.py — Dynamic Context Sync & Auto-Update Engine

This script dynamically maintains and auto-updates the cslim context files.
It performs three major operations:
  1. KI Mirroring: Copies active system KIs from the local AppData directory into
     cslim/kis/ to preserve on-the-fly edits made by the system.
  2. Dynamic File Discovery: Scans the workspace root for active scripts and HTML
     dashboards, automatically rebuilding the Key File Structure table in context.md.
  3. Dynamic Regression Verification: Executes all verification suites and writes
     the latest test status and date into cslim_context.json.

Run this after locking any new video milestone:
  python cslim/sync_manager.py
"""

import json
import re
import shutil
import sys
import subprocess
from datetime import date
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).parent.parent
CSLIM_DIR      = Path(__file__).parent
KIS_DIR        = CSLIM_DIR / "kis"
JSON_STATE     = CSLIM_DIR / "cslim_context.json"

# Files that belong to cslim infrastructure — must not appear in workspace scan
CSLIM_SCRIPTS = {
    "sync_manager.py", "bootstrap.py", "replicate_kis.py"
}

# Scripts whose names indicate a specific purpose (pattern-based, not a whitelist)
def classify_py(name: str) -> str:
    if name.startswith("visualize_"):
        return "Plotly visualization dashboard"
    if name.startswith("verify_"):
        return "Regression audit & verification script"
    if name == "risk_engine.py":
        return "Capital risk & exits scheduling engine"
    return None   # None = skip — not a key registered file


# ── 1. Mirror system KIs → workspace kis/ ───────────────────────────────────
def mirror_active_system_kis():
    """Reverse-syncs system-level KIs into workspace cslim/kis/ when they are newer."""
    home_dir = Path.home()
    system_kb = home_dir / ".gemini" / "antigravity" / "knowledge"
    if not system_kb.exists():
        print("  [INFO] System AppData knowledge base not found. Skipping KI mirror.")
        return

    ki_mappings = {
        "notes_standard.md":      "ict-notes-standard/artifacts/notes_standard.md",
        "gatekeeper.md":          "ict-gatekeeper-protocol/artifacts/gatekeeper.md",
        "engineering_standards.md": "ict-engineering-standards/artifacts/engineering_standards.md",
        "protocol.md":            "ict-new-notes-protocol/artifacts/protocol.md",
        "rules.md":               "ict-development-rules/artifacts/rules.md",
        "context.md":             "ict-intelligence-suite/artifacts/context.md",
    }

    print("--- 1. MIRRORING SYSTEM KNOWLEDGE ITEMS ---")
    for filename, rel_path in ki_mappings.items():
        sys_file   = system_kb / rel_path
        local_file = KIS_DIR / filename
        if sys_file.exists():
            if not local_file.exists() or sys_file.stat().st_mtime > local_file.stat().st_mtime:
                KIS_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sys_file, local_file)
                print(f"  [REVERSE-SYNCED] {filename}")
            else:
                print(f"  [UP-TO-DATE]     {filename}")
        else:
            print(f"  [MISSING IN SYSTEM] {rel_path}")


# ── 2. Scan workspace and rebuild context.md Section 5 ──────────────────────
def scan_and_update_registries():
    """Scans workspace root for scripts & HTML dashboards and rebuilds the
    Key File Structure table in kis/context.md."""
    print("\n--- 2. DYNAMIC WORKSPACE FILE REGISTRY SCAN ---")

    # Collect python scripts (pattern-classified only; skip cslim infrastructure)
    py_entries = []
    for f in sorted(WORKSPACE_ROOT.glob("*.py")):
        if f.name in CSLIM_SCRIPTS:
            continue
        purpose = classify_py(f.name)
        if purpose:
            py_entries.append((f.name, purpose))

    # Collect HTML golden master outputs
    html_files = sorted([f.name for f in WORKSPACE_ROOT.glob("*.html")])

    print(f"  Discovered {len(py_entries)} classified scripts and {len(html_files)} HTML outputs.")

    context_md_path = KIS_DIR / "context.md"
    if not context_md_path.exists():
        print("  [WARN] cslim/kis/context.md not found. Skipping registry update.")
        return

    content = context_md_path.read_text(encoding="utf-8")

    # Rebuild the table
    table_lines = [
        "## 5. Key File Structure",
        "| File | Purpose |",
        "|---|---|",
        "| `smartmoneyconcepts/smc.py` | Single source of all detector classmethods |",
        "| `smartmoneyconcepts/state_machine.py` | Core transition engine: detect_reversals(), turtle_soup_signals() |",
    ]
    for name, purpose in py_entries:
        table_lines.append(f"| `{name}` | {purpose} |")
    for html in html_files:
        table_lines.append(f"| `{html}` | Locked golden master output |")

    new_table = "\n".join(table_lines) + "\n"

    # Robust regex: match "## 5. Key File Structure" heading + all immediately
    # following table rows (lines starting with |), then stop.
    pattern = r"(## 5\. Key File Structure\n)(\|[^\n]*\n)+"
    if re.search(pattern, content):
        updated = re.sub(pattern, new_table, content)
        context_md_path.write_text(updated, encoding="utf-8")
        print("  [UPDATED] kis/context.md Key File Structure table.")
    else:
        print("  [WARN] Could not locate Section 5 table in context.md — no update applied.")


# ── 3. Run regressions and write JSON state ──────────────────────────────────
def run_regression_audits():
    """Executes all verification suites and writes pass/fail status into cslim_context.json."""
    print("\n--- 3. EXECUTING DYNAMIC REGRESSION AUDITS ---")

    scripts = [
        "verify_step2.py",
        "verify_video8.py",
        "verify_month2_video2.py",
    ]
    results = {}
    for script in scripts:
        path = WORKSPACE_ROOT / script
        if not path.exists():
            results[script] = "MISSING"
            print(f"  [MISSING] {script}")
            continue
        try:
            res = subprocess.run(
                [sys.executable, str(path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=60
            )
            status = "PASSED" if res.returncode == 0 else "FAILED"
        except Exception as e:
            status = f"ERROR: {e}"
        results[script] = status
        print(f"  [{status}] {script}")

    # Write to JSON — use a readable date string, not a float timestamp
    if JSON_STATE.exists():
        state = json.loads(JSON_STATE.read_text(encoding="utf-8"))
        state["last_updated"] = str(date.today())
        state["golden_master_metrics"]["last_regression_status"]  = results.get("verify_step2.py", "MISSING")
        state["golden_master_metrics"]["video8_status"]           = results.get("verify_video8.py", "MISSING")
        state["golden_master_metrics"]["month2_video2_status"]    = results.get("verify_month2_video2.py", "MISSING")
        JSON_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print("\n  [UPDATED] cslim_context.json with regression status and today's date.")


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    print("=" * 64)
    print("  CSLIM DYNAMIC CONTEXT SYNC ENGINE")
    print("=" * 64)
    mirror_active_system_kis()
    scan_and_update_registries()
    run_regression_audits()
    print("\n=== SYNC COMPLETE — cslim/ is fully up to date. ===\n")


if __name__ == "__main__":
    main()
