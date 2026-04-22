using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Data.Sqlite;
using Microsoft.Win32;

const string AppName = "The Bazaar Russian Patcher";
const string BackupDirName = ".rus_patch_backups";
const string PatchResourceName = "Patch/translation-patch.json";

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
var steamStreamingAssets = FindSteamStreamingAssets().ToList();
var assumeYes = args.Any(a => a.Equals("--yes", StringComparison.OrdinalIgnoreCase));

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
    Console.WriteLine($"Строк перевода в патче: {patch.Translations.Count:N0}");

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
    var dbPath = Path.Combine(root, "translations", "ru-RU.bytes");
    if (File.Exists(dbPath))
    {
        if (!ValidateTranslationDatabase(dbPath, out var reason))
        {
            Console.WriteLine($"  ru-RU.bytes: пропущено ({reason})");
        }
        else
        {
            if (!dryRun)
            {
                BackupExistingFile(root, dbPath, stamp);
            }

            var changed = PatchTranslationDatabase(dbPath, dryRun);
            Console.WriteLine(dryRun
                ? $"  ru-RU.bytes: будет обновлено строк {changed:N0}"
                : $"  ru-RU.bytes: обновлено строк {changed:N0}");
        }
    }
    else
    {
        Console.WriteLine("  ru-RU.bytes не найден.");
    }

    var cards = Path.Combine(root, "cards.json");
    if (File.Exists(cards))
    {
        PatchJsonFile(root, cards, stamp, dryRun);
    }

    var tooltips = Path.Combine(root, "tooltips.json");
    if (File.Exists(tooltips))
    {
        PatchJsonFile(root, tooltips, stamp, dryRun);
    }

    UpdateManifestIfExists(Path.Combine(root, "manifest.json"), root, dryRun);
    UpdateManifestIfExists(Path.Combine(root, "translations", "manifest.json"), Path.Combine(root, "translations"), dryRun);
}

void PatchStreamingAssets(string root, string stamp, bool dryRun)
{
    foreach (var fileName in new[] { "cards.json", "tooltips.json" })
    {
        var path = Path.Combine(root, fileName);
        if (!File.Exists(path))
        {
            Console.WriteLine($"  {fileName}: не найден.");
            continue;
        }

        PatchJsonFile(root, path, stamp, dryRun);
    }

    UpdateManifestIfExists(Path.Combine(root, "manifest.json"), root, dryRun);
}

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

    var changed = PatchJsonTextByKey(path, dryRun);
    Console.WriteLine(dryRun
        ? $"  {fileName}: будет обновлено текстов {changed:N0}"
        : $"  {fileName}: обновлено текстов {changed:N0}");
}

int PatchTranslationDatabase(string dbPath, bool dryRun)
{
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

        foreach (var (hash, text) in patch.Translations)
        {
            selectHash.Value = hash;
            var existing = select.ExecuteScalar() as string;
            if (existing != text)
            {
                changed++;
            }
        }

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

    foreach (var (hash, text) in patch.Translations)
    {
        hashParam.Value = hash;
        textParam.Value = text;
        changed += command.ExecuteNonQuery();
    }

    transaction.Commit();
    return changed;
}

int PatchJsonTextByKey(string path, bool dryRun)
{
    var json = File.ReadAllText(path);
    var root = JsonNode.Parse(json);
    if (root is null)
    {
        return 0;
    }

    var changed = 0;
    PatchNode(root, ref changed);

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

    return changed;
}

void PatchNode(JsonNode node, ref int changed)
{
    if (node is JsonObject obj)
    {
        if (obj.TryGetPropertyValue("Key", out var keyNode)
            && obj.TryGetPropertyValue("Text", out var textNode)
            && keyNode?.GetValueKind() == JsonValueKind.String
            && textNode?.GetValueKind() == JsonValueKind.String)
        {
            var key = keyNode.GetValue<string>();
            var current = textNode.GetValue<string>();

            if (patch.Translations.TryGetValue(key, out var translated) && translated != current)
            {
                obj["Text"] = translated;
                changed++;
            }
        }

        foreach (var child in obj.ToList())
        {
            if (child.Value is not null)
            {
                PatchNode(child.Value, ref changed);
            }
        }
    }
    else if (node is JsonArray array)
    {
        foreach (var child in array)
        {
            if (child is not null)
            {
                PatchNode(child, ref changed);
            }
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

        if (!obj.ContainsKey("5.0.0"))
        {
            reason = "версия данных не проверена";
            return false;
        }

        var textNodeCount = 0;
        CountTextNodes(root, ref textNodeCount);
        if (textNodeCount == 0)
        {
            reason = "не найдены узлы Key/Text";
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
        if (obj.TryGetPropertyValue("Key", out var keyNode)
            && obj.TryGetPropertyValue("Text", out var textNode)
            && keyNode?.GetValueKind() == JsonValueKind.String
            && textNode?.GetValueKind() == JsonValueKind.String)
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
    Console.WriteLine($"Строк перевода: {patch.Translations.Count:N0}");
}

IEnumerable<InstallTarget> GetInstallTargets()
{
    yield return new InstallTarget("Общий кэш LocalLow", cacheRoot, TargetKind.Cache);

    if (Directory.Exists(launcherStreamingAssets))
    {
        yield return new InstallTarget("Tempo Launcher", launcherStreamingAssets, TargetKind.StreamingAssets);
    }

    foreach (var steamPath in steamStreamingAssets)
    {
        yield return new InstallTarget("Steam", steamPath, TargetKind.StreamingAssets);
    }
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

TranslationPatch LoadPatch()
{
    using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(PatchResourceName)
        ?? throw new InvalidOperationException($"Patch resource not found: {PatchResourceName}");
    var result = JsonSerializer.Deserialize<TranslationPatch>(stream, new JsonSerializerOptions
    {
        PropertyNameCaseInsensitive = true
    });

    if (result is null || result.Translations.Count == 0)
    {
        throw new InvalidOperationException("Translation patch is empty.");
    }

    return result;
}

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

record TranslationPatch(int Format, string Name, string Language, Dictionary<string, string> Translations);
record InstallTarget(string Name, string Root, TargetKind Kind);

enum TargetKind
{
    Cache,
    StreamingAssets
}
