"""
Merge the LLM rough-cleanup batches (.llm-rough-batch*.json, keyed by English)
into Patch/translation-patch.json + live ru-RU.bytes, OVERWRITING the existing
rough (rule-engine) translations. English keys map to hashes via
.all-game-hashes.json (covered hashes included — we are replacing them).
Backups written first. Re-audits the rough-leftover count at the end.
"""
import json, sqlite3, shutil, glob, sys, re
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"E:\memore\the-bazaar-rus-patcher"
OUT = ROOT + r"\tools-extract"
PATCH = ROOT + r"\Patch\translation-patch.json"
CACHE = r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes"

cyr = lambda s: any('Ѐ' <= c <= 'ӿ' for c in s)

def main():
    game = json.load(open(OUT + r"\.all-game-hashes.json", encoding="utf-8"))["translations"]
    doc = json.load(open(PATCH, encoding="utf-8")); patch = doc["translations"]

    mydict = {}
    for fn in sorted(glob.glob(OUT + r"\.llm-rough-batch*.json")):
        mydict.update(json.load(open(fn, encoding="utf-8")))
    print(f"LLM rough-переводов загружено: {len(mydict)}")

    en2hashes = defaultdict(list)
    for h, en in game.items():
        en2hashes[en].append(h)

    hash_tr = {}
    for en, ru in mydict.items():
        if not cyr(ru):
            continue
        for h in en2hashes.get(en, []):
            hash_tr[h] = ru
    print(f"хешей к перезаписи: {len(hash_tr)}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(PATCH, PATCH + f".bak_{stamp}")
    for h, ru in hash_tr.items():
        patch[h] = ru
    json.dump(doc, open(PATCH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"patch: записей теперь {len(patch)} (бэкап .bak_{stamp})")

    import os
    if os.path.exists(CACHE):
        shutil.copy2(CACHE, CACHE + f".bak_{stamp}")
        con = sqlite3.connect(CACHE); cur = con.cursor(); ins = upd = 0; cur.execute("BEGIN")
        for h, ru in hash_tr.items():
            ex = cur.execute("SELECT text FROM translation WHERE hash=?", (h,)).fetchone()
            if ex is None:
                cur.execute("INSERT INTO translation(hash,text) VALUES(?,?)", (h, ru)); ins += 1
            elif ex[0] != ru:
                cur.execute("UPDATE translation SET text=? WHERE hash=?", (ru, h)); upd += 1
        con.commit(); con.close()
        print(f"cache: +{ins} новых, {upd} обновлено")

    # re-audit rough leftovers
    def clean(v):
        v = re.sub(r"<[^>]*>", " ", v); v = re.sub(r"https?://\S+", " ", v); v = re.sub(r"\{[^}]*\}", " ", v); return v
    allow = {"SMG","PVP","PVE","XP","HP","CORA","Piggles","Kyvers","Roughtown","DEBUG","Bazaar","The","EULA","br","color","size","link","b","sprite","name","u","i"}
    stop = {"the","your","you","have","has","each","for","when","and","are","is","by","it","of","an","at","if","with","this","that","to","a","in","gain","gains","start","starts","item","items","non","half","first","or","all","their","its","enemy","other","stop","able","may"}
    fn = re.compile(r"[A-Za-z]{2,}")
    rough = 0
    for h, v in patch.items():
        if not isinstance(v, str): continue
        if re.search(r"\b(bir|kazan|seviye)\b", v): continue
        words = [w for w in fn.findall(clean(v)) if w not in allow]
        if {w.lower() for w in words} & stop:
            rough += 1
    print(f"\n«Грубых» осталось в патче: {rough} (было ~1636)")

if __name__ == "__main__":
    main()
