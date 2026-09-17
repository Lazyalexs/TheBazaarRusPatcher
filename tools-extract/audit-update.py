"""Snapshot official game data and compare localization with the shipped patch.

Requires Python with SQLite >= 3.37. Never modifies the game or the baseline.
Usage: python audit-update.py --output <new-directory>
"""
import argparse
import collections
import hashlib
import io
import json
import re
import sqlite3
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if sqlite3.sqlite_version_info < (3, 37):
        parser.error('SQLite >= 3.37 required for STRICT tables')
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, data):
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    provenance = {'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'files': {}}
    for name in ('maintenance.json', 'GameData.db.zip'):
        url = 'https://data.playthebazaar.com/static/' + name
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            provenance['files'][name] = dict(url=url, etag=response.headers.get('ETag'),
                last_modified=response.headers.get('Last-Modified'), sha256=hashlib.sha256(data).hexdigest())
        (args.output / name).write_bytes(data)
        if name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                # Extract only the expected member, never arbitrary archive paths.
                (args.output / 'GameData.db').write_bytes(archive.read('GameData.db'))
    save('provenance.json', provenance)
    baseline = json.loads((ROOT / 'tools-extract/.all-game-hashes.json').read_text(encoding='utf-8'))['translations']
    patch = json.loads((ROOT / 'Patch/translation-patch.json').read_text(encoding='utf-8'))['translations']
    texts, contexts, conflicts, tooltips = {}, collections.defaultdict(list), {}, {}
    def walk(node, context):
        if isinstance(node, dict):
            key, value = node.get('Key'), node.get('Text')
            if isinstance(key, str) and key and isinstance(value, str) and value:
                if key in texts and texts[key] != value:
                    conflicts.setdefault(key, set()).update((texts[key], value))
                texts[key] = value
                contexts[key].append(context)
            for value in node.values():
                walk(value, context)
        elif isinstance(node, list):
            for value in node:
                walk(value, context)
    counts = {}
    with sqlite3.connect((args.output / 'GameData.db').resolve().as_uri() + '?mode=ro', uri=True) as con:
        assert con.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
        for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            if not re.fullmatch(r'[a-z_]+', table):
                raise ValueError(table)
            rows = con.execute(f'SELECT Id, Data FROM "{table}"').fetchall()
            counts[table] = len(rows)
            for row_id, blob in rows:
                node = json.loads(blob)
                walk(node, f'{table}/{row_id}')
                if table == 'tooltips':
                    tooltips[str(row_id)] = node
    missing = {k: {'en': v, 'context': sorted(set(contexts[k])), 'placeholders': re.findall(r'\{[^{}]+\}', v)}
               for k, v in texts.items() if not patch.get(k)}
    changed = {k: {'before': baseline[k], 'en': v, 'ru': patch.get(k), 'context': sorted(set(contexts[k]))}
               for k, v in texts.items() if k in baseline and baseline[k] != v}
    mismatches = {k: {'en': v, 'ru': patch[k]} for k, v in texts.items() if k in patch
                  and collections.Counter(re.findall(r'\{[^{}]+\}', v)) != collections.Counter(re.findall(r'\{[^{}]+\}', patch[k]))}
    report = dict(tables=counts, unique_keys=len(texts), patch_entries=len(patch),
        added_keys=len(texts.keys() - baseline.keys()), removed_keys=len(baseline.keys() - texts.keys()),
        changed_source=len(changed), missing=len(missing), placeholder_mismatches=len(mismatches),
        conflicting_keys=len(conflicts), key_presence_percent=round(100*(len(texts)-len(missing))/len(texts), 2))
    for name, data in [('source.json', texts), ('missing.json', missing), ('changed.json', changed),
                       ('placeholder-mismatches.json', mismatches), ('tooltips.json', tooltips),
                       ('conflicts.json', {k: sorted(v) for k,v in conflicts.items()}), ('report.json', report)]:
        save(name, data)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
