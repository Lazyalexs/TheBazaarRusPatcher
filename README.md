# Русификатор The Bazaar

Неофициальный патчер русской локализации для **The Bazaar**.

Проект поддерживает две отдельные сборки:

- `TheBazaarRusPatcher.exe` - основная версия для Tempo Launcher и совместимых установок;
- `TheBazaarRusSteamPatcher.exe` - отдельная версия для Steam.

Скачать последнюю версию:

```text
https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest
```

## Важно

Это неофициальный фанатский перевод. Проект не связан с Tempo, Tempo Storm, AVY Entertainment или разработчиками The Bazaar.

Репозиторий и релизы не распространяют игровые файлы вроде `cards.json`, `tooltips.json`, `ru-RU.bytes` и `manifest.json`. Патчер содержит только таблицы перевода и применяет их к локальным файлам игры на компьютере пользователя.

Перед изменением файлов патчер создает резервную копию в `.rus_patch_backups`.

## Что переведено

- интерфейс;
- карточки и описания эффектов;
- подсказки;
- теги предметов;
- часть NPC, магазинов и событий.

Steam-ветка дополнительно использует отдельный слой quality fixes и глоссарий терминов, чтобы уменьшить кривые подстановки в карточках и тегах.

## Обратная связь

Почта для сообщений об ошибках перевода и проблемах патчера:

```text
adeptas3@gmail.com
```

Лучше прикладывать:

- скриншот карточки, подсказки или меню;
- краткое описание ошибки;
- версию игры;
- какой клиент используется: Steam или Tempo Launcher.

## Установка

### Launcher / общая версия

1. Закройте игру и лаунчер.
2. Скачайте `TheBazaarRusPatcher.exe` из Releases.
3. Для проверки без записи файлов запустите:

```powershell
.\TheBazaarRusPatcher.exe --check
```

4. Для установки запустите:

```powershell
.\TheBazaarRusPatcher.exe --install
```

### Steam-версия

Для Steam рекомендуется использовать отдельный файл:

```text
TheBazaarRusSteamPatcher.exe
```

Проверка:

```powershell
.\TheBazaarRusSteamPatcher.exe --check
```

Установка:

```powershell
.\TheBazaarRusSteamPatcher.exe --install --yes
```

Steam-сборка патчит:

- `steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets`
- кэш игры в `AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache`

И не трогает папку Tempo Launcher.

Подробности по Steam-сборке: [STEAM_PATCHER.md](STEAM_PATCHER.md)

## Восстановление

Откат последнего бэкапа:

```powershell
.\TheBazaarRusPatcher.exe --restore
```

или для Steam:

```powershell
.\TheBazaarRusSteamPatcher.exe --restore
```

## Команды

Основная версия:

```powershell
.\TheBazaarRusPatcher.exe
.\TheBazaarRusPatcher.exe --install
.\TheBazaarRusPatcher.exe --install --yes
.\TheBazaarRusPatcher.exe --check
.\TheBazaarRusPatcher.exe --paths
.\TheBazaarRusPatcher.exe --verify-patch
.\TheBazaarRusPatcher.exe --restore
```

Steam-версия:

```powershell
.\TheBazaarRusSteamPatcher.exe --check
.\TheBazaarRusSteamPatcher.exe --install --yes
.\TheBazaarRusSteamPatcher.exe --restore
```

## Релизы

Рекомендуемая схема релизов:

- `TheBazaarRusPatcher.exe` - общий релиз для лаунчера;
- `TheBazaarRusSteamPatcher.exe` - отдельный релиз для Steam;
- в одном GitHub Release можно выкладывать оба файла как отдельные артефакты.

Готовые тексты:

- [RELEASE_NOTES_LAUNCHER.md](RELEASE_NOTES_LAUNCHER.md)
- [RELEASE_NOTES_STEAM.md](RELEASE_NOTES_STEAM.md)

## GitHub About

Описание:

```text
Русификатор The Bazaar для Tempo Launcher и Steam
```

Topics:

```text
the-bazaar russian-translation localization patcher steam launcher rusifikator
```

## Безопасность проекта

- проект не использует официальные игровые ассеты;
- проект не распространяет игровые файлы;
- есть dry-run режим `--check`;
- есть восстановление бэкапа `--restore`;
- есть отдельный дисклеймер: [DISCLAIMER.md](DISCLAIMER.md);
- есть шаблон письма правообладателю: [CONTACT_RIGHTS_HOLDER.md](CONTACT_RIGHTS_HOLDER.md).

## Сборка из исходников

Требуется .NET SDK 8 или новее.

Сборка основной версии:

```powershell
dotnet publish .\TheBazaarRusPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish
```

Сборка Steam-версии:

```powershell
dotnet publish .\TheBazaarRusSteamPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish-steam
```
