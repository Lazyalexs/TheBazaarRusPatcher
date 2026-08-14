"""
Scrape BazaarDB patch notes for a given version.
Writes the content to stdout (markdown-ish).

Usage: python _bazaar_scrape.py [--version 17] [--host https://sin.bazaardb.gg]
"""

import json
import re
import sys
import urllib.request
import urllib.error
from html import unescape as html_unescape


DEFAULT_HOST = "https://sin.bazaardb.gg"
UA = "TheBazaarRusPatcher/0.5"


def fetch_text(url, attempts=3):
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code >= 500 and i < attempts - 1:
                continue
            raise
        except Exception:
            if i < attempts - 1:
                continue
            raise


def decode_next_flight(html):
    """Reconstruct the Next.js RSC flight data from self.__next_f.push chunks."""
    chunks = []
    for m in re.finditer(r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)</script>', html):
        chunks.append(json.loads(f'"{m.group(1)}"'))
    return "".join(chunks)


def extract_json_object(source, start):
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(source)):
        c = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise ValueError("Unterminated JSON object")


def extract_initial_data(html):
    unescaped = decode_next_flight(html) or html
    m = re.search(r'"initialData":', unescaped)
    if not m:
        raise ValueError("initialData not found")
    return json.loads(extract_json_object(unescaped, m.end()))


def fetch_patchnotes(host, version=None):
    """Fetch all patch notes pages and filter by version."""
    all_notes = []
    page = 1
    while True:
        url = f"{host}/patchnotes"
        if page > 1:
            url += f"?page={page}"
        print(f"  Fetching {url} ...", file=sys.stderr)
        html = fetch_text(url)
        data = extract_initial_data(html)
        notes = data.get("patchNotes") or data.get("pageCards") or []
        if not notes:
            break
        for note in notes:
            v = str(note.get("Version", note.get("version", "")))
            if version is None or v.startswith(str(version)):
                all_notes.append(note)
        total = data.get("total", 0)
        page_size = len(notes)
        if page * page_size >= total:
            break
        page += 1
    return all_notes


def render_note(note):
    version = note.get("Version", note.get("version", "??"))
    title = note.get("Title", note.get("title", ""))
    date = note.get("Date", note.get("date", ""))
    body = note.get("Body", note.get("body", note.get("Content", note.get("content", ""))))

    lines = [f"## Патч {version} — {html_unescape(title or '')}"]
    if date:
        lines.append(f"**Дата:** {date}")
    lines.append("")
    if body:
        if isinstance(body, str):
            lines.append(html_unescape(body))
        elif isinstance(body, list):
            for section in body:
                if isinstance(section, dict):
                    h = section.get("Header", section.get("header", ""))
                    t = section.get("Text", section.get("text", ""))
                    if h:
                        lines.append(f"### {html_unescape(h)}")
                    if t:
                        lines.append(html_unescape(t))
                elif isinstance(section, str):
                    lines.append(html_unescape(section))
                lines.append("")
    return "\n".join(lines)


def main():
    version = None
    host = DEFAULT_HOST

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--version" and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] in ("--help", "-h"):
            print(__doc__)
            return
        else:
            # positional: version
            version = args[i]
            i += 1

    print(f"=== BazaarDB Patch Notes Scraper ===", file=sys.stderr)
    print(f"Host: {host}, Version filter: {version or 'all'}", file=sys.stderr)

    try:
        notes = fetch_patchnotes(host, version)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nTrying fallback host https://bazaardb.gg ...", file=sys.stderr)
        try:
            notes = fetch_patchnotes("https://bazaardb.gg", version)
        except Exception as e2:
            print(f"ERROR: {e2}", file=sys.stderr)
            sys.exit(1)

    if not notes:
        print(f"No patch notes found for version {version or 'any'}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(notes)} patch note(s)", file=sys.stderr)
    print()

    for note in notes:
        print(render_note(note))
        print()


if __name__ == "__main__":
    main()
