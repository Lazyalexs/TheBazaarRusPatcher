# Steam-only patcher

Отдельная сборка для Steam-клиента.

Steam-ветка использует отдельные ресурсы:

```text
Patch\steam-translation-patch.json
Patch\steam-quality-overrides.json
Patch\steam-glossary.json
```

Формат Steam-патча:

```text
key + sourceText -> translatedText
```

Это нужно, чтобы Steam-сборка не путала разные английские строки с одинаковым `TranslationKey`.

Дополнительно Steam-версия использует:

- quality overrides для кривых и неточных формулировок;
- глоссарий для унификации терминов и тегов;
- отдельный `ru-RU.bytes` в кэше локализаций.

Базовая терминология для Steam-ветки:

- `Burn` -> `Поджог`
- `Heal` -> `Исцеление`
- `Regen` -> `Регенерация`
- `Poison` -> `Яд`
- `Damage` -> `Урон`
- `Crit Chance` -> `Шанс критического удара`
- `Shield` -> `Щит`
- `Slow` -> `Замедление`
- `Haste` -> `Ускорение`
- `Freeze` -> `Заморозка`

Сборка:

```powershell
dotnet publish .\TheBazaarRusSteamPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish-steam
```

Готовый файл:

```text
publish-steam\TheBazaarRusSteamPatcher.exe
```

Steam-сборка патчит только:

```text
steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets
AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache
```

И не трогает папку Tempo Launcher.

Проверка без записи файлов:

```powershell
.\publish-steam\TheBazaarRusSteamPatcher.exe --check
```

Установка:

```powershell
.\publish-steam\TheBazaarRusSteamPatcher.exe --install --yes
```

В основной сборке `TheBazaarRusPatcher.exe` также доступен режим:

```powershell
.\TheBazaarRusPatcher.exe --steam-only --check
```
