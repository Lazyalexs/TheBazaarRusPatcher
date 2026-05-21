"""
Apply just the POSTPROCESS_RULES (case-agreement fixes) to every row in
ru-RU.bytes — not only the ~3 000 entries the diff pipeline owns.
Many older translations from earlier patch commits use nominative "Друг"
where Russian wants accusative "Друга" after action verbs like "используете".
"""
import sqlite3
import re
import shutil
from pathlib import Path
from datetime import datetime

# Import POSTPROCESS_RULES from translate.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from translate import POSTPROCESS_RULES

DB = Path(r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes")
PATCH_FILE = Path(r"E:\memore\the-bazaar-rus-patcher\Patch\translation-patch.json")

def apply_rules(s: str) -> str:
    for pattern, repl in POSTPROCESS_RULES:
        s = re.sub(pattern, repl, s)
    return s

def fix_bytes():
    backup = DB.with_suffix(f".bytes.bak_{datetime.now():%Y%m%d_%H%M%S}_postproc")
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    rows = cur.execute("SELECT hash, text FROM translation").fetchall()
    changed = 0
    samples_before = []
    samples_after = []
    cur.execute("BEGIN")
    for h, t in rows:
        if not t:
            continue
        new = apply_rules(t)
        if new != t:
            cur.execute("UPDATE translation SET text = ? WHERE hash = ?", (new, h))
            if len(samples_before) < 10:
                samples_before.append((h, t))
                samples_after.append((h, new))
            changed += 1
    con.commit()
    con.close()
    print(f"ru-RU.bytes rows changed by postprocess: {changed}")
    print()
    print("Sample fixes (first 10):")
    for (h, b), (_, a) in zip(samples_before, samples_after):
        print(f"  {h[:18]}")
        print(f"    before: {b[:110]}")
        print(f"    after : {a[:110]}")

def fix_patch_json():
    import json
    with PATCH_FILE.open(encoding="utf-8") as f:
        patch = json.load(f)
    changed = 0
    for k, v in patch["translations"].items():
        new = apply_rules(v)
        if new != v:
            patch["translations"][k] = new
            changed += 1
    with PATCH_FILE.open("w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)
    print(f"translation-patch.json rows changed: {changed}")

if __name__ == "__main__":
    fix_bytes()
    print()
    fix_patch_json()
