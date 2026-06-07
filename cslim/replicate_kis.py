import os
import shutil
from pathlib import Path

def replicate_knowledge_items():
    print("=== ANTIMATTER KNOWLEDGE ITEM REPLICATOR ===")
    
    # Locate workspace cslim/kis directory
    workspace_kis_dir = Path(__file__).parent / "kis"
    if not workspace_kis_dir.exists():
        print(f"Error: Localized KIs directory not found at {workspace_kis_dir}")
        return
    
    # Determine the target AppData directory for Antigravity Knowledge base
    # AppData AppData Home: C:\Users\<User>\.gemini\antigravity\knowledge
    home_dir = Path.home()
    target_knowledge_base = home_dir / ".gemini" / "antigravity" / "knowledge"
    
    print(f"Targeting System AppData: {target_knowledge_base}\n")
    
    # Mapping of localized folders to active KIs
    ki_mappings = {
        "notes_standard.md": "ict-notes-standard/artifacts/notes_standard.md",
        "gatekeeper.md": "ict-gatekeeper-protocol/artifacts/gatekeeper.md",
        "engineering_standards.md": "ict-engineering-standards/artifacts/engineering_standards.md",
        "protocol.md": "ict-new-notes-protocol/artifacts/protocol.md",
        "rules.md": "ict-development-rules/artifacts/rules.md",
        "context.md": "ict-intelligence-suite/artifacts/context.md"
    }
    
    copied_count = 0
    for filename, relative_dest in ki_mappings.items():
        src_file = workspace_kis_dir / filename
        dest_file = target_knowledge_base / relative_dest
        
        if src_file.exists():
            # Ensure target parent folder exists
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(src_file, dest_file)
            print(f"  [SYNCED] {filename} -> {relative_dest}")
            copied_count += 1
        else:
            print(f"  [MISSING] Source file not found: {src_file}")
            
    print(f"\nSuccessfully replicated {copied_count} Knowledge Items directly to Antigravity's active system memory!")
    print("New Antigravity instances will instantly register all curriculum rules and OTE definitions!")

if __name__ == '__main__':
    replicate_knowledge_items()
