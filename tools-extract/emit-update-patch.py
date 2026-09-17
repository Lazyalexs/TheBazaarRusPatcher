"""Print an apply_patch diff for the reviewed delta; never writes the patch itself."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
root = Path(__file__).resolve().parent.parent
path = root / 'Patch/translation-patch.json'
delta = json.loads((root / 'tools-extract/snapshot-18.3-20260917b/delta-review.json').read_text(encoding='utf-8'))
current = json.loads(path.read_text(encoding='utf-8'))['translations']
lines = path.read_text(encoding='utf-8').splitlines()
print('*** Begin Patch')
print('*** Update File: ' + path.as_posix())
positions = {k: i for i, k in enumerate(current)}
for key, row in sorted(delta.items(), key=lambda item: positions.get(item[0], len(positions))):
    if key in current and current[key] != row['ru']:
        match = [line for line in lines if line.lstrip().startswith(json.dumps(key) + ':')]
        assert len(match) == 1, key
        old = match[0]
        new = '    ' + json.dumps(key) + ': ' + json.dumps(row['ru'], ensure_ascii=False) + (',' if old.endswith(',') else '')
        print('@@\n-' + old + '\n+' + new)
additions = [(k, r['ru']) for k, r in delta.items() if k not in current]
if additions:
    assert lines[-2:] == ['  }', '}']
    print('@@\n-' + lines[-3] + '\n+' + lines[-3] + ',')
    for i, (key, value) in enumerate(additions):
        print('+    ' + json.dumps(key) + ': ' + json.dumps(value, ensure_ascii=False) + (',' if i < len(additions)-1 else ''))
    print('   }\n }')
print('*** End Patch')
