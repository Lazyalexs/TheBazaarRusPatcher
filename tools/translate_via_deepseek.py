"""
Re-translate The Bazaar source strings via DeepSeek with strict glossary enforcement.

Usage:
    python tools/translate_via_deepseek.py                 # full run, all strings
    python tools/translate_via_deepseek.py --limit 50      # sample run
    python tools/translate_via_deepseek.py --batch-size 20 # tune batch
    python tools/translate_via_deepseek.py --steam         # also build steam patch

Reads:
    %LocalAppData%\..\LocalLow\Tempo Storm\The Bazaar\prod\cache\cards.json
    %LocalAppData%\..\LocalLow\Tempo Storm\The Bazaar\prod\cache\challenges.json
    Patch/glossary.json
    Patch/translation-patch.json (for skip-already-translated mode)

Writes:
    Patch/translation-patch.json     (with all new translations)
    Patch/steam-translation-patch.json (optional, --steam)
    tools/.translate-progress.json   (resumable progress)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time

# Force UTF-8 stdout on Windows so Cyrillic/arrows don't crash
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    import tomllib  # py 3.11+
except ImportError:
    import tomli as tomllib  # py < 3.11

import urllib.request
import urllib.error

REPO_ROOT = Path(__file__).resolve().parent.parent
PATCH_DIR = REPO_ROOT / "Patch"
GLOSSARY_PATH = PATCH_DIR / "glossary.json"
EXISTING_PATCH_PATH = PATCH_DIR / "translation-patch.json"
STEAM_PATCH_PATH = PATCH_DIR / "steam-translation-patch.json"
PROGRESS_PATH = REPO_ROOT / "tools" / ".translate-progress.json"
CARD_NAMES_PATH = REPO_ROOT / "tools" / ".translate-card-names.json"
SKILLS_DUMP_PATH = REPO_ROOT / "tools" / ".bazaardb-skills.json"

GAME_CACHE = Path(os.environ["USERPROFILE"]) / "AppData/LocalLow/Tempo Storm/The Bazaar/prod/cache"
SOURCE_FILES = ["cards.json", "challenges.json"]

DEEPSEEK_BASE = "https://api.deepseek.com/beta"
DEEPSEEK_MODEL = "deepseek-v4-pro"
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")


def load_api_key() -> str:
    config_path = Path.home() / ".deepseek" / "config.toml"
    with config_path.open("rb") as f:
        cfg = tomllib.load(f)
    # config.toml may have api_key at top level or under [providers.deepseek]
    if "api_key" in cfg:
        return cfg["api_key"]
    providers = cfg.get("providers") or {}
    deepseek = providers.get("deepseek") or {}
    if "api_key" in deepseek:
        return deepseek["api_key"]
    raise RuntimeError("DeepSeek api_key not found in ~/.deepseek/config.toml")


def load_source_strings() -> tuple[set[str], set[str]]:
    """
    Returns (all_translatable_strings, card_titles).
    card_titles are a subset of all_translatable_strings — specifically the
    Localization.Title.Text fields from cards.json (the canonical card names).
    """
    all_strings: set[str] = set()
    card_titles: set[str] = set()

    def walk_titles(card_obj: Any) -> None:
        """Find Localization.Title.Text inside a single card."""
        if not isinstance(card_obj, dict):
            return
        loc = card_obj.get("Localization")
        if isinstance(loc, dict):
            title = loc.get("Title")
            if isinstance(title, dict) and isinstance(title.get("Text"), str):
                card_titles.add(title["Text"])

    def walk_all_texts(obj: Any) -> None:
        if isinstance(obj, dict):
            text = obj.get("Text")
            if isinstance(text, str) and text:
                all_strings.add(text)
            for v in obj.values():
                walk_all_texts(v)
        elif isinstance(obj, list):
            for item in obj:
                walk_all_texts(item)

    for filename in SOURCE_FILES:
        path = GAME_CACHE / filename
        if not path.exists():
            print(f"WARN: source file not found: {path}", file=sys.stderr)
            continue
        with path.open(encoding="utf-8-sig") as f:
            data = json.load(f)
        # cards.json shape: { "5.0.0": [{card}, {card}, ...] } typically
        if filename == "cards.json" and isinstance(data, dict):
            for cards in data.values():
                if isinstance(cards, list):
                    for card in cards:
                        walk_titles(card)
        walk_all_texts(data)

    # Server-side skills come from bazaardb (not in local cache)
    if SKILLS_DUMP_PATH.exists():
        with SKILLS_DUMP_PATH.open(encoding="utf-8") as f:
            skills = json.load(f)
        for skill in skills:
            walk_titles(skill)  # Title.Text → goes to card_titles (Pass 1 will translate)
        walk_all_texts(skills)
        print(f"  Loaded {len(skills)} skills from {SKILLS_DUMP_PATH.name}", file=sys.stderr)
    else:
        print(
            f"  Skills dump not found at {SKILLS_DUMP_PATH}. "
            f"Run 'node tools/fetch-bazaardb-skills.mjs' to include skill text.",
            file=sys.stderr,
        )

    return all_strings, card_titles


def referenced_cards_in_batch(strings: list[str], card_titles: set[str]) -> dict[str, bool]:
    """Find card titles that appear in any of the given strings (substring match)."""
    referenced: dict[str, bool] = {}
    for s in strings:
        for title in card_titles:
            # Only longer titles to avoid spurious matches like "a" or "I"
            if len(title) >= 3 and title in s:
                referenced[title] = True
    return referenced


def load_glossary() -> dict[str, Any]:
    with GLOSSARY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(glossary: dict[str, Any]) -> str:
    lines = [
        "You are a professional translator for the videogame *The Bazaar*. Translate English UI/card strings into Russian.",
        "",
        "## STRICT RULES",
    ]
    for rule in glossary["rules"]:
        lines.append(f"- {rule}")

    lines.append("")
    lines.append("## CANONICAL TERMINOLOGY (use these Russian translations verbatim, no synonyms):")
    for term, data in glossary["terms"].items():
        ru = data.get("noun") or data.get("verb") or ""
        extra = ""
        if "form_does" in data:
            extra += f' (3rd-person: «{data["form_does"]}»)'
        if "context" in data:
            extra += f' — {data["context"]}'
        lines.append(f"- {term} → **{ru}**{extra}")

    lines.append("")
    lines.append("## ITEM TYPES (always capitalize as proper nouns):")
    for en, ru in glossary["item_types"].items():
        lines.append(f"- {en} → {ru}")

    lines.append("")
    lines.append("## TIERS:")
    for en, ru in glossary["tiers"].items():
        lines.append(f"- {en} → {ru}")

    lines.append("")
    lines.append("## HERO NAMES — ALWAYS KEEP ENGLISH:")
    lines.append(glossary["hero_names_rule"])
    lines.append(f"Heroes: {', '.join(glossary['hero_names_keep_english'])}")

    lines.append("")
    lines.append("## CARD-ITEM NAME REFERENCES:")
    lines.append(glossary["card_names_rule"])
    lines.append("If the per-batch user message includes a 'card_names' section, use those Russian names for any matching English card titles that appear inside the strings.")

    lines.append("")
    lines.append("## STANDARD PHRASES:")
    for en, ru in glossary["phrases"].items():
        lines.append(f"- «{en}» → «{ru}»")

    lines.append("")
    lines.append("## FORBIDDEN — never produce these (common bad translations to avoid):")
    for bad, reason in glossary["forbidden"].items():
        lines.append(f"- «{bad}» — {reason}")

    lines.append("")
    lines.append("## EXAMPLES:")
    for ex in glossary["examples"]:
        lines.append(f"EN: {ex['en']}")
        lines.append(f"RU: {ex['ru']}")
        lines.append("")

    lines.append("## OUTPUT FORMAT")
    lines.append("You will receive a JSON array of English strings to translate. Respond with **only** a JSON array of the same length, each entry being the Russian translation. No comments, no markdown, no extra text. Preserve ALL placeholders like {ability.0}, {aura.1}, {0} EXACTLY as in the source.")

    return "\n".join(lines)


def deepseek_chat(api_key: str, system: str, user: str, *, timeout: int = 120) -> str:
    body = json.dumps(
        {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{DEEPSEEK_BASE}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def extract_placeholders(s: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(s))


def validate_translation(en: str, ru: str, glossary: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty if OK)."""
    errors: list[str] = []
    if not ru or not ru.strip():
        errors.append("empty translation")
        return errors

    src_ph = extract_placeholders(en)
    tgt_ph = extract_placeholders(ru)
    if src_ph != tgt_ph:
        errors.append(f"placeholder mismatch: source={src_ph} translation={tgt_ph}")

    # forbidden patterns
    for bad in glossary["forbidden"]:
        if bad in ru:
            errors.append(f"forbidden pattern present: «{bad}»")

    # length sanity
    if len(en) > 5 and (len(ru) < len(en) * 0.4 or len(ru) > len(en) * 2.2):
        errors.append(f"length out of range: en={len(en)} ru={len(ru)}")

    return errors


def translate_batch(
    api_key: str,
    system_prompt: str,
    strings: list[str],
    glossary: dict[str, Any],
    *,
    max_retries: int = 2,
) -> list[tuple[str, str, list[str]]]:
    """Translate a batch. Returns list of (source, translation, errors)."""
    payload: dict[str, Any] = {"strings": strings}
    extra_context = ""
    card_map = getattr(translate_batch, "_card_map", None)
    if card_map:
        # only inject card names referenced by THIS batch
        all_titles = set(card_map.keys())
        refs = {t for s in strings for t in all_titles if len(t) >= 3 and t in s}
        if refs:
            ref_map = {t: card_map[t] for t in refs}
            payload["card_names"] = ref_map
            extra_context = (
                "The 'card_names' field maps English card titles referenced inside the "
                "strings to their canonical Russian translations. Use these EXACTLY when "
                "the English card name appears in a string.\n"
            )

    user = (
        "Translate the following English strings into Russian. "
        "Respond with a JSON object of shape `{\"translations\": [...]}` "
        "where the array has exactly the same length and order as the input. "
        "Apply all glossary rules. Hero names stay in English.\n"
        + extra_context
        + "\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    last_error: str | None = None
    for attempt in range(max_retries + 1):
        try:
            response = deepseek_chat(api_key, system_prompt, user)
            parsed = json.loads(response)
            if isinstance(parsed, list):
                translations = parsed
            elif isinstance(parsed, dict):
                translations = (
                    parsed.get("translations")
                    or parsed.get("strings")
                    or parsed.get("result")
                )
                if translations is None:
                    # Last resort: take all values if they look like a list of strings
                    values = list(parsed.values())
                    if len(values) == len(strings) and all(isinstance(v, str) for v in values):
                        translations = values
                if isinstance(translations, dict):
                    translations = list(translations.values())
            else:
                raise ValueError(f"unexpected top-level type: {type(parsed).__name__}")

            if not isinstance(translations, list) or len(translations) != len(strings):
                raise ValueError(
                    f"expected list of {len(strings)} translations, got "
                    f"{type(translations).__name__ if translations is not None else 'None'} of len "
                    f"{len(translations) if hasattr(translations, '__len__') else '?'}"
                )

            results: list[tuple[str, str, list[str]]] = []
            for src, tgt in zip(strings, translations):
                tgt_str = str(tgt) if tgt is not None else ""
                errors = validate_translation(src, tgt_str, glossary)
                results.append((src, tgt_str, errors))
            return results

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError) as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < max_retries:
                time.sleep(2 + attempt * 3)
                continue

    return [(s, "", [f"API failure after retries: {last_error}"]) for s in strings]


def md5_key(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Translate only N strings (0=all)")
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--workers", type=int, default=3, help="Parallel batches")
    parser.add_argument("--steam", action="store_true", help="Also write steam-translation-patch.json")
    parser.add_argument("--keep-existing", action="store_true", help="Skip strings already in translation-patch.json")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt and first batch then exit")
    parser.add_argument(
        "--pass",
        dest="pass_mode",
        choices=["titles", "rest", "all"],
        default="all",
        help="titles = translate card titles only; rest = translate everything else (uses .translate-card-names.json); all = both phases sequentially",
    )
    args = parser.parse_args()

    api_key = load_api_key()
    glossary = load_glossary()
    system_prompt = build_system_prompt(glossary)

    print(f"System prompt: {len(system_prompt)} chars (~{len(system_prompt)//4} tokens)")

    all_strings, card_titles = load_source_strings()
    sources = sorted(all_strings)
    print(f"Source strings: {len(sources)} total, {len(card_titles)} card titles")

    # Load card name map if it exists (for Pass 2 / rest mode)
    card_map: dict[str, str] = {}
    if CARD_NAMES_PATH.exists():
        with CARD_NAMES_PATH.open(encoding="utf-8") as f:
            card_map = json.load(f)
        print(f"Loaded card-name map: {len(card_map)} entries")

    # Pick what to translate based on pass mode
    if args.pass_mode == "titles":
        to_translate_set = card_titles
        print(f"Pass: TITLES only ({len(to_translate_set)} card names)")
    elif args.pass_mode == "rest":
        to_translate_set = set(sources) - card_titles
        translate_batch._card_map = card_map
        print(f"Pass: REST only ({len(to_translate_set)} strings, excluding {len(card_titles)} card titles)")
    else:
        to_translate_set = set(sources)
        translate_batch._card_map = card_map
        print(f"Pass: ALL ({len(to_translate_set)} strings)")

    existing: dict[str, str] = {}
    if args.keep_existing and EXISTING_PATCH_PATH.exists():
        with EXISTING_PATCH_PATH.open(encoding="utf-8") as f:
            existing = json.load(f).get("translations", {})
        print(f"Existing translations: {len(existing)}")

    progress: dict[str, str] = {}
    if PROGRESS_PATH.exists():
        with PROGRESS_PATH.open(encoding="utf-8") as f:
            progress = json.load(f)
        print(f"Resuming from progress: {len(progress)} translated")

    to_translate = sorted(
        s for s in to_translate_set
        if md5_key(s) not in progress
        and (not args.keep_existing or md5_key(s) not in existing)
    )
    if args.limit:
        to_translate = to_translate[: args.limit]
    print(f"Will translate: {len(to_translate)} strings in batches of {args.batch_size}")

    if args.dry_run:
        print("\n=== SYSTEM PROMPT PREVIEW (first 1500 chars) ===")
        print(system_prompt[:1500])
        print("\n=== FIRST BATCH PREVIEW ===")
        for s in to_translate[:args.batch_size]:
            print(f"  {s[:100]}")
        return 0

    batches = [to_translate[i : i + args.batch_size] for i in range(0, len(to_translate), args.batch_size)]
    start = time.time()
    errors_log: list[tuple[str, str, list[str]]] = []
    success = 0

    def run_batch(batch: list[str]) -> list[tuple[str, str, list[str]]]:
        return translate_batch(api_key, system_prompt, batch, glossary)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_batch, b): b for b in batches}
        done = 0
        for fut in as_completed(futures):
            batch = futures[fut]
            results = fut.result()
            done += 1
            for src, ru, errs in results:
                if errs:
                    errors_log.append((src, ru, errs))
                else:
                    progress[md5_key(src)] = ru
                    success += 1
            # Save progress every 5 batches
            if done % 5 == 0 or done == len(batches):
                PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = time.time() - start
                rate = success / max(elapsed, 1)
                eta = (len(to_translate) - success) / max(rate, 0.1)
                print(f"[{done}/{len(batches)} batches] ok={success} err={len(errors_log)} | {rate:.1f} str/s | ETA {eta:.0f}s")

    # If we just ran the titles pass, persist English→Russian card-name map
    if args.pass_mode == "titles":
        new_card_map = dict(card_map)
        for title in card_titles:
            ru = progress.get(md5_key(title))
            if ru:
                new_card_map[title] = ru
        CARD_NAMES_PATH.write_text(json.dumps(new_card_map, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote card-name map: {CARD_NAMES_PATH} ({len(new_card_map)} entries)")

    # Final patch
    new_translations = dict(existing)
    new_translations.update(progress)
    patch = {
        "format": 1,
        "name": "The Bazaar Russian Translation Patch",
        "language": "ru-RU",
        "translations": new_translations,
    }
    EXISTING_PATCH_PATH.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {EXISTING_PATCH_PATH} with {len(new_translations)} entries")

    if errors_log:
        err_path = REPO_ROOT / "tools" / ".translate-errors.json"
        err_path.write_text(
            json.dumps(
                [{"en": e, "ru": r, "errors": errs} for e, r, errs in errors_log],
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        print(f"WARN: {len(errors_log)} strings failed validation; details in {err_path}")

    print(f"\nDone. Success: {success}/{len(to_translate)} ({100*success/max(len(to_translate),1):.1f}%)")
    print(f"Total time: {time.time()-start:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
