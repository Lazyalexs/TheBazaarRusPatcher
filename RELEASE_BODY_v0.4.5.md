# v0.4.5

Финальная сборка для двух вариантов установки: отдельно для лаунчера и отдельно для Steam.

## Что скачивать

- `TheBazaarRusPatcher.exe` - версия для Tempo Launcher и совместимых установок The Bazaar.
- `TheBazaarRusSteamPatcher.zip` - готовый архив для Steam.
- `Patch.zip` - таблицы перевода для launcher-версии.
- `SHA256SUMS.txt` - контрольные суммы файлов релиза.

## Steam-версия

Для Steam теперь рекомендуется скачивать `TheBazaarRusSteamPatcher.zip`.

Как установить:

1. Закройте The Bazaar.
2. Распакуйте `TheBazaarRusSteamPatcher.zip` в любую папку.
3. Запустите `Install_Russian.bat`.
4. Если игра установлена не в стандартную папку Steam, укажите путь вручную.

Что делает Steam-архив:

- заменяет `TheBazaar_Data/StreamingAssets/cards.json` и `challenges.json`;
- обновляет локальный кэш в `AppData/LocalLow/Tempo Storm/The Bazaar/prod/cache`;
- патчит cached `translations/*.bytes`, чтобы убрать турецкие, английские и неполные строки;
- создает резервную копию перед заменой файлов;
- поддерживает откат через `Uninstall_Russian.bat`;
- не трогает Tempo Launcher.

Если после установки часть строк не изменилась, закройте игру полностью и запустите установку еще раз. Это важно, потому что часть текста игра берет из `LocalLow` cache.

## Launcher-версия

Для игры из Tempo Launcher используйте `TheBazaarRusPatcher.exe`.

## Что исправлено в этой версии

- Добавлен готовый Steam-архив для прямой установки.
- Обновлен LocalLow cache и SQLite `translations/*.bytes`.
- Исправлены турецкие и английские остатки в интерфейсе.
- Уточнены формулировки карточек, тегов, NPC и описаний.
- Исправлены проблемные строки для `Dooltron`, `Power Drill`, `Firepower`, `Fire Bomb`, `Coral`, `Money Furnace`, `Diana-Saur`, `Trollosaur`.
- Исправлены placeholder-строки, где в игре могли появляться значения вроде `{ability.0}`.
