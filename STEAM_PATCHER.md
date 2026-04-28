# Steam patcher

Актуальная Steam-версия распространяется как архив:

```text
TheBazaarRusSteamPatcher.zip
```

Внутри архива:

```text
Install_Russian.bat
Uninstall_Russian.bat
install-rus.ps1
payload\
tools\
localization-audit-report.txt
localization-audit-report.json
```

## Что делает установщик

Steam-архив ставит готовую русификацию в Steam-клиент The Bazaar и локальный кэш игры:

```text
steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets
AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache
```

Установщик:

- заменяет `cards.json` и `challenges.json`;
- обновляет кэшированные `cards.json` и `challenges.json`;
- патчит cached `translations/*.bytes`, включая `ru-RU.bytes`;
- создает недостающий `translations\ru-RU.bytes`, если его нет в кэше;
- делает резервную копию перед заменой файлов;
- не трогает папку Tempo Launcher.

## Установка

1. Закройте The Bazaar.
2. Распакуйте `TheBazaarRusSteamPatcher.zip`.
3. Запустите `Install_Russian.bat`.
4. Если путь к Steam-версии не найден автоматически, укажите папку игры вручную.

Ручной запуск:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-rus.ps1
```

С явными путями:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-rus.ps1 -GamePath "C:\Program Files (x86)\Steam\steamapps\common\The Bazaar" -CachePath "$env:USERPROFILE\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache"
```

## Откат

Для восстановления последней резервной копии:

```text
Uninstall_Russian.bat
```

## Что внутри payload

Steam-архив содержит уже подготовленный payload:

```text
payload\cards.json
payload\challenges.json
payload\cache\cards.json
payload\cache\challenges.json
payload\cache\translations\*.bytes
```

Он собран из текущей Steam-версии игры и пропущен через проверку локализации.

## Исходные таблицы

В репозитории также остаются исходные таблицы Steam-перевода для C#-версии патчера:

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

## Legacy C# Steam patcher

Старая C# Steam-сборка может быть собрана из исходников, но для обычных пользователей сейчас рекомендуется zip-архив из Releases.

Сборка legacy exe:

```powershell
dotnet publish .\TheBazaarRusSteamPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish-steam
```

Готовый legacy-файл:

```text
publish-steam\TheBazaarRusSteamPatcher.exe
```

Проверка legacy exe без записи файлов:

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
