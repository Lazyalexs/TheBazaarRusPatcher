# Русификатор The Bazaar

Неофициальный фанатский перевод The Bazaar на русский язык для Steam и Tempo Launcher.

## Скачать свежую версию

**[v0.7.4 — исправление кнопки в меню паузы](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/tag/v0.7.4)**.

| Ваша версия игры | Скачать патчер |
|---|---|
| Steam | [TheBazaarRusPatcher-Steam.exe](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/download/v0.7.4/TheBazaarRusPatcher-Steam.exe) |
| Tempo Launcher | [TheBazaarRusPatcher-Tempo.exe](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases/download/v0.7.4/TheBazaarRusPatcher-Tempo.exe) |

Сведения о составе и изменениях версии — в [описании релиза](docs/releases/v0.7.4.md).

[Все релизы](https://github.com/Lazyalexs/TheBazaarRusPatcher/releases) · [Изменения этой версии](docs/releases/v0.7.4.md) · [Discord: помощь и обратная связь](https://discord.gg/FH8z7D3xe7)

## Состояние перевода

В патч включено 17 299 записей перевода. Версия 0.7.4 сохраняет адаптацию к данным Season 19 из v0.7.3 и исправляет подпись кнопки сдачи в меню паузы на «Сдаться».

**Известные ограничения:**

- Пункт «Русский» может отсутствовать: игра обновляет список доступных языков с сервера, перезаписывая локальное изменение. Повторная установка не гарантирует устранение этой проблемы.
- Обновления игры могут перезаписать изменённые файлы. Служебные DEBUG/шаблонные строки не переводятся как обычный игровой контент.

## Установка

1. Закройте The Bazaar и лаунчер.
2. Скачайте EXE для своего лаунчера из таблицы выше. Устанавливать .NET отдельно не нужно.
3. Запустите патчер и выберите пункт 1 — установку.
4. Запустите игру через лаунчер. Если «Русский» доступен в Settings → Language, выберите его.

Если языка нет или перевод работает частично, сообщите об этом в Discord, приложив скриншот и результат `--check`.

Перед изменением файлов патчер создаёт резервные копии в `.rus_patch_backups/`. Для отката используйте `--restore`.

## Команды

```powershell
.\TheBazaarRusPatcher-Steam.exe                  # интерактивное меню
.\TheBazaarRusPatcher-Steam.exe --install --yes  # установка без подтверждения
.\TheBazaarRusPatcher-Steam.exe --check          # проверка без изменения файлов
.\TheBazaarRusPatcher-Steam.exe --paths          # найденные пути
.\TheBazaarRusPatcher-Steam.exe --restore        # восстановление резервной копии
```

Для Tempo замените имя файла на `TheBazaarRusPatcher-Tempo.exe`. Имя EXE определяет целевой лаунчер. Патчер также работает с общим кэшем игры: `--game-path` не является режимом изолированного тестирования.

## Структура репозитория

| Путь | Назначение |
|---|---|
| `Program.cs` | Установка, проверка и восстановление файлов |
| `Patch/` | Ресурсы переводов, встраиваемые в EXE |
| `tools-extract/` | Извлечение оригиналов, подготовка и проверка переводов |
| `docs/releases/` | Архив описаний релизов |
| `docs/audits/` | Технические отчёты об обновлениях |
| `build.ps1` | Сборка EXE для Steam и Tempo |

## Для разработчиков

Требуется .NET SDK 8+. Сборка:

```powershell
.\build.ps1
```

Результат: `dist/TheBazaarRusPatcher-Steam.exe` и `dist/TheBazaarRusPatcher-Tempo.exe`. Скрипт пересоздаёт выходные каталоги сборки; не храните в них единственные копии файлов.

Перевод встроен в исполняемый файл. Изменение JSON в репозитории само по себе не обновляет уже скачанный патчер. Автоматическая проверка параметров строк не заменяет смысловую вычитку и проверку интерфейса в игре.

## Обратная связь и права

[Discord](https://discord.gg/FH8z7D3xe7) · Email: `adeptas3@gmail.com`.

Для сообщения об ошибке приложите скриншот, версию игры и патчера, используемый лаунчер и вывод `--check`. Не публикуйте полные игровые логи без удаления данных авторизации.

Проект не связан с Tempo, Tempo Storm, AVY Entertainment или разработчиками The Bazaar.

[Отказ от ответственности](DISCLAIMER.md) · [Правообладателям](CONTACT_RIGHTS_HOLDER.md) · [Лицензия](LICENSE)
