## v0.4.4

Hotfix for Steam cache rollback.

- The Steam patcher no longer rewrites `LocalLow` CDN manifests by default. Keeping the original server ETag lets the game receive `304 Not Modified` and prevents it from downloading English JSON back over the patched files on launch.
- The patcher now searches all detected `LocalLow\Tempo Storm\The Bazaar\*\cache` folders instead of only the hardcoded `prod\cache`.
- The patcher now scans all top-level static JSON files in each cache/StreamingAssets folder and patches any supported `Key/Text` or tooltip nodes it finds.

If you intentionally need the old manifest rewrite behavior, run with `--update-manifest`.
