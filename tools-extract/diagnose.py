"""
Diagnose: did the postprocess rules actually land in the live ru-RU.bytes?
Compare a few known-broken patterns before vs current state.
"""
import sqlite3, re

DB = r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes"
con = sqlite3.connect(DB)
cur = con.cursor()

rows = cur.execute("SELECT hash, text FROM translation").fetchall()
con.close()

print(f"Total rows: {len(rows)}\n")

# Things that should be FIXED (zero hits) after POSTPROCESS_RULES:
bad = [
    (r"\bиспользуете Друг\b",         "should be Друга"),
    (r"\bиспользуете Дракон\b",       "should be Дракона"),
    (r"\bиспользуете Монстр\b",       "should be Монстра"),
    (r"\b\+\{[\w.]+\} Урон\b",        "should be {X} урона"),
    (r"\b\+\d+ Урон\b",               "should be N урона"),
    (r"\bПобедите \{[\w.]+\} Монстры\b", "should be Монстров"),
    (r"\bАлмазный уровень\b",         "should be Алмазного уровня"),
    (r"\b\+\d+ Щит\b",                "should be щита"),
    (r"\b\+\{[\w.]+\} Щит\b",         "should be щита"),
    (r"\b\+\d+ Поджог\b",             "should be поджога"),
]
print("Bad pattern hits (must be ZERO after declension pass):")
for pat, hint in bad:
    n = sum(1 for h, t in rows if re.search(pat, t))
    flag = "OK" if n == 0 else f"FAIL ({n})"
    print(f"  {hint:50s} {flag}")

# Things that should be PRESENT (proof the rules ran):
good = [
    (r"\bиспользуете Друга\b",        "accusative form"),
    (r"\b\d+ урона\b",                "genitive of урон"),
    (r"\b\{[\w.]+\} урона\b",         "genitive with token"),
    (r"\bАлмазного уровня\b",         "tier in genitive"),
]
print("\nGood pattern hits (should be > 0 if rules ran):")
for pat, hint in good:
    n = sum(1 for h, t in rows if re.search(pat, t))
    print(f"  {hint:30s} {n}")

# Show a sample of what hashes were updated by postprocess-all by mtime of backup
import pathlib, os
backups = sorted(pathlib.Path(r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations").glob("ru-RU.bytes.bak_*_postproc"))
print(f"\nPostprocess backups present: {len(backups)}")
for b in backups[-3:]:
    print(f"  {b.name} ({os.path.getsize(b):,} bytes)")
