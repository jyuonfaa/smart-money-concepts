"""
Read line 106 raw bytes and extract the full ReplacementContent without truncation.
"""
import re

log_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e\.system_generated\logs\overview.txt'

with open(log_path, 'rb') as f:
    raw_bytes = f.read()

# Decode as UTF-8
text = raw_bytes.decode('utf-8', errors='replace')
lines = text.split('\n')

print(f"Total lines: {len(lines)}")
print(f"Line 106 total length: {len(lines[105])}")

# Extract ReplacementContent from line 106 using regex
line = lines[105]

# The ReplacementContent value starts after "ReplacementContent":" and ends before the next ","
# but may contain escaped quotes, so we use a careful approach
match = re.search(r'"ReplacementContent"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"StartLine"', line, re.DOTALL)
if match:
    raw_val = match.group(1)
    print(f"\nExtracted ReplacementContent length: {len(raw_val)}")
    # Unescape
    unescaped = raw_val.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
    with open('market_protraction_final.py', 'w', encoding='utf-8') as out:
        out.write(unescaped)
    print(f"Saved {len(unescaped)} chars to market_protraction_final.py")
    print("\n--- First 600 chars ---")
    print(unescaped[:600])
    print("\n--- Last 400 chars ---")
    print(unescaped[-400:])
else:
    print("Regex did not match. Trying alternate boundary...")
    # Try different end boundary
    match2 = re.search(r'"ReplacementContent"\s*:\s*"((?:[^"\\]|\\.)*)"', line, re.DOTALL)
    if match2:
        raw_val = match2.group(1)
        print(f"Alt match length: {len(raw_val)}")
        print(f"First 300: {raw_val[:300]}")
    else:
        print("No match found at all.")
        print(f"Line snippet around ReplacementContent: {line[line.find('ReplacementContent'):line.find('ReplacementContent')+200]}")
