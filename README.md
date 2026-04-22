# Русификатор The Bazaar

Патчер русской локализации для **The Bazaar**. Поддерживает Steam-версию и Tempo Launcher Beta.

**Скачать последнюю версию:**  
https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest

## Важно

Это неофициальный фанатский перевод. Проект не связан с Tempo, Tempo Storm или разработчиками The Bazaar.

Репозиторий и exe **не распространяют игровые файлы** (`cards.json`, `tooltips.json`, `ru-RU.bytes`, `manifest.json`). Внутри патчера хранится только таблица русских строк перевода. Патчер применяет эти строки к локальным файлам игры на компьютере пользователя и перед изменением делает бэкап.

## Что переведено

- интерфейс;
- карточки и описания эффектов;
- подсказки;
- теги предметов;
- часть NPC, магазинов и событий.

Перевод пока дорабатывается. Если нашли кривую фразу, лучше прислать скриншот карточки или меню.

## Обратная связь

Нашли ошибку в переводе или баг патчера? Пишите на почту:

```text
adeptas3@gmail.com
```

По возможности приложите:

- скриншот карточки, подсказки или меню;
- описание, где встретилась ошибка;
- версию игры;
- какой клиент используется: Steam или Tempo Launcher.

## Установка

1. Полностью закройте игру и лаунчер.
2. Скачайте `TheBazaarRusPatcher.exe` из раздела Releases.
3. Запустите файл.
4. Выберите `Установить русификатор`.
5. После завершения запустите игру заново.

Патчер автоматически ищет:

- общий кэш игры в `AppData\LocalLow`;
- Steam-версию;
- Tempo Launcher Beta.

Перед изменением файлов патчер делает бэкап в папку `.rus_patch_backups`.

## Восстановление

Если нужно откатить изменения, запустите патчер и выберите восстановление бэкапа.

Также можно запустить через командную строку:

```powershell
.\TheBazaarRusPatcher.exe --restore
```

## Команды

Интерактивный режим:

```powershell
.\TheBazaarRusPatcher.exe
```

Установить без меню:

```powershell
.\TheBazaarRusPatcher.exe --install
```

Показать найденные пути:

```powershell
.\TheBazaarRusPatcher.exe --paths
```

Проверить встроенную таблицу перевода:

```powershell
.\TheBazaarRusPatcher.exe --verify-patch
```

## Для GitHub About

Короткое описание:

```text
Русификатор The Bazaar для Steam и Tempo Launcher
```

Topics:

```text
the-bazaar russian-translation localization patcher rusifikator
```

Ссылка для скачивания:

```text
https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest
```

## Текст для поста

```text
Сделал русификатор для The Bazaar.

Переведены:
- интерфейс;
- карточки и описания эффектов;
- подсказки;
- теги предметов;
- часть NPC, магазинов и событий.

Поддерживает Steam и Tempo Launcher Beta.
Патчер сам находит игру, применяет только таблицу перевода к локальным файлам и делает бэкап перед изменениями.
Исходники открыты на GitHub, игровые файлы в репозитории и exe не распространяются.

Скачать:
https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/latest

Если найдёте кривой перевод, присылайте скриншот карточки или меню.

Почта для обратной связи:
adeptas3@gmail.com
```

## Сборка из исходников

Требуется .NET SDK 8 или новее.

```powershell
dotnet publish .\TheBazaarRusPatcher.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true /p:EnableCompressionInSingleFile=true /p:IncludeNativeLibrariesForSelfExtract=true -o .\publish
```

Готовый файл появится здесь:

```text
publish\TheBazaarRusPatcher.exe
```
