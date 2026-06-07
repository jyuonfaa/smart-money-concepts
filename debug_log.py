"""
Step 1: Understand the actual log format before trying to parse it.
"""
log_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print(f"Total file size: {len(content)} bytes")
print(f"Total lines: {len(content.splitlines())}")

# Find a line that mentions market_protraction and show surrounding context
lines = content.splitlines()
for i, line in enumerate(lines):
    if 'market_protraction' in line and 'def ' in line:
        start = max(0, i-2)
        end = min(len(lines), i+3)
        print(f"\n--- Found 'def market_protraction' at line {i+1} ---")
        print(f"Line type: {lines[i][:200]}")
        break

# Also show all lines that contain market_protraction
print("\n--- All lines with 'market_protraction' (first 120 chars each) ---")
mp_lines = [(i+1, line) for i, line in enumerate(lines) if 'market_protraction' in line]
print(f"Total: {len(mp_lines)}")
for lineno, line in mp_lines[:10]:
    print(f"  Line {lineno}: {line[:120]}")
