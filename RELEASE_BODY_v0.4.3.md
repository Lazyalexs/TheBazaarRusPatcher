# The Bazaar Russian Patcher v0.4.3

Hotfix для Steam-версии: в `v0.4.2` карточки могли остаться на английском, потому что Steam JSON был переведён только по неполному exact-слою.

Что исправлено:
- Steam JSON снова применяет перевод в режиме `exact first -> key fallback`;
- карточки, описания и tooltip-строки снова массово переводятся в `cards.json`;
- сохранён флаг `--strict-exact` / `--exact-only` для частичной безопасной проверки без key fallback;
- launcher-сборка перенесена без изменений.

Файлы релиза:
- `TheBazaarRusSteamPatcher.exe` - новая Steam-сборка;
- `TheBazaarRusPatcher.exe` - launcher-сборка;
- `Patch.zip` - папка `Patch`.

Проверка:
```powershell
.\TheBazaarRusSteamPatcher.exe --check
```

Установка Steam:
```powershell
.\TheBazaarRusSteamPatcher.exe --install --yes
```

Если после старой версии в Steam уже смешались названия карточек, сначала восстановите целостность файлов игры в Steam, затем установите этот релиз.
