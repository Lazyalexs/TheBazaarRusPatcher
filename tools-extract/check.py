"""
Direct text-search audit of ru-RU.bytes — avoids PowerShell terminal encoding
mangling so we can actually see what's there.
"""
import sqlite3, re

DB = r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes"
con = sqlite3.connect(DB)
cur = con.cursor()

# Targets: "используете" + noun forms
queries = [
    ("используете Друг",   "should be Друга (accusative)"),
    ("используете Друга",  "OK — accusative"),
    ("используете Друзья", "should be Друзей (gen.pl)"),
    ("используете Дракон", "should be Дракона"),
    ("используете Дракона", "OK"),
    ("используете Монстр", "should be Монстра"),
    ("используете Монстра", "OK"),
    ("Друг или", "Друг followed by word — possibly mid-sentence"),
    ("Друга или", "OK — accusative"),
    ("Друг и ", "Друг in conjunction — should be Друга"),
    ("Друга и ", "OK"),
    ("используете a Friend", "untranslated leftover"),
    ("используете Friend", "untranslated"),
]
print("Audit of ru-RU.bytes:")
for needle, hint in queries:
    rows = cur.execute("SELECT hash, text FROM translation WHERE text LIKE ?", (f"%{needle}%",)).fetchall()
    print(f"  '{needle}' -> {len(rows)} rows ({hint})")
    if rows and len(rows) <= 3:
        for h, t in rows[:3]:
            # Show only a window around the match
            idx = t.find(needle)
            s = max(0, idx - 20)
            e = min(len(t), idx + len(needle) + 60)
            window = t[s:e].replace("\n", " ")
            print(f"      {h[:18]}: ...{window}...")

# Also look at the tooltips table BLOB itself: is "Друг" tag rendered nominative?
print()
print("Tooltips BLOB in GameData.db — Friend entry:")
gdb = r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\GameData.db"
c2 = sqlite3.connect(gdb)
cur2 = c2.cursor()
row = cur2.execute("SELECT Data FROM tooltips").fetchone()
if row:
    import json
    obj = json.loads(row[0].decode("utf-8"))
    f = obj.get("Friend") or obj.get("Friends")
    if f:
        print(f"  Friend.Tag    : {f.get('Tag')}")
        print(f"  Friend.Keyword: {f.get('Keyword')}")
    else:
        # search keys
        for k in obj.keys():
            if "Friend" in k or "Друг" in (obj[k].get("Tag", "")):
                print(f"  key={k}: Tag={obj[k].get('Tag')} Keyword={obj[k].get('Keyword')}")
c2.close()
con.close()
