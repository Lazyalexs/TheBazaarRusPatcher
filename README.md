# Русификатор The Bazaar

Неофициальный патчер русской локализации для **The Bazaar**.

Проект поддерживает два варианта установки:

- `TheBazaarRusPatcher.exe` - основная версия для Tempo Launcher и совместимых установок;
- `TheBazaarRusSteamPatcher.zip` - отдельный готовый архив для Steam-версии игры.

Скачать последнюю версию:

```text
https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest
```

## Важно

Это неофициальный фанатский перевод. Проект не связан с Tempo, Tempo Storm, AVY Entertainment или разработчиками The Bazaar.

Исходники репозитория содержат код патчера и таблицы перевода. Steam-архив в Releases содержит готовый payload для установки русификации в Steam-клиент и локальный кэш игры.

Перед изменением файлов патчер создает резервную копию в `.rus_patch_backups`.

## Что переведено

- интерфейс;
- карточки и описания эффектов;
- подсказки;
- теги предметов;
- часть NPC, магазинов и событий.

Steam-архив дополнительно включает исправления интерфейса, карточек, описаний, тегов, NPC и cached `translations/*.bytes`, чтобы убрать турецкие/английские остатки и кривые подстановки.

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

Для Steam рекомендуется использовать архив:

```text
TheBazaarRusSteamPatcher.zip
```

Установка:

1. Закройте The Bazaar.
2. Распакуйте `TheBazaarRusSteamPatcher.zip` в любую папку.
3. Запустите `Install_Russian.bat`.
4. Если игра установлена не в стандартную папку Steam, установщик попросит указать путь.

Ручной запуск через PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-rus.ps1
```

Steam-архив устанавливает:

- `TheBazaar_Data\StreamingAssets\cards.json`
- `TheBazaar_Data\StreamingAssets\challenges.json`
- локальный кэш в `AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache`
- cached `translations/*.bytes`, включая `ru-RU.bytes`

Перед заменой файлов создается резервная копия в `.rus_patch_backups`. Папка Tempo Launcher не трогается.

Подробности по Steam-сборке: [STEAM_PATCHER.md](STEAM_PATCHER.md)

## Восстановление

Откат последнего бэкапа:

```powershell
.\TheBazaarRusPatcher.exe --restore
```

или для Steam:

```powershell
.\Uninstall_Russian.bat
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
.\Install_Russian.bat
.\Uninstall_Russian.bat
powershell -ExecutionPolicy Bypass -File .\install-rus.ps1
```

## Релизы

Рекомендуемая схема релизов:

- `TheBazaarRusPatcher.exe` - общий релиз для лаунчера;
- `TheBazaarRusSteamPatcher.zip` - готовый архив для Steam;
- `Patch.zip` - таблицы перевода для launcher-версии;
- `SHA256SUMS.txt` - контрольные суммы файлов релиза.

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

Актуальная Steam-раздача собирается как zip-архив с `Install_Russian.bat`, `Uninstall_Russian.bat`, `install-rus.ps1` и папкой `payload`.
