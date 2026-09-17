"""Validate the shipped resources against the frozen 18.3 snapshot."""
import collections
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
snapshot = root / 'tools-extract/snapshot-18.3-20260917b'


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def tokens(text):
    return collections.Counter(re.findall(r'\{[^{}]+\}', text))


source = read(snapshot / 'source.json')
patch = read(root / 'Patch/translation-patch.json')['translations']
delta = read(snapshot / 'delta-review.json')
excluded = read(snapshot / 'debug-excluded.json')
missing = [k for k in source if not patch.get(k)]
mismatches = [k for k, text in source.items() if k in patch and tokens(text) != tokens(patch[k])]
errors = []
for k, row in delta.items():
    if source[k] != row['en'] or patch.get(k) != row['ru']:
        errors.append(k + ': delta/source/patch disagree')
    # Check literal numbers independently of placeholder names.
    numeric = lambda text: collections.Counter(re.findall(r'\d+(?:\.\d+)?', re.sub(r'\{[^{}]+\}', '', text)))
    if numeric(row['en']) != numeric(row['ru']):
        errors.append(k + ': numeric literals disagree')
glossary = read(root / 'Patch/gamedata-tooltips.json')
tooltips = read(snapshot / 'tooltips.json')['tooltips']
glossary_missing = sorted(set(tooltips) - set(glossary))
glossary_tokens = []
for k, node in tooltips.items():
    if k in glossary:
        for field in ('Tag', 'Keyword'):
            if tokens(node[field]) != tokens(glossary[k][field]):
                glossary_tokens.append(f'{k}/{field}')
report = dict(source_keys=len(source), patch_entries=len(patch),
    additions=sum(r['kind']=='addition' for r in delta.values()),
    repairs=sum(r['kind']=='repair' for r in delta.values()),
    missing_keys=len(missing), missing_non_debug=len(set(missing)-set(excluded)),
    placeholder_mismatches=len(mismatches), glossary_missing=glossary_missing,
    glossary_placeholder_mismatches=glossary_tokens, delta_errors=errors,
    limitation='Key presence and syntax only; not a full semantic or in-game UI audit.')
(snapshot / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
assert not (set(missing)-set(excluded) or mismatches or glossary_missing or glossary_tokens or errors)
