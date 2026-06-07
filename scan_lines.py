"""
Check all lines 100-108 for the longest market_protraction code block.
"""
import json

log_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Check lines 100-108 (0-indexed: 99-107)
for i in range(98, 108):
    raw = lines[i]
    try:
        data = json.loads(raw)
        step = data.get('step_index', '?')
        tool_calls = data.get('tool_calls', [])
        for call in tool_calls:
            name = call.get('name', '')
            args = call.get('args', {})
            for key in ('ReplacementContent', 'CodeContent', 'content'):
                val = args.get(key, '')
                if 'market_protraction' in val:
                    print(f"\n=== Line {i+1}, step={step}, tool={name}, key={key} ===")
                    print(f"Length: {len(val)}")
                    # Show raw with escape sequences
                    print(f"Raw (first 300): {repr(val[:300])}")
    except Exception as e:
        pass
