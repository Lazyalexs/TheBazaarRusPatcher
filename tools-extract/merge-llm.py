"""
Merge the LLM-authored translations (.llm-batch*.json, keyed by English) into:
  1. Patch/translation-patch.json   (shipped patch — source of truth)
  2. every present ru-RU.bytes        (live caches, for immediate in-game testing)

English keys are mapped to hashes via .all-game-hashes.json, restricted to the
hashes the shipped patch does NOT yet cover. Backups are written before any
mutation. Re-verifies coverage at the end.
"""
import json, sqlite3, shutil, glob, sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"E:\memore\the-bazaar-rus-patcher")
OUT = ROOT / "tools-extract"
PATCH = ROOT / "Patch" / "translation-patch.json"

BYTES_PATHS = [
    Path(r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes"),
    Path(r"G:\SteamLibrary\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets\translations\ru-RU.bytes"),
    Path(r"C:\Users\users\AppData\Roaming\Tempo Launcher - Beta\game\buildx64\TheBazaar_Data\StreamingAssets\translations\ru-RU.bytes"),
]

cyr = lambda s: any('Ѐ' <= c <= 'ӿ' for c in s)

def main():
    game = json.load(open(OUT / ".all-game-hashes.json", encoding="utf-8"))["translations"]
    patch_doc = json.load(open(PATCH, encoding="utf-8"))
    patch = patch_doc["translations"]
    covered = {h for h, v in patch.items() if isinstance(v, str) and v.strip()}
    uncov = {h: game[h] for h in game if h not in covered}

    mydict = {}
    for fn in sorted(glob.glob(str(OUT / ".llm-batch*.json"))):
        mydict.update(json.load(open(fn, encoding="utf-8")))
    print(f"LLM-переводов загружено: {len(mydict)}")

    # english -> hash(es), only for uncovered hashes, only cyrillic values
    hash_tr = {}
    for h, en in uncov.items():
        ru = mydict.get(en)
        if ru and cyr(ru):
            hash_tr[h] = ru
    print(f"Хешей к добавлению: {len(hash_tr)}")

    # --- backup + merge patch json ---
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(PATCH, PATCH.with_suffix(f".json.bak_{stamp}"))
    for h, ru in hash_tr.items():
        patch[h] = ru
    json.dump(patch_doc, open(PATCH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"patch: бэкап translation-patch.json.bak_{stamp}, теперь записей: {len(patch)}")

    # --- backup + merge each present ru-RU.bytes ---
    for db in BYTES_PATHS:
        if not db.exists():
            print(f"  bytes: пропуск (нет) {db}")
            continue
        shutil.copy2(db, db.with_suffix(f".bytes.bak_{stamp}"))
        con = sqlite3.connect(str(db)); cur = con.cursor()
        ins = upd = 0
        cur.execute("BEGIN")
        for h, ru in hash_tr.items():
            ex = cur.execute("SELECT text FROM translation WHERE hash=?", (h,)).fetchone()
            if ex is None:
                cur.execute("INSERT INTO translation(hash,text) VALUES(?,?)", (h, ru)); ins += 1
            elif ex[0] != ru:
                cur.execute("UPDATE translation SET text=? WHERE hash=?", (ru, h)); upd += 1
        con.commit(); con.close()
        print(f"  bytes: {db.parent.parent.name}\\...  +{ins} новых, {upd} обновлено")

    # --- re-verify coverage ---
    covered2 = {h for h, v in patch.items() if isinstance(v, str) and v.strip()}
    gh = set(game)
    cov = len(gh & covered2)
    print(f"\n=== ПОКРЫТИЕ ПОСЛЕ МЁРЖА ===")
    print(f"game hashes: {len(gh):,} | покрыто: {cov:,} = {cov/len(gh)*100:.1f}% | осталось: {len(gh-covered2):,}")

if __name__ == "__main__":
    main()
