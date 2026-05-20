"""
Merge .missing-translated.json into:
  1. ru-RU.bytes (LocalLow cache) — insert new (hash, text) rows
  2. Patch/translation-patch.json — so future installs ship them too
"""
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT       = Path(r"E:\memore\the-bazaar-rus-patcher")
OUT_DIR    = ROOT / "tools-extract"
TRANSLATED = OUT_DIR / ".missing-translated.json"
PATCH_FILE = ROOT / "Patch" / "translation-patch.json"

CACHE_RU_RU = Path(r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes")
STEAM_TRANS = Path(r"G:\SteamLibrary\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets\translations\ru-RU.bytes")

def load_translated():
    with TRANSLATED.open(encoding="utf-8") as f:
        d = json.load(f)
    # Skip entries that didn't change (still English) — pointless to insert as Russian
    cyr = lambda s: any("Ѐ" <= c <= "ӿ" for c in s)
    clean = {h: t for h, t in d.items() if cyr(t)}
    print(f"Loaded {len(d)} entries; {len(clean)} have Russian text and will be inserted")
    return clean

def merge_into_bytes(db_path: Path, entries: dict):
    if not db_path.exists():
        print(f"  Skip: {db_path} not present")
        return 0
    backup = db_path.with_suffix(f".bytes.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(db_path, backup)
    print(f"  Backup: {backup.name}")

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    # Make sure schema is what we expect
    schema = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='translation'").fetchone()
    if not schema:
        print(f"  ERROR: no translation table in {db_path}")
        con.close()
        return 0

    # Upsert
    cur.execute("BEGIN")
    inserted = 0
    updated = 0
    for h, ru in entries.items():
        # Skip if exact same value already present
        existing = cur.execute("SELECT text FROM translation WHERE hash = ?", (h,)).fetchone()
        if existing is None:
            cur.execute("INSERT INTO translation(hash, text) VALUES (?, ?)", (h, ru))
            inserted += 1
        elif existing[0] != ru:
            cur.execute("UPDATE translation SET text = ? WHERE hash = ?", (ru, h))
            updated += 1
    con.commit()
    con.close()
    print(f"  Inserted: {inserted}, Updated: {updated}")
    return inserted + updated

def merge_into_patch(entries: dict):
    with PATCH_FILE.open(encoding="utf-8") as f:
        patch = json.load(f)
    before = len(patch["translations"])
    added = 0
    overwritten = 0
    for h, ru in entries.items():
        if h not in patch["translations"]:
            patch["translations"][h] = ru
            added += 1
        elif patch["translations"][h] != ru:
            # only overwrite if our new value is a real Russian translation
            # and the old value was the same English passthrough
            patch["translations"][h] = ru
            overwritten += 1
    with PATCH_FILE.open("w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)
    print(f"  Before: {before}, Added: {added}, Overwritten: {overwritten}, After: {len(patch['translations'])}")

def main():
    entries = load_translated()
    print()
    print("=== Merging into LocalLow cache ru-RU.bytes ===")
    n1 = merge_into_bytes(CACHE_RU_RU, entries)
    print()
    print("=== Merging into Steam install ru-RU.bytes ===")
    n2 = merge_into_bytes(STEAM_TRANS, entries)
    print()
    print("=== Merging into Patch/translation-patch.json ===")
    merge_into_patch(entries)
    print()
    print(f"Done. LocalLow rows changed: {n1}, Steam rows changed: {n2}")

if __name__ == "__main__":
    main()
