"""
Extracts the market_protraction implementation from a conversation log.
"""
import json
import re

log_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Each line in overview.txt is a JSON object
lines = content.splitlines()
found_code = None
for line in lines:
    if 'market_protraction' not in line:
        continue
    if 'ReplacementContent' not in line and 'CodeContent' not in line:
        continue
    # find the JSON start
    idx = line.find('{"step_index"')
    if idx == -1:
        continue
    try:
        data = json.loads(line[idx:])
        for call in data.get('tool_calls', []):
            args = call.get('args', {})
            for key in ('ReplacementContent', 'CodeContent'):
                val = args.get(key, '')
                if 'def market_protraction' in val and len(val) > 500:
                    found_code = val
                    print(f"Found in step_index={data.get('step_index')}, tool={call.get('name')}, key={key}")
                    break
            if found_code:
                break
    except Exception as e:
        continue
    if found_code:
        break

if found_code:
    # Unescape \\n -> \n, \\\" -> "  etc. (JSON string that was double-encoded)
    try:
        unescaped = found_code.encode('raw_unicode_escape').decode('unicode_escape')
    except Exception:
        unescaped = found_code.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')

    with open('market_protraction_final.py', 'w', encoding='utf-8') as out:
        out.write(unescaped)
    print("Saved to market_protraction_final.py")
    print("First 500 chars:")
    print(unescaped[:500])
else:
    print("Could not find market_protraction implementation in log.")
