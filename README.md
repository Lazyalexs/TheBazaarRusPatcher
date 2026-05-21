# Русификатор The Bazaar

Неофициальный фанатский перевод **The Bazaar** на русский язык.

💬 **[Discord-сообщество](https://discord.gg/FH8z7D3xe7)** — вопросы по установке, баг-репорты, предложения по переводу.

Поддерживаются обе версии игры — Steam и Tempo Launcher. Скачайте нужный патчер в [Releases](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest):

| Файл | Для какой версии |
|---|---|
| `TheBazaarRusPatcher-Steam.exe` | Steam-копия The Bazaar |
| `TheBazaarRusPatcher-Tempo.exe` | Tempo Launcher (beta) |

Имя файла сам определяет какую копию игры патчить — флаги указывать не нужно. Бинарник самодостаточный (.NET 8 включён), просто скачайте и запустите.

## Установка

1. Закройте The Bazaar и лаунчер (Steam или Tempo).
2. Скачайте нужный `.exe` из последнего релиза.
3. Двойной клик — откроется консольное меню, выберите пункт 1 (установить).

Без меню, одной командой:

```powershell
.\TheBazaarRusPatcher-Steam.exe --install --yes
# или
.\TheBazaarRusPatcher-Tempo.exe --install --yes
```

После установки перезапустите игру **через лаунчер** (не через ярлык на рабочем столе). В меню **Settings → Language** выберите «Русский».

## Что переведено

- **15 000+ строк** в локализационной базе `ru-RU.bytes`;
- описания всех карт, тултипов и испытаний (в `cards.json`, `tooltips.json`, `challenges.json`);
- BLOB-данные в `GameData.db` (cards, challenges, tooltips, monsters);
- внутриигровой глоссарий терминов (`Burn → Поджог`, `Income → Доход`, `Charge → Зарядить`, и т.д.);
- основные UI-элементы, главное меню, настройки, экраны побед/поражений;
- **«Русский» добавлен в список языков** в настройках игры.

Покрытие переводов **≈ 99.97%** (10 286 из 10 289 уникальных hash в game data).

## Команды

```powershell
.\TheBazaarRusPatcher-Steam.exe                  # интерактивное меню
.\TheBazaarRusPatcher-Steam.exe --install --yes  # установить без подтверждения
.\TheBazaarRusPatcher-Steam.exe --check          # проверить состояние, не менять файлы
.\TheBazaarRusPatcher-Steam.exe --paths          # показать какие пути найдены
.\TheBazaarRusPatcher-Steam.exe --restore        # откатить последний бэкап
.\TheBazaarRusPatcher-Steam.exe --game-path "C:\Games\The Bazaar\..." # явный путь
```

Все опции одинаково работают и для Tempo-версии. Флаги `--steam-only` / `--tempo-only` можно указать явно если нужно патчить вручную (но обычно имя бинарника уже это решает).

## Архитектура

- `Patch/translation-patch.json` (14 000+ entries) — основная таблица переводов, встроена в exe как ресурс.
- `Patch/gamedata-tooltips.json` (123 термина) — переводы tag/keyword для таблицы `tooltips` в `GameData.db`.
- Патчер обрабатывает:
  - JSON-файлы в `StreamingAssets/` и LocalLow кэше (`cards.json`, `tooltips.json`, `challenges.json`);
  - SQLite `translations/ru-RU.bytes` — основной источник локализации игры;
  - SQLite `GameData.db` — BLOB-таблицы с описаниями карт/испытаний/монстров и глоссарием tooltips;
  - `maintenance.json` — добавляет `ru-RU` в список локалей чтобы появился пункт «Русский» в настройках.
- Файл `manifest.json` **не трогается** — игра при запуске сравнивает локальный ETag с CDN. Сохранение CDN-ETag заставляет сервер ответить `304 Not Modified` и наш патч переживает запуск.
- Перед изменением каждого файла создаётся бэкап в `.rus_patch_backups/` рядом с файлом — `--restore` откатывает последний.

## Обратная связь

- **Discord:** [discord.gg/FH8z7D3xe7](https://discord.gg/FH8z7D3xe7) — обсуждение, помощь с установкой, баг-репорты.
- **Email:** `adeptas3@gmail.com` — для длинных багов с приложениями.

При репорте бага полезно приложить:

- скриншот карты/тултипа/меню с английским текстом;
- какая версия игры (Steam / Tempo);
- что выводит `.\TheBazaarRusPatcher-XXX.exe --check`.

## Важно

Русификатор не связан с Tempo, Tempo Storm, AVY Entertainment или разработчиками The Bazaar.

Перед заменой файлов патчер создаёт бэкап (`.rus_patch_backups/<timestamp>/`). Откат — `--restore`.

См. также: [DISCLAIMER.md](DISCLAIMER.md), [CONTACT_RIGHTS_HOLDER.md](CONTACT_RIGHTS_HOLDER.md).

## Для разработчиков

Требуется .NET SDK 8+. Сборка:

```powershell
.\build.ps1
```

Производит `dist\TheBazaarRusPatcher-Tempo.exe` и `dist\TheBazaarRusPatcher-Steam.exe`. Тот же бинарник, переименован — каждый автоматически выбирает целевой лаунчер по своему имени файла.

Pipeline переводов (в `tools-extract/`):

1. `extract.cs` — извлекает все `{Key, Text}` пары из game data;
2. `diff.cs` — сравнивает с текущим `ru-RU.bytes`, выдаёт список непереведённых hash;
3. `translate.py` — пакетный pattern-translator с глоссарием и postprocess-правилами (падежи);
4. `manual-additions.py` — ручные переводы для строк которые pattern не покрыл;
5. `merge.py` — встраивает новые `(hash, text)` rows в `ru-RU.bytes` и в `Patch/translation-patch.json`;
6. `postprocess-all.py` — применяет падежные правила ко всем существующим entries.
