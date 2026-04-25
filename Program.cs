using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Data.Sqlite;
using Microsoft.Win32;

#if STEAM_ONLY
const string AppName = "The Bazaar Russian Steam Patcher";
const string PatchResourceName = "Patch/steam-translation-patch.json";
const string OverridePatchResourceName = "Patch/steam-quality-overrides.json";
const string GlossaryResourceName = "Patch/steam-glossary.json";
#else
const string AppName = "The Bazaar Russian Patcher";
const string PatchResourceName = "Patch/translation-patch.json";
#endif
const string BackupDirName = ".rus_patch_backups";
string[] dataJsonFileNames =
[
    "cards.json",
    "tooltips.json",
    "challenges.json",
    "gamemodes.json",
    "levelups.json",
    "seasons.json",
    "monsters.json",
    "maintenance.json"
];

Console.OutputEncoding = System.Text.Encoding.UTF8;
Console.Title = AppName;

var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
var localLow = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
    "AppData",
    "LocalLow");

var cacheRoot = Path.Combine(localLow, "Tempo Storm", "The Bazaar", "prod", "cache");
var launcherStreamingAssets = Path.Combine(
    appData,
    "Tempo Launcher - Beta",
    "game",
    "buildx64",
    "TheBazaar_Data",
    "StreamingAssets");

var patch = LoadPatch();
#if STEAM_ONLY
var glossary = LoadGlossary();
patch = LoadPatch(OverridePatchResourceName, patch);
patch = PatchCatalog.Normalize(patch, glossary.Normalize);
#endif
var steamStreamingAssets = FindSteamStreamingAssets().ToList();
#if STEAM_ONLY
var steamOnly = true;
#else
var steamOnly = args.Any(a => a.Equals("--steam-only", StringComparison.OrdinalIgnoreCase));
#endif
var assumeYes = args.Any(a => a.Equals("--yes", StringComparison.OrdinalIgnoreCase));
#if STEAM_ONLY
var strictExact = args.Any(a =>
    a.Equals("--strict-exact", StringComparison.OrdinalIgnoreCase)
    || a.Equals("--exact-only", StringComparison.OrdinalIgnoreCase));
#else
var strictExact = false;
#endif
var updateManifests = args.Any(a => a.Equals("--update-manifest", StringComparison.OrdinalIgnoreCase));

if (args.Any(a => a.Equals("--restore", StringComparison.OrdinalIgnoreCase)))
{
    RestoreAll();
    return;
}

if (args.Any(a => a.Equals("--paths", StringComparison.OrdinalIgnoreCase)))
{
    PrintTargets();
    return;
}

if (args.Any(a => a.Equals("--verify-patch", StringComparison.OrdinalIgnoreCase)))
{
    VerifyPatch();
    return;
}

if (args.Any(a => a.Equals("--check", StringComparison.OrdinalIgnoreCase)))
{
    CheckAll();
    return;
}

if (args.Any(a => a.Equals("--install", StringComparison.OrdinalIgnoreCase)))
{
    InstallAll();
    return;
}

while (true)
{
    Console.Clear();
    Console.WriteLine(AppName);
    Console.WriteLine();
    Console.WriteLine("1. Установить русификатор");
    Console.WriteLine("2. Восстановить последний бэкап");
    Console.WriteLine("3. Показать найденные пути");
    Console.WriteLine("4. Проверить встроенный патч");
    Console.WriteLine("5. Проверить изменения без установки");
    Console.WriteLine("0. Выход");
    Console.WriteLine();
    Console.Write("Выбор: ");

    switch (Console.ReadLine()?.Trim())
    {
        case "1":
            InstallAll();
            Pause();
            break;
        case "2":
            RestoreAll();
            Pause();
            break;
        case "3":
            PrintTargets();
            Pause();
            break;
        case "4":
            VerifyPatch();
            Pause();
            break;
        case "5":
            CheckAll();
            Pause();
            break;
        case "0":
            return;
    }
}

void CheckAll()
{
    InstallOrCheck(dryRun: true);
}

void InstallAll()
{
    if (!ConfirmDisclaimer())
    {
        Console.WriteLine("Установка отменена.");
        return;
    }

    InstallOrCheck(dryRun: false);
}

void InstallOrCheck(bool dryRun)
{
    var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss");
    var targets = GetInstallTargets().Where(t => Directory.Exists(t.Root)).ToList();

    if (targets.Count == 0)
    {
        Console.WriteLine("Не найдено ни одного пути для установки.");
        return;
    }

    Console.WriteLine();
    Console.WriteLine(dryRun ? "Проверка без установки..." : "Установка русификатора...");
    Console.WriteLine($"Строк перевода в патче: {patch.TranslationCount:N0}");

    foreach (var target in targets)
    {
        Console.WriteLine();
        Console.WriteLine($"[{target.Name}] {target.Root}");

        if (target.Kind == TargetKind.Cache)
        {
            PatchCache(target.Root, stamp, dryRun);
        }
        else
        {
            PatchStreamingAssets(target.Root, stamp, dryRun);
        }
    }

    Console.WriteLine();
    Console.WriteLine(dryRun
        ? "Проверка завершена. Файлы не изменялись."
        : "Готово. Полностью закройте игру и лаунчер, затем запустите заново.");
}

bool ConfirmDisclaimer()
{
    if (assumeYes)
    {
        return true;
    }

    Console.WriteLine();
    Console.WriteLine("ВНИМАНИЕ");
    Console.WriteLine("Это неофициальный фанатский перевод.");
    Console.WriteLine("Проект не связан с разработчиками The Bazaar.");
    Console.WriteLine("Патчер изменяет локальные файлы игры на вашем компьютере.");
    Console.WriteLine("Используйте на свой риск. Перед изменениями будет создан бэкап.");
    Console.WriteLine();
    Console.Write("Продолжить установку? Введите YES: ");

    return string.Equals(Console.ReadLine()?.Trim(), "YES", StringComparison.Ordinal);
}

void PatchCache(string root, string stamp, bool dryRun)
{
    PatchTranslationDatabases(root, stamp, dryRun);
    PatchDataJsonFiles(root, stamp, dryRun);

    if (updateManifests)
    {
        UpdateManifestIfExists(Path.Combine(root, "manifest.json"), root, dryRun);
        UpdateManifestIfExists(Path.Combine(root, "translations", "manifest.json"), Path.Combine(root, "translations"), dryRun);
    }
    else
    {
        ReportManifestPreservedIfExists(root, Path.Combine(root, "manifest.json"));
        ReportManifestPreservedIfExists(root, Path.Combine(root, "translations", "manifest.json"));
    }
}

void PatchStreamingAssets(string root, string stamp, bool dryRun)
{
    PatchDataJsonFiles(root, stamp, dryRun);
    UpdateManifestIfExists(Path.Combine(root, "manifest.json"), root, dryRun);
}

void PatchDataJsonFiles(string root, string stamp, bool dryRun)
{
    var paths = EnumerateDataJsonFiles(root).ToList();
    if (paths.Count == 0)
    {
        Console.WriteLine("  *.json: не найден.");
        return;
    }

    foreach (var path in paths)
    {
        PatchJsonFile(root, path, stamp, dryRun);
    }
}

IEnumerable<string> EnumerateDataJsonFiles(string root)
{
    if (!Directory.Exists(root))
    {
        yield break;
    }

    var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    foreach (var fileName in dataJsonFileNames)
    {
        var path = Path.Combine(root, fileName);
        if (File.Exists(path) && seen.Add(Path.GetFullPath(path)))
        {
            yield return path;
        }
    }

    foreach (var path in Directory.EnumerateFiles(root, "*.json", SearchOption.TopDirectoryOnly)
        .OrderBy(Path.GetFileName, StringComparer.OrdinalIgnoreCase))
    {
        if (string.Equals(Path.GetFileName(path), "manifest.json", StringComparison.OrdinalIgnoreCase))
        {
            continue;
        }

        if (seen.Add(Path.GetFullPath(path)))
        {
            yield return path;
        }
    }
}

void ReportManifestPreservedIfExists(string root, string manifestPath)
{
    if (!File.Exists(manifestPath))
    {
        return;
    }

    var relative = Path.GetRelativePath(root, manifestPath).Replace('\\', '/');
    Console.WriteLine($"  {relative}: оставлен без изменений (CDN ETag)");
}

void PatchTranslationDatabases(string root, string stamp, bool dryRun)
{
    var translationsDir = Path.Combine(root, "translations");
    if (!Directory.Exists(translationsDir))
    {
#if STEAM_ONLY
        if (dryRun)
        {
            Console.WriteLine("  translations: будет создана папка.");
            Console.WriteLine($"  ru-RU.bytes: будет создана база перевода ({patch.KeyTranslations.Count:N0} строк)");
            return;
        }

        Directory.CreateDirectory(translationsDir);
#else
        Console.WriteLine("  translations not found.");
        return;
#endif
    }

#if STEAM_ONLY
    var ruDbPath = Path.Combine(translationsDir, "ru-RU.bytes");
    var willCreateRuDb = EnsureSteamTranslationDatabase(root, ruDbPath, stamp, dryRun);
    var dbFiles = Directory.EnumerateFiles(translationsDir, "*.bytes", SearchOption.TopDirectoryOnly)
        .OrderBy(path => string.Equals(Path.GetFileName(path), "ru-RU.bytes", StringComparison.OrdinalIgnoreCase) ? 0 : 1)
        .ThenBy(Path.GetFileName, StringComparer.OrdinalIgnoreCase)
        .ToList();
#else
    var dbFiles = Directory.EnumerateFiles(translationsDir, "*.bytes", SearchOption.TopDirectoryOnly)
        .OrderBy(Path.GetFileName, StringComparer.OrdinalIgnoreCase)
        .ToList();
#endif

    if (dbFiles.Count == 0)
    {
#if STEAM_ONLY
        if (!willCreateRuDb)
        {
            Console.WriteLine("  translations/*.bytes not found.");
        }
#else
        Console.WriteLine("  translations/*.bytes not found.");
#endif
        return;
    }

    foreach (var dbPath in dbFiles)
    {
        var fileName = Path.GetFileName(dbPath);
        if (!ValidateTranslationDatabase(dbPath, out var reason))
        {
            Console.WriteLine($"  {fileName}: skipped ({reason})");
            continue;
        }

        if (!dryRun)
        {
            BackupExistingFile(root, dbPath, stamp);
        }

        var changed = PatchTranslationDatabase(dbPath, dryRun);
        Console.WriteLine(dryRun
            ? $"  {fileName}: will update strings {changed:N0}"
            : $"  {fileName}: updated strings {changed:N0}");
    }
}

#if STEAM_ONLY
bool EnsureSteamTranslationDatabase(string root, string ruDbPath, string stamp, bool dryRun)
{
    if (File.Exists(ruDbPath))
    {
        return false;
    }

    if (dryRun)
    {
        Console.WriteLine($"  ru-RU.bytes: будет создана база перевода ({patch.KeyTranslations.Count:N0} строк)");
        return true;
    }

    BackupExistingFile(root, ruDbPath, stamp);
    CreateTranslationDatabase(ruDbPath);
    Console.WriteLine("  ru-RU.bytes: создана база перевода");
    return true;
}

void CreateTranslationDatabase(string dbPath)
{
    Directory.CreateDirectory(Path.GetDirectoryName(dbPath)!);

    var connectionString = new SqliteConnectionStringBuilder
    {
        DataSource = dbPath,
        Mode = SqliteOpenMode.ReadWriteCreate
    }.ToString();

    using var connection = new SqliteConnection(connectionString);
    connection.Open();

    using var command = connection.CreateCommand();
    command.CommandText = """
        CREATE TABLE translation
        (
            hash TEXT PRIMARY KEY,
            text TEXT NOT NULL
        ) WITHOUT ROWID
        """;
    command.ExecuteNonQuery();
}
#endif

void PatchJsonFile(string root, string path, string stamp, bool dryRun)
{
    var fileName = Path.GetFileName(path);
    if (!ValidatePatchableJson(path, out var reason))
    {
        Console.WriteLine($"  {fileName}: пропущено ({reason})");
        return;
    }

    if (!dryRun)
    {
        BackupExistingFile(root, path, stamp);
    }

    var result = PatchJsonTextByKey(path, dryRun, skipAmbiguousKeys: steamOnly);
    Console.WriteLine(dryRun
        ? $"  {fileName}: будет обновлено текстов {result.Changed:N0}"
        : $"  {fileName}: обновлено текстов {result.Changed:N0}");

    if (result.SkippedAmbiguous > 0)
    {
        Console.WriteLine($"  {fileName}: пропущено неоднозначных текстов {result.SkippedAmbiguous:N0}");
    }
}

int PatchTranslationDatabase(string dbPath, bool dryRun)
{
#if STEAM_ONLY
    if (patch.KeyTranslations.Count == 0 && glossary.IsEmpty)
#else
    if (patch.KeyTranslations.Count == 0)
#endif
    {
        return 0;
    }

    var changed = 0;
    var connectionString = new SqliteConnectionStringBuilder
    {
        DataSource = dbPath,
        Mode = SqliteOpenMode.ReadWrite
    }.ToString();

    using var connection = new SqliteConnection(connectionString);
    connection.Open();

    if (dryRun)
    {
        using var select = connection.CreateCommand();
        select.CommandText = "SELECT text FROM translation WHERE hash = $hash";
        var selectHash = select.Parameters.Add("$hash", SqliteType.Text);

        foreach (var (hash, text) in patch.KeyTranslations)
        {
            selectHash.Value = hash;
            var existing = select.ExecuteScalar() as string;
            if (existing != text)
            {
                changed++;
            }
        }

#if STEAM_ONLY
        {
            using var glossaryScan = connection.CreateCommand();
            glossaryScan.CommandText = "SELECT hash, text FROM translation";
            using var glossaryReader = glossaryScan.ExecuteReader();
            while (glossaryReader.Read())
            {
                var existing = glossaryReader.IsDBNull(1) ? "" : glossaryReader.GetString(1);
                var normalized = glossary.Normalize(existing);
                if (normalized != existing)
                {
                    changed++;
                }
            }
        }
#endif

        return changed;
    }

    using var transaction = connection.BeginTransaction();
    using var command = connection.CreateCommand();
    command.Transaction = transaction;
    command.CommandText = """
        INSERT INTO translation(hash, text)
        VALUES ($hash, $text)
        ON CONFLICT(hash) DO UPDATE SET text = excluded.text
        WHERE translation.text <> excluded.text
        """;
    var hashParam = command.Parameters.Add("$hash", SqliteType.Text);
    var textParam = command.Parameters.Add("$text", SqliteType.Text);

    foreach (var (hash, text) in patch.KeyTranslations)
    {
        hashParam.Value = hash;
        textParam.Value = text;
        changed += command.ExecuteNonQuery();
    }

#if STEAM_ONLY
    {
        using var glossaryScan = connection.CreateCommand();
        glossaryScan.Transaction = transaction;
        glossaryScan.CommandText = "SELECT hash, text FROM translation";

        using var update = connection.CreateCommand();
        update.Transaction = transaction;
        update.CommandText = """
            UPDATE translation
            SET text = $text
            WHERE hash = $hash AND text <> $text
            """;
        var updateHash = update.Parameters.Add("$hash", SqliteType.Text);
        var updateText = update.Parameters.Add("$text", SqliteType.Text);

        using var glossaryReader = glossaryScan.ExecuteReader();
        while (glossaryReader.Read())
        {
            var hash = glossaryReader.GetString(0);
            var existing = glossaryReader.IsDBNull(1) ? "" : glossaryReader.GetString(1);
            var normalized = glossary.Normalize(existing);
            if (normalized == existing)
            {
                continue;
            }

            updateHash.Value = hash;
            updateText.Value = normalized;
            changed += update.ExecuteNonQuery();
        }
    }
#endif

    transaction.Commit();
    return changed;
}

JsonPatchResult PatchJsonTextByKey(string path, bool dryRun, bool skipAmbiguousKeys)
{
    var json = File.ReadAllText(path);
    var root = JsonNode.Parse(json);
    if (root is null)
    {
        return new JsonPatchResult(0, 0);
    }

    var ambiguousKeys = skipAmbiguousKeys && !patch.HasExactTranslations
        ? FindAmbiguousPatchKeys(root)
        : new HashSet<string>();
    var changed = 0;
    var skippedAmbiguous = 0;
    PatchNode(root, ambiguousKeys, ref changed, ref skippedAmbiguous);

    if (changed > 0)
    {
        if (!dryRun)
        {
            File.WriteAllText(path, root.ToJsonString(new JsonSerializerOptions
            {
                WriteIndented = false,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            }));
        }
    }

    return new JsonPatchResult(changed, skippedAmbiguous);
}

void PatchNode(JsonNode node, HashSet<string> ambiguousKeys, ref int changed, ref int skippedAmbiguous)
{
    if (node is JsonObject obj)
    {
        if (IsKeyTextNode(obj))
        {
            var keyNode = obj["Key"]!;
            var textNode = obj["Text"]!;
            var key = keyNode.GetValue<string>();
            var current = textNode.GetValue<string>();

            var hasTranslation = strictExact && patch.HasExactTranslations
                ? patch.TryTranslateExact(key, current, out var translated)
                : patch.TryTranslate(key, current, out translated);

            if (hasTranslation && translated != current)
            {
                if (ambiguousKeys.Contains(key))
                {
                    skippedAmbiguous++;
                }
                else
                {
                    obj["Text"] = translated;
                    changed++;
                }
            }
        }
        else if (IsTooltipTextNode(obj))
        {
            PatchTooltipNode(obj, ref changed);
        }

        foreach (var child in obj.ToList())
        {
            if (child.Value is not null)
            {
                PatchNode(child.Value, ambiguousKeys, ref changed, ref skippedAmbiguous);
            }
        }
    }
    else if (node is JsonArray array)
    {
        foreach (var child in array)
        {
            if (child is not null)
            {
                PatchNode(child, ambiguousKeys, ref changed, ref skippedAmbiguous);
            }
        }
    }
}

void PatchTooltipNode(JsonObject obj, ref int changed)
{
    var id = obj["Id"]!.GetValue<string>();
    PatchTooltipProperty(obj, id, "Tag", ref changed);
    PatchTooltipProperty(obj, id, "Keyword", ref changed);
}

void PatchTooltipProperty(JsonObject obj, string id, string propertyName, ref int changed)
{
    if (!obj.TryGetPropertyValue(propertyName, out var textNode)
        || textNode?.GetValueKind() != JsonValueKind.String)
    {
        return;
    }

    var current = textNode.GetValue<string>();
    if (string.IsNullOrEmpty(current))
    {
        return;
    }

    var hasTranslation = patch.TryTranslate(id, current, out var translated);
#if STEAM_ONLY
    if (!hasTranslation)
    {
        translated = glossary.Normalize(current);
        hasTranslation = translated != current;
    }
#endif

    if (hasTranslation && translated != current)
    {
        obj[propertyName] = translated;
        changed++;
    }
}

bool IsKeyTextNode(JsonObject obj)
{
    return obj.TryGetPropertyValue("Key", out var keyNode)
        && obj.TryGetPropertyValue("Text", out var textNode)
        && keyNode?.GetValueKind() == JsonValueKind.String
        && textNode?.GetValueKind() == JsonValueKind.String;
}

bool IsTooltipTextNode(JsonObject obj)
{
    return obj.TryGetPropertyValue("Id", out var idNode)
        && idNode?.GetValueKind() == JsonValueKind.String
        && (IsStringProperty(obj, "Tag") || IsStringProperty(obj, "Keyword"));
}

bool IsStringProperty(JsonObject obj, string propertyName)
{
    return obj.TryGetPropertyValue(propertyName, out var valueNode)
        && valueNode?.GetValueKind() == JsonValueKind.String;
}

HashSet<string> FindAmbiguousPatchKeys(JsonNode root)
{
    var textsByKey = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
    CollectKeyTexts(root, textsByKey);

    return textsByKey
        .Where(pair => patch.KeyTranslations.ContainsKey(pair.Key) && pair.Value.Count > 1)
        .Select(pair => pair.Key)
        .ToHashSet(StringComparer.Ordinal);
}

void CollectKeyTexts(JsonNode? node, Dictionary<string, HashSet<string>> textsByKey)
{
    if (node is JsonObject obj)
    {
        if (obj.TryGetPropertyValue("Key", out var keyNode)
            && obj.TryGetPropertyValue("Text", out var textNode)
            && keyNode?.GetValueKind() == JsonValueKind.String
            && textNode?.GetValueKind() == JsonValueKind.String)
        {
            var key = keyNode.GetValue<string>();
            var text = textNode.GetValue<string>();
            if (!textsByKey.TryGetValue(key, out var texts))
            {
                texts = new HashSet<string>(StringComparer.Ordinal);
                textsByKey[key] = texts;
            }

            texts.Add(text);
        }

        foreach (var child in obj)
        {
            CollectKeyTexts(child.Value, textsByKey);
        }
    }
    else if (node is JsonArray array)
    {
        foreach (var child in array)
        {
            CollectKeyTexts(child, textsByKey);
        }
    }
}

bool ValidateTranslationDatabase(string dbPath, out string reason)
{
    try
    {
        var connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = dbPath,
            Mode = SqliteOpenMode.ReadOnly
        }.ToString();

        using var connection = new SqliteConnection(connectionString);
        connection.Open();

        using var table = connection.CreateCommand();
        table.CommandText = "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'translation'";
        if (Convert.ToInt32(table.ExecuteScalar()) != 1)
        {
            reason = "нет таблицы translation";
            return false;
        }

        using var columns = connection.CreateCommand();
        columns.CommandText = "PRAGMA table_info(translation)";
        using var reader = columns.ExecuteReader();
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        while (reader.Read())
        {
            names.Add(reader.GetString(1));
        }

        if (!names.Contains("hash") || !names.Contains("text"))
        {
            reason = "неожиданная структура таблицы translation";
            return false;
        }

        reason = "";
        return true;
    }
    catch (Exception ex)
    {
        reason = ex.Message;
        return false;
    }
}

bool ValidatePatchableJson(string path, out string reason)
{
    try
    {
        var root = JsonNode.Parse(File.ReadAllText(path));
        if (root is not JsonObject obj)
        {
            reason = "ожидался JSON-объект верхнего уровня";
            return false;
        }

        if (!obj.Any(kvp => System.Text.RegularExpressions.Regex.IsMatch(kvp.Key, @"^\d+\.\d+")))
        {
            reason = "версия данных не проверена";
            return false;
        }

        var textNodeCount = 0;
        CountTextNodes(root, ref textNodeCount);
        if (textNodeCount == 0)
        {
            reason = "не найдены переводимые узлы Key/Text или Id/Tag";
            return false;
        }

        reason = "";
        return true;
    }
    catch (Exception ex)
    {
        reason = ex.Message;
        return false;
    }
}

void CountTextNodes(JsonNode? node, ref int count)
{
    if (node is JsonObject obj)
    {
        if (IsKeyTextNode(obj))
        {
            count++;
        }
        else if (IsTooltipTextNode(obj))
        {
            count++;
        }

        foreach (var child in obj)
        {
            CountTextNodes(child.Value, ref count);
        }
    }
    else if (node is JsonArray array)
    {
        foreach (var child in array)
        {
            CountTextNodes(child, ref count);
        }
    }
}

void UpdateManifestIfExists(string manifestPath, string root, bool dryRun)
{
    if (!File.Exists(manifestPath))
    {
        return;
    }

    JsonNode? manifest;
    try
    {
        manifest = JsonNode.Parse(File.ReadAllText(manifestPath));
    }
    catch
    {
        Console.WriteLine($"  {Path.GetFileName(manifestPath)}: не удалось прочитать.");
        return;
    }

    if (manifest is null)
    {
        return;
    }

    var changed = false;
    foreach (var file in Directory.EnumerateFiles(root, "*", SearchOption.TopDirectoryOnly))
    {
        var name = Path.GetFileName(file);
        var md5 = ComputeMd5(file);
        UpdateManifestNode(manifest, name, md5, ref changed);

        var nameWithoutExtension = Path.GetFileNameWithoutExtension(name);
        if (!string.Equals(name, nameWithoutExtension, StringComparison.Ordinal))
        {
            UpdateManifestNode(manifest, nameWithoutExtension, md5, ref changed);
        }
    }

    if (changed)
    {
        if (!dryRun)
        {
            File.WriteAllText(manifestPath, manifest.ToJsonString(new JsonSerializerOptions
            {
                WriteIndented = false,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            }));
        }

        Console.WriteLine(dryRun
            ? $"  {Path.GetFileName(manifestPath)}: будут обновлены хэши"
            : $"  {Path.GetFileName(manifestPath)}: обновлены хэши.");
    }
}

void UpdateManifestNode(JsonNode node, string fileName, string md5, ref bool changed)
{
    if (node is JsonObject obj)
    {
        if (obj.TryGetPropertyValue(fileName, out var byName) && byName is JsonObject byNameObj)
        {
            byNameObj["ETag"] = md5;
            changed = true;
        }

        if (obj.TryGetPropertyValue("Name", out var nameNode)
            && nameNode?.GetValueKind() == JsonValueKind.String
            && nameNode.GetValue<string>().Equals(fileName, StringComparison.OrdinalIgnoreCase))
        {
            obj["ETag"] = md5;
            changed = true;
        }

        foreach (var child in obj)
        {
            if (child.Value is not null)
            {
                UpdateManifestNode(child.Value, fileName, md5, ref changed);
            }
        }
    }
    else if (node is JsonArray array)
    {
        foreach (var child in array)
        {
            if (child is not null)
            {
                UpdateManifestNode(child, fileName, md5, ref changed);
            }
        }
    }
}

void RestoreAll()
{
    var targets = GetInstallTargets().Where(t => Directory.Exists(t.Root)).ToList();

    if (targets.Count == 0)
    {
        Console.WriteLine("Не найдено ни одного пути для восстановления.");
        return;
    }

    Console.WriteLine();
    Console.WriteLine("Восстановление последнего бэкапа...");

    foreach (var target in targets)
    {
        var backupRoot = Path.Combine(target.Root, BackupDirName);
        if (!Directory.Exists(backupRoot))
        {
            Console.WriteLine($"[{target.Name}] бэкапов нет.");
            continue;
        }

        var latest = Directory.GetDirectories(backupRoot)
            .OrderByDescending(Path.GetFileName)
            .FirstOrDefault();

        if (latest is null)
        {
            Console.WriteLine($"[{target.Name}] бэкапов нет.");
            continue;
        }

        Console.WriteLine($"[{target.Name}] {Path.GetFileName(latest)}");

        foreach (var backupFile in Directory.EnumerateFiles(latest, "*", SearchOption.AllDirectories))
        {
            var relative = Path.GetRelativePath(latest, backupFile);
            var destination = Path.Combine(target.Root, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            File.Copy(backupFile, destination, overwrite: true);
            Console.WriteLine($"  RESTORE {relative}");
        }
    }

    Console.WriteLine();
    Console.WriteLine("Восстановление завершено.");
}

void PrintTargets()
{
    Console.WriteLine();
    foreach (var target in GetInstallTargets())
    {
        var state = Directory.Exists(target.Root) ? "найдено" : "не найдено";
        Console.WriteLine($"{target.Name}: {state}");
        Console.WriteLine(target.Root);
        Console.WriteLine();
    }
}

void VerifyPatch()
{
    Console.WriteLine();
    Console.WriteLine("Проверка встроенного патча:");
    Console.WriteLine($"Название: {patch.Name}");
    Console.WriteLine($"Язык: {patch.Language}");
    Console.WriteLine($"Формат: {patch.Format}");
    Console.WriteLine($"Строк перевода: {patch.TranslationCount:N0}");
}

IEnumerable<InstallTarget> GetInstallTargets()
{
    var cacheRoots = FindCacheRoots().ToList();
    if (cacheRoots.Count == 0)
    {
        cacheRoots.Add(cacheRoot);
    }

    foreach (var cachePath in cacheRoots)
    {
        var name = string.Equals(cachePath, cacheRoot, StringComparison.OrdinalIgnoreCase)
            ? "Общий кэш LocalLow"
            : "Кэш LocalLow";
        yield return new InstallTarget(name, cachePath, TargetKind.Cache);
    }

    if (!steamOnly && Directory.Exists(launcherStreamingAssets))
    {
        yield return new InstallTarget("Tempo Launcher", launcherStreamingAssets, TargetKind.StreamingAssets);
    }

    foreach (var steamPath in steamStreamingAssets)
    {
        yield return new InstallTarget("Steam", steamPath, TargetKind.StreamingAssets);
    }
}

IEnumerable<string> FindCacheRoots()
{
    var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    if (Directory.Exists(cacheRoot) && seen.Add(Path.GetFullPath(cacheRoot)))
    {
        yield return cacheRoot;
    }

    var bazaarLocalLowRoot = Path.Combine(localLow, "Tempo Storm", "The Bazaar");
    if (!Directory.Exists(bazaarLocalLowRoot))
    {
        yield break;
    }

    List<string> candidates;
    try
    {
        candidates = Directory.EnumerateDirectories(bazaarLocalLowRoot, "cache", SearchOption.AllDirectories)
            .ToList();
    }
    catch
    {
        yield break;
    }

    foreach (var candidate in candidates.OrderBy(path => path, StringComparer.OrdinalIgnoreCase))
    {
        if (IsIgnoredCachePath(candidate) || !LooksLikeGameCache(candidate))
        {
            continue;
        }

        var fullPath = Path.GetFullPath(candidate);
        if (seen.Add(fullPath))
        {
            yield return fullPath;
        }
    }
}

bool LooksLikeGameCache(string path)
{
    return Directory.Exists(path)
        && (File.Exists(Path.Combine(path, "manifest.json"))
            || File.Exists(Path.Combine(path, "cards.json"))
            || Directory.Exists(Path.Combine(path, "translations")));
}

bool IsIgnoredCachePath(string path)
{
    var normalized = path.Replace('/', Path.DirectorySeparatorChar);
    return normalized.Contains($"{Path.DirectorySeparatorChar}{BackupDirName}{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)
        || normalized.Contains($"{Path.DirectorySeparatorChar}backup_before", StringComparison.OrdinalIgnoreCase)
        || normalized.Contains($"{Path.DirectorySeparatorChar}ru_work{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase);
}

void BackupExistingFile(string root, string destination, string stamp)
{
    if (!File.Exists(destination))
    {
        return;
    }

    var relative = Path.GetRelativePath(root, destination);
    var backup = Path.Combine(root, BackupDirName, stamp, relative);
    Directory.CreateDirectory(Path.GetDirectoryName(backup)!);

    if (!File.Exists(backup))
    {
        File.Copy(destination, backup, overwrite: false);
    }
}

PatchCatalog LoadPatch(string resourceName = PatchResourceName, PatchCatalog? basePatch = null)
{
    using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName)
        ?? throw new InvalidOperationException($"Patch resource not found: {resourceName}");

    using var document = JsonDocument.Parse(stream);
    var root = document.RootElement;
    var format = root.GetProperty("format").GetInt32();
    var name = root.GetProperty("name").GetString() ?? "Translation Patch";
    var language = root.GetProperty("language").GetString() ?? "ru-RU";

    if (format == 1)
    {
        var translations = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var property in root.GetProperty("translations").EnumerateObject())
        {
            translations[property.Name] = property.Value.GetString() ?? "";
        }

        if (translations.Count == 0)
        {
            throw new InvalidOperationException("Translation patch is empty.");
        }

        var patch = PatchCatalog.FromKeyTranslations(format, name, language, translations);
        return basePatch is null ? patch : PatchCatalog.Merge(basePatch, patch);
    }

    if (format == 2)
    {
        var keyTranslations = new Dictionary<string, string>(StringComparer.Ordinal);
        if (root.TryGetProperty("keyTranslations", out var keyTranslationsNode))
        {
            foreach (var property in keyTranslationsNode.EnumerateObject())
            {
                keyTranslations[property.Name] = property.Value.GetString() ?? "";
            }
        }

        var translations = new Dictionary<(string Key, string SourceText), string>();
        foreach (var item in root.GetProperty("translations").EnumerateArray())
        {
            var key = item.GetProperty("key").GetString();
            var sourceText = item.GetProperty("sourceText").GetString();
            var translatedText = item.GetProperty("translatedText").GetString();
            if (string.IsNullOrEmpty(key) || sourceText is null || translatedText is null)
            {
                continue;
            }

            translations[(key, sourceText)] = translatedText;
        }

        if (translations.Count == 0 && keyTranslations.Count == 0)
        {
            throw new InvalidOperationException("Translation patch is empty.");
        }

        var patch = PatchCatalog.FromExactTranslations(format, name, language, keyTranslations, translations);
        return basePatch is null ? patch : PatchCatalog.Merge(basePatch, patch);
    }

    throw new InvalidOperationException($"Unsupported patch format: {format}");
}

#if STEAM_ONLY
GlossaryCatalog LoadGlossary()
{
    using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(GlossaryResourceName)
        ?? throw new InvalidOperationException($"Glossary resource not found: {GlossaryResourceName}");

    using var document = JsonDocument.Parse(stream);
    var replacements = new List<KeyValuePair<string, string>>();

    if (document.RootElement.TryGetProperty("replacements", out var replacementsNode))
    {
        if (replacementsNode.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in replacementsNode.EnumerateObject())
            {
                var from = property.Name;
                var to = property.Value.GetString() ?? "";
                if (!string.IsNullOrEmpty(from) && !string.IsNullOrEmpty(to))
                {
                    replacements.Add(new KeyValuePair<string, string>(from, to));
                }
            }
        }
        else if (replacementsNode.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in replacementsNode.EnumerateArray())
            {
                var from = item.GetProperty("from").GetString() ?? "";
                var to = item.GetProperty("to").GetString() ?? "";
                if (!string.IsNullOrEmpty(from) && !string.IsNullOrEmpty(to))
                {
                    replacements.Add(new KeyValuePair<string, string>(from, to));
                }
            }
        }
    }

    if (replacements.Count == 0)
    {
        throw new InvalidOperationException("Glossary replacements are empty.");
    }

    return new GlossaryCatalog(replacements);
}
#endif

string ComputeMd5(string path)
{
    using var md5 = MD5.Create();
    using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
    return Convert.ToHexString(md5.ComputeHash(stream)).ToLowerInvariant();
}

IEnumerable<string> FindSteamStreamingAssets()
{
    foreach (var library in FindSteamLibraries().Distinct(StringComparer.OrdinalIgnoreCase))
    {
        var candidate = Path.Combine(
            library,
            "steamapps",
            "common",
            "The Bazaar",
            "TheBazaar_Data",
            "StreamingAssets");

        if (Directory.Exists(candidate))
        {
            yield return candidate;
        }
    }
}

IEnumerable<string> FindSteamLibraries()
{
    var steamPath = GetSteamPathFromRegistry();
    if (!string.IsNullOrWhiteSpace(steamPath))
    {
        yield return steamPath;

        var libraryFolders = Path.Combine(steamPath, "steamapps", "libraryfolders.vdf");
        if (File.Exists(libraryFolders))
        {
            foreach (var path in ParseSteamLibraryFolders(libraryFolders))
            {
                yield return path;
            }
        }
    }

    foreach (var drive in DriveInfo.GetDrives().Where(d => d.IsReady))
    {
        foreach (var candidate in new[]
        {
            Path.Combine(drive.RootDirectory.FullName, "SteamLibrary"),
            Path.Combine(drive.RootDirectory.FullName, "Program Files (x86)", "Steam"),
            Path.Combine(drive.RootDirectory.FullName, "Program Files", "Steam")
        })
        {
            if (Directory.Exists(Path.Combine(candidate, "steamapps")))
            {
                yield return candidate;
            }
        }
    }
}

string? GetSteamPathFromRegistry()
{
    foreach (var keyName in new[]
    {
        @"HKEY_CURRENT_USER\Software\Valve\Steam",
        @"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam",
        @"HKEY_LOCAL_MACHINE\SOFTWARE\Valve\Steam"
    })
    {
        var value = Registry.GetValue(keyName, "SteamPath", null)
            ?? Registry.GetValue(keyName, "InstallPath", null);

        if (value is string path && Directory.Exists(path))
        {
            return path.Replace('/', Path.DirectorySeparatorChar);
        }
    }

    return null;
}

IEnumerable<string> ParseSteamLibraryFolders(string vdfPath)
{
    foreach (var line in File.ReadLines(vdfPath))
    {
        var trimmed = line.Trim();
        if (!trimmed.Contains("\"path\"", StringComparison.OrdinalIgnoreCase))
        {
            continue;
        }

        var parts = trimmed.Split('"', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length >= 2)
        {
            var path = parts[^1].Replace(@"\\", @"\");
            if (Directory.Exists(path))
            {
                yield return path;
            }
        }
    }
}

void Pause()
{
    Console.WriteLine();
    Console.Write("Нажмите Enter...");
    Console.ReadLine();
}

record InstallTarget(string Name, string Root, TargetKind Kind);
record JsonPatchResult(int Changed, int SkippedAmbiguous);

sealed class PatchCatalog
{
    readonly Dictionary<string, string> keyTranslations;
    readonly Dictionary<(string Key, string SourceText), string> exactTranslations;

    PatchCatalog(
        int format,
        string name,
        string language,
        Dictionary<string, string> keyTranslations,
        Dictionary<(string Key, string SourceText), string> exactTranslations)
    {
        Format = format;
        Name = name;
        Language = language;
        this.keyTranslations = keyTranslations;
        this.exactTranslations = exactTranslations;
    }

    public int Format { get; }
    public string Name { get; }
    public string Language { get; }
    public int TranslationCount => Math.Max(exactTranslations.Count, keyTranslations.Count);
    public bool HasExactTranslations => exactTranslations.Count > 0;
    public IReadOnlyDictionary<string, string> KeyTranslations => keyTranslations;

    public bool TryTranslate(string key, string sourceText, out string translated)
    {
        if (exactTranslations.TryGetValue((key, sourceText), out translated!))
        {
            return true;
        }

        return keyTranslations.TryGetValue(key, out translated!);
    }

    public bool TryTranslateExact(string key, string sourceText, out string translated)
    {
        return exactTranslations.TryGetValue((key, sourceText), out translated!);
    }

    public static PatchCatalog FromKeyTranslations(
        int format,
        string name,
        string language,
        Dictionary<string, string> keyTranslations)
    {
        return new PatchCatalog(
            format,
            name,
            language,
            keyTranslations,
            new Dictionary<(string Key, string SourceText), string>());
    }

    public static PatchCatalog FromExactTranslations(
        int format,
        string name,
        string language,
        Dictionary<string, string> keyTranslations,
        Dictionary<(string Key, string SourceText), string> exactTranslations)
    {
        return new PatchCatalog(
            format,
            name,
            language,
            keyTranslations,
            exactTranslations);
    }

    public static PatchCatalog Merge(PatchCatalog basePatch, PatchCatalog overridePatch)
    {
        var keyTranslations = new Dictionary<string, string>(basePatch.keyTranslations, StringComparer.Ordinal);
        foreach (var pair in overridePatch.keyTranslations)
        {
            keyTranslations[pair.Key] = pair.Value;
        }

        var exactTranslations = new Dictionary<(string Key, string SourceText), string>(basePatch.exactTranslations);
        foreach (var pair in overridePatch.exactTranslations)
        {
            exactTranslations[pair.Key] = pair.Value;
        }

        return new PatchCatalog(
            Math.Max(basePatch.Format, overridePatch.Format),
            overridePatch.Name,
            overridePatch.Language,
            keyTranslations,
            exactTranslations);
    }

    public static PatchCatalog Normalize(PatchCatalog patch, Func<string, string> normalize)
    {
        var keyTranslations = new Dictionary<string, string>(patch.keyTranslations.Count, StringComparer.Ordinal);
        foreach (var pair in patch.keyTranslations)
        {
            keyTranslations[pair.Key] = normalize(pair.Value);
        }

        var exactTranslations = new Dictionary<(string Key, string SourceText), string>(patch.exactTranslations.Count);
        foreach (var pair in patch.exactTranslations)
        {
            exactTranslations[pair.Key] = normalize(pair.Value);
        }

        return new PatchCatalog(
            patch.Format,
            patch.Name,
            patch.Language,
            keyTranslations,
            exactTranslations);
    }
}

sealed class GlossaryCatalog
{
    readonly List<KeyValuePair<string, string>> replacements;

    public GlossaryCatalog(IEnumerable<KeyValuePair<string, string>> replacements)
    {
        this.replacements = replacements
            .OrderByDescending(static pair => pair.Key.Length)
            .ToList();
    }

    public bool IsEmpty => replacements.Count == 0;

    public string Normalize(string text)
    {
        var result = text;
        foreach (var pair in replacements)
        {
            result = result.Replace(pair.Key, pair.Value, StringComparison.Ordinal);
        }

        return result;
    }
}

enum TargetKind
{
    Cache,
    StreamingAssets
}
