using Microsoft.Data.Sqlite;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

class Diff
{
    static void Main()
    {
        var outDir = @"E:\memore\the-bazaar-rus-patcher\tools-extract";

        var allDoc = JsonNode.Parse(File.ReadAllText(Path.Combine(outDir, ".all-game-hashes.json")))!;
        var translations = (JsonObject)allDoc["translations"]!;
        var gameHashes = translations.ToDictionary(kv => kv.Key, kv => kv.Value!.GetValue<string>());

        var ruHashes = new HashSet<string>();
        var ruRu = @"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\translations\ru-RU.bytes";
        using (var con = new SqliteConnection($"Data Source={ruRu};Mode=ReadOnly"))
        {
            con.Open();
            using var cmd = con.CreateCommand();
            cmd.CommandText = "SELECT hash, text FROM translation WHERE text <> ''";
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                ruHashes.Add(r.GetString(0));
            }
        }

        var englishSource = new Dictionary<string, string>(StringComparer.Ordinal);
        var zipPath = @"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache\GameData.db.zip";
        if (File.Exists(zipPath))
        {
            var tempDb = Path.Combine(Path.GetTempPath(), $"english-gamedata-{Guid.NewGuid()}.db");
            try
            {
                using (var zip = ZipFile.OpenRead(zipPath))
                {
                    var entry = zip.Entries.FirstOrDefault(e => e.Name.EndsWith(".db", StringComparison.OrdinalIgnoreCase));
                    if (entry != null) entry.ExtractToFile(tempDb, true);
                }
                if (File.Exists(tempDb))
                {
                    using var con = new SqliteConnection($"Data Source={tempDb};Mode=ReadOnly");
                    con.Open();
                    foreach (var tbl in new[] { "cards", "challenges", "collectibles", "game_modes", "level_ups", "monsters", "seasons" })
                    {
                        using var c = con.CreateCommand();
                        c.CommandText = $"SELECT Data FROM {tbl}";
                        try
                        {
                            using var rd = c.ExecuteReader();
                            while (rd.Read())
                            {
                                var blob = (byte[])rd["Data"];
                                var s = Encoding.UTF8.GetString(blob);
                                try
                                {
                                    var node = JsonNode.Parse(s);
                                    if (node != null) CollectKeyText(node, englishSource);
                                }
                                catch { }
                            }
                        }
                        catch (Exception e) { Console.WriteLine($"[skip {tbl}] {e.Message}"); }
                    }
                }
                File.Delete(tempDb);
            }
            catch (Exception e) { Console.WriteLine($"Zip extract failed: {e.Message}"); }
        }

        Console.WriteLine($"Game on-disk hashes (cards/GameData):        {gameHashes.Count:N0}");
        Console.WriteLine($"ru-RU.bytes hashes (non-empty translations): {ruHashes.Count:N0}");
        Console.WriteLine($"English source hashes (from zip GameData):   {englishSource.Count:N0}");

        var missing = gameHashes.Keys.Where(k => !ruHashes.Contains(k)).ToList();
        Console.WriteLine($"Hashes used by game but NOT in ru-RU.bytes:  {missing.Count:N0}");

        var missingDict = new Dictionary<string, string>(StringComparer.Ordinal);
        int withEnglish = 0;
        foreach (var k in missing)
        {
            if (englishSource.TryGetValue(k, out var en))
            {
                missingDict[k] = en;
                withEnglish++;
            }
            else
            {
                missingDict[k] = gameHashes[k];
            }
        }
        Console.WriteLine($"  with confirmed English source from zip:    {withEnglish:N0}");
        Console.WriteLine($"  using on-disk text as source:              {missing.Count - withEnglish:N0}");

        File.WriteAllText(Path.Combine(outDir, ".missing-from-ru-RU.json"),
            JsonSerializer.Serialize(missingDict, new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            }));

        var report = new StringBuilder();
        report.AppendLine($"Coverage report - {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}Z");
        report.AppendLine();
        report.AppendLine($"Game on-disk unique hashes:                  {gameHashes.Count:N0}");
        report.AppendLine($"ru-RU.bytes non-empty translations:          {ruHashes.Count:N0}");
        report.AppendLine($"English source from GameData.db.zip:         {englishSource.Count:N0}");
        report.AppendLine();
        report.AppendLine($"Hashes in game-data but missing from ru-RU:  {missing.Count:N0}");
        report.AppendLine($"  with confirmed English source:             {withEnglish:N0}");
        report.AppendLine($"  fallback to on-disk (may be RU already):   {missing.Count - withEnglish:N0}");
        report.AppendLine();
        report.AppendLine("Sample missing entries (first 30):");
        foreach (var k in missing.Take(30))
        {
            var src = missingDict[k];
            var shown = src.Length > 100 ? src.Substring(0, 100) + "..." : src;
            report.AppendLine($"  {k[..Math.Min(20, k.Length)]} | {shown}");
        }
        File.WriteAllText(Path.Combine(outDir, ".coverage-report.txt"), report.ToString());
        Console.WriteLine($"Wrote .missing-from-ru-RU.json + .coverage-report.txt");
    }

    static void CollectKeyText(JsonNode node, Dictionary<string, string> dict)
    {
        if (node is JsonObject obj)
        {
            if (obj.TryGetPropertyValue("Key", out var keyNode)
                && obj.TryGetPropertyValue("Text", out var textNode)
                && keyNode?.GetValueKind() == JsonValueKind.String
                && textNode?.GetValueKind() == JsonValueKind.String)
            {
                var k = keyNode.GetValue<string>();
                var t = textNode.GetValue<string>();
                if (!string.IsNullOrEmpty(k) && !string.IsNullOrEmpty(t))
                {
                    if (!dict.ContainsKey(k)) dict[k] = t;
                }
            }
            foreach (var c in obj) if (c.Value != null) CollectKeyText(c.Value, dict);
        }
        else if (node is JsonArray arr)
        {
            foreach (var c in arr) if (c != null) CollectKeyText(c, dict);
        }
    }
}
