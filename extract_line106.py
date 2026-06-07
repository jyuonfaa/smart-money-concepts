"""
Extract market_protraction from line 106 of the conversation log.
The args values are stored as JSON strings (double-encoded), so we need careful handling.
"""
import json
import re

log_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Line 106 (0-indexed: line 105)
raw_line = lines[105]

# The outer JSON parses fine — the issue is that args values are themselves JSON strings
data = json.loads(raw_line)
call = data['tool_calls'][0]
print(f"Tool name: {call['name']}")

args = call['args']
print(f"Arg keys: {list(args.keys())}")

# ReplacementContent is a double-encoded JSON string
rc = args.get('ReplacementContent', '')
print(f"\nReplacementContent length: {len(rc)}")
print(f"First 200 chars raw:\n{rc[:200]}")

# The value is stored as a JSON string literal (with surrounding quotes stripped by first parse)
# But \\n -> \n etc. need unescaping.
# Try json.loads on it as if it were a quoted string
try:
    unescaped = json.loads(f'"{rc}"')
    print("\n[SUCCESS] json.loads unescaping worked")
except Exception as e:
    print(f"\n[FALLBACK] json.loads failed: {e}")
    unescaped = rc.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')

with open('market_protraction_final.py', 'w', encoding='utf-8') as out:
    out.write(unescaped)

print(f"\nSaved {len(unescaped)} chars to market_protraction_final.py")
print("\n--- First 800 chars of recovered code ---")
print(unescaped[:800])
