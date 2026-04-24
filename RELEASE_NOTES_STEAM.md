# The Bazaar Rus Steam Patcher

Отдельная Steam-сборка русификатора для The Bazaar.

Эта версия предназначена именно для Steam-клиента и его локального кэша.

Особенности Steam-версии:

- отдельный формат патча `key + sourceText -> translatedText`;
- отдельный quality override слой;
- отдельный глоссарий терминов и тегов;
- патч Steam `StreamingAssets` и `AppData\\LocalLow` кэша;
- не затрагивает Tempo Launcher.

Как использовать:

```powershell
.\TheBazaarRusSteamPatcher.exe --check
.\TheBazaarRusSteamPatcher.exe --install --yes
```

Если нужна версия для Tempo Launcher, используйте:

```text
TheBazaarRusPatcher.exe
```
