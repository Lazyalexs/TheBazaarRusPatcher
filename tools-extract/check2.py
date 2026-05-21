"""
Proper regex check (LIKE matches substrings — "используете Друга" contains
"используете Друг" as a prefix, so LIKE gives a false positive). Use \b.
"""
import sqlite3, re

DB = r"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes"
con = sqlite3.connect(DB)
cur = con.cursor()

# Build a list of all rows once
rows = cur.execute("SELECT hash, text FROM translation").fetchall()
con.close()

def count_and_sample(label, regex):
    matches = [(h, t) for h, t in rows if re.search(regex, t)]
    print(f"{label}: {len(matches)}")
    for h, t in matches[:5]:
        m = re.search(regex, t)
        s = max(0, m.start() - 25)
        e = min(len(t), m.end() + 60)
        print(f"   {h[:18]}: ...{t[s:e]}...")
    print()

# Cases of "используете" + animate noun in WRONG (nominative) form
count_and_sample("'используете Друг' (no -а, word-boundary)",  r"\bиспользуете Друг\b")
count_and_sample("'используете Друга' (correct accusative)",   r"\bиспользуете Друга\b")
count_and_sample("'используете Друзья' (nom plural, wrong)",   r"\bиспользуете Друзья\b")
count_and_sample("'используете Друзей' (correct gen.pl)",      r"\bиспользуете Друзей\b")
count_and_sample("'используете Дракон' (no -а, wrong)",        r"\bиспользуете Дракон\b")
count_and_sample("'используете Дракона' (correct)",            r"\bиспользуете Дракона\b")
count_and_sample("'используете Монстр' (no -а, wrong)",        r"\bиспользуете Монстр\b")
count_and_sample("'используете Монстра' (correct)",            r"\bиспользуете Монстра\b")

# Also check forms with imperative "используйте"
count_and_sample("'используйте Друг' (no -а, wrong)",          r"\bиспользуйте Друг\b")
count_and_sample("'используйте Друга' (correct)",              r"\bиспользуйте Друга\b")

# Generic: "Друг" mid-sentence (not at end, not followed by a/я vowel suffix)
count_and_sample("'Друг ' mid-sentence (any context)",         r"\bДруг\b(?! и )")
