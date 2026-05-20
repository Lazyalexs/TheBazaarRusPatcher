using Microsoft.Data.Sqlite;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

class Extract
{
    static readonly string CACHE_ROOT = @"C:\Users\users\AppData\LocalLow\Tempo Storm\The Bazaar\prod\cache";
    static readonly string STEAM_ROOT = @"G:\SteamLibrary\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets";
    static readonly string OUT_DIR = @"E:\memore\the-bazaar-rus-patcher\tools-extract";

    static void Main()
    {
        // hash -> first English source text we see for that hash
        var all = new Dictionary<string, string>(StringComparer.Ordinal);
        // count how many times each hash appears (for visibility)
        var sources = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);

        // 1. cards.json / tooltips.json / challenges.json from both locations
        foreach (var root in new[] { CACHE_ROOT, STEAM_ROOT })
        {
            foreach (var fn in new[] { "cards.json", "tooltips.json", "challenges.json", "monsters.json", "gamemodes.json", "levelups.json", "seasons.json" })
            {
                var p = Path.Combine(root, fn);
                if (!File.Exists(p)) continue;
                try
                {
                    var node = JsonNode.Parse(File.ReadAllText(p));
                    if (node is null) continue;
                    CollectKeyText(node, all, sources, $"{Path.GetFileName(root)}/{fn}");
                }
                catch (Exception e) { Console.WriteLine($"[skip {p}] {e.Message}"); }
            }
        }

        // 2. GameData.db BLOB tables
        foreach (var root in new[] { CACHE_ROOT, STEAM_ROOT })
        {
            var db = Path.Combine(root, "GameData.db");
            if (!File.Exists(db)) continue;
            try
            {
                using var con = new SqliteConnection($"Data Source={db};Mode=ReadOnly");
                con.Open();
                foreach (var tbl in new[] { "cards", "challenges", "collectibles", "game_modes", "level_ups", "monsters", "seasons" })
                {
                    using var cmd = con.CreateCommand();
                    cmd.CommandText = $"SELECT Data FROM {tbl}";
                    using var r = cmd.ExecuteReader();
                    while (r.Read())
                    {
                        var blob = (byte[])r["Data"];
                        var s = Encoding.UTF8.GetString(blob);
                        try
                        {
                            var node = JsonNode.Parse(s);
                            if (node is null) continue;
                            CollectKeyText(node, all, sources, $"{Path.GetFileName(root)}/GameData.db/{tbl}");
                        }
                        catch { }
                    }
                }
            }
            catch (Exception e) { Console.WriteLine($"[skip {db}] {e.Message}"); }
        }

        Console.WriteLine($"Total unique hashes found: {all.Count:N0}");
        Console.WriteLine($"Sources count: {sources.Sum(s => s.Value.Count):N0} hash occurrences across files");

        // Save dict to JSON
        var output = new
        {
            count = all.Count,
            generated = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            translations = all
        };
        File.WriteAllText(
            Path.Combine(OUT_DIR, ".all-game-hashes.json"),
            JsonSerializer.Serialize(output, new JsonSerializerOptions
            {
                WriteIndented = false,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            }));

        // Also save sources map
        var srcOut = sources.ToDictionary(kv => kv.Key, kv => kv.Value.ToArray());
        File.WriteAllText(
            Path.Combine(OUT_DIR, ".all-game-hashes-sources.json"),
            JsonSerializer.Serialize(srcOut, new JsonSerializerOptions
            {
                WriteIndented = false,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            }));

        Console.WriteLine($"Wrote {Path.Combine(OUT_DIR, ".all-game-hashes.json")}");
    }

    static void CollectKeyText(JsonNode node, Dictionary<string, string> all, Dictionary<string, HashSet<string>> sources, string label)
    {
        if (node is JsonObject obj)
        {
            // {Key, Text} pair (the canonical localization shape)
            if (obj.TryGetPropertyValue("Key", out var keyNode)
                && obj.TryGetPropertyValue("Text", out var textNode)
                && keyNode?.GetValueKind() == JsonValueKind.String
                && textNode?.GetValueKind() == JsonValueKind.String)
            {
                var k = keyNode.GetValue<string>();
                var t = textNode.GetValue<string>();
                if (!string.IsNullOrEmpty(k) && !string.IsNullOrEmpty(t))
                {
                    if (!all.ContainsKey(k)) all[k] = t;
                    if (!sources.ContainsKey(k)) sources[k] = new HashSet<string>(StringComparer.Ordinal);
                    sources[k].Add(label);
                }
            }
            // {Id, Tag, Keyword} tooltip-style — Id is human-readable, NOT a hash, skip for hash collection
            foreach (var child in obj)
            {
                if (child.Value is not null) CollectKeyText(child.Value, all, sources, label);
            }
        }
        else if (node is JsonArray arr)
        {
            foreach (var child in arr)
            {
                if (child is not null) CollectKeyText(child, all, sources, label);
            }
        }
    }
}
