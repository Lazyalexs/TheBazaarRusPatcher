# The Bazaar Russian Patcher v0.4.2

Steam-обновление русификатора с исправлениями установки для Steam-версии.

Что исправлено:
- Steam-сборка теперь использует Steam patch format 2;
- исправлено безопасное применение `key + sourceText`, без переноса текста между разными строками с одинаковым ключом;
- `tooltips.json` патчится в новой схеме `Id/Tag/Keyword`;
- Steam-кэш патчит только `translations/ru-RU.bytes`, не остальные языки;
- обновление manifest учитывает записи вида `ru-RU`;
- `build-steam.ps1` корректно завершается при ошибках и обходит битую NuGet fallback-конфигурацию.

Файлы релиза:
- `TheBazaarRusSteamPatcher.exe` - новая Steam-сборка;
- `TheBazaarRusPatcher.exe` - launcher-сборка перенесена без изменений;
- `Patch.zip` - папка `Patch` с файлами патча.

Проверка:
```powershell
.\TheBazaarRusSteamPatcher.exe --check
```

Установка Steam:
```powershell
.\TheBazaarRusSteamPatcher.exe --install --yes
```

Если Steam-файлы уже были повреждены старой сборкой, сначала восстановите целостность файлов игры в Steam, затем запускайте установку русификатора.
