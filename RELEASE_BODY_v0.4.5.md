## v0.4.5

Hotfix for users whose cache does not contain `translations/ru-RU.bytes`.

- Steam patcher now creates `translations/ru-RU.bytes` when the game cache is missing it.
- Steam patcher now patches every existing `translations/*.bytes` database, not only `ru-RU.bytes`, so the Russian text is applied even if the game loads another cached locale.
- `LocalLow` CDN manifests are still preserved by default to avoid the game downloading English JSON back over patched files.
