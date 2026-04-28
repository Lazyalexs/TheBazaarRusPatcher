# Русификатор The Bazaar

Неофициальный фанатский перевод **The Bazaar** на русский язык.

Проект поддерживает две версии установки:

- **Steam** - готовый архив `TheBazaarRusSteamPatcher.zip`;
- **Tempo Launcher** - патчер `TheBazaarRusPatcher.exe`.

Последняя версия доступна в [Releases](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest).

## Что скачать

| Клиент игры | Файл | Когда использовать |
| --- | --- | --- |
| Steam | `TheBazaarRusSteamPatcher.zip` | Если игра установлена через Steam |
| Tempo Launcher | `TheBazaarRusPatcher.exe` | Если игра установлена через официальный лаунчер |
| Tempo Launcher | `Patch.zip` | Таблицы перевода для launcher-версии |

## Установка Steam-версии

1. Закройте The Bazaar.
2. Скачайте `TheBazaarRusSteamPatcher.zip` из [последнего релиза](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest).
3. Распакуйте архив в любую папку.
4. Запустите `Install_Russian.bat`.
5. Если игра установлена не в стандартную папку Steam, установщик попросит указать путь к игре.

Ручной запуск через PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-rus.ps1
```

Steam-архив устанавливает перевод в:

- `TheBazaar_Data\StreamingAssets\cards.json`
- `TheBazaar_Data\StreamingAssets\challenges.json`
- `AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache`
- cached `translations/*.bytes`, включая `ru-RU.bytes`

Перед заменой файлов создается резервная копия в `.rus_patch_backups`. Папка Tempo Launcher при установке Steam-версии не изменяется.

Удаление Steam-версии:

```powershell
.\Uninstall_Russian.bat
```

Подробности: [STEAM_PATCHER.md](STEAM_PATCHER.md).

## Установка Launcher-версии

1. Закройте The Bazaar и Tempo Launcher.
2. Скачайте `TheBazaarRusPatcher.exe` из [последнего релиза](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest).
3. Запустите проверку:

```powershell
.\TheBazaarRusPatcher.exe --check
```

4. Установите перевод:

```powershell
.\TheBazaarRusPatcher.exe --install
```

Для установки без подтверждений:

```powershell
.\TheBazaarRusPatcher.exe --install --yes
```

Откат последнего бэкапа:

```powershell
.\TheBazaarRusPatcher.exe --restore
```

## Что переведено

- интерфейс;
- карточки и названия предметов;
- описания эффектов;
- теги предметов;
- подсказки;
- NPC, магазины, события и задания;
- строки победы, поражения и другие экранные сообщения;
- проблемные остатки турецкого и английского текста.

Отдельное внимание уделено карточкам и интерфейсу, где встречались смешанные строки вроде `Galibiyetler`, `YOSUNLU`, `Ulu Knife`, `Shielded`, неполные описания предметов и англоязычные куски внутри русских описаний.

## Проверка и восстановление

Launcher-версия:

```powershell
.\TheBazaarRusPatcher.exe --check
.\TheBazaarRusPatcher.exe --paths
.\TheBazaarRusPatcher.exe --verify-patch
.\TheBazaarRusPatcher.exe --restore
```

Steam-версия:

```powershell
.\Install_Russian.bat
.\Uninstall_Russian.bat
```

Если после обновления игры перевод пропал или появились старые строки, установите русификатор заново из актуального релиза.

## Обратная связь

Сообщения об ошибках перевода и проблемах патчера можно отправлять на почту:

```text
adeptas3@gmail.com
```

Лучше прикладывать:

- скриншот карточки, подсказки или меню;
- краткое описание ошибки;
- версию игры;
- клиент игры: Steam или Tempo Launcher.

## Важно

Русификатор не связан с Tempo, Tempo Storm, AVY Entertainment или разработчиками The Bazaar.

Исходники репозитория содержат код патчера и таблицы перевода. Steam-архив в Releases содержит готовый payload для установки русификации в Steam-клиент и локальный кэш игры. Перед заменой файлов установщик создает бэкап, чтобы можно было откатить изменения.

Дополнительные документы:

- [DISCLAIMER.md](DISCLAIMER.md)
- [CONTACT_RIGHTS_HOLDER.md](CONTACT_RIGHTS_HOLDER.md)
- [RELEASE_NOTES_STEAM.md](RELEASE_NOTES_STEAM.md)
- [RELEASE_NOTES_LAUNCHER.md](RELEASE_NOTES_LAUNCHER.md)

## Для разработчиков

Требуется .NET SDK 8 или новее.

Сборка launcher-версии:

```powershell
dotnet publish .\TheBazaarRusPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish
```

Сборка Steam-версии:

```powershell
dotnet publish .\TheBazaarRusSteamPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish-steam
```

Актуальная Steam-раздача собирается как zip-архив с `Install_Russian.bat`, `Uninstall_Russian.bat`, `install-rus.ps1` и папкой `payload`.
