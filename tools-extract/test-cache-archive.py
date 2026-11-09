"""Integration test for patching an isolated cache and its startup archive.

Run with Python and the .NET SDK on Windows. Only a temporary fixture under
dist is changed; real cache discovery and the game-process check are disabled
in a private copy of Program.cs, not in the production source.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = (ROOT / 'dist').resolve()
WORK.mkdir(exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, **kwargs):
    p = subprocess.run(args, check=True, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', **kwargs)
    if 'ОШИБКА:' in p.stdout:
        raise RuntimeError(p.stdout)
    return p.stdout


dotnet = shutil.which('dotnet')
if not dotnet:
    raise RuntimeError('The .NET SDK must be on PATH')

with tempfile.TemporaryDirectory(prefix='cache-regression-', dir=WORK) as folder:
    fixture = Path(folder).resolve()
    assert fixture.parent == WORK
    (fixture / 'Patch').mkdir()
    (fixture / 'cache/translations').mkdir(parents=True)
    for name in ('translation-patch.json', 'gamedata-tooltips.json'):
        shutil.copy2(ROOT / 'Patch' / name, fixture / 'Patch' / name)

    source = (ROOT / 'Program.cs').read_text(encoding='utf-8')
    substitutions = {
        'var cacheRoot = Path.Combine(localLow, "Tempo Storm", "The Bazaar", "prod", "cache");':
            'var cacheRoot = Environment.GetEnvironmentVariable("BAZAAR_TEST_CACHE")!;',
        'var steamStreamingAssets = FindSteamStreamingAssets().ToList();':
            'var steamStreamingAssets = new List<string>();',
        'var cacheRoots = FindCacheRoots().ToList();':
            'var cacheRoots = new List<string> { cacheRoot };',
        'if (!dryRun && !EnsureGameClosed())': 'if (!dryRun && false)',
    }
    for before, after in substitutions.items():
        assert source.count(before) == 1, before
        source = source.replace(before, after, 1)
    (fixture / 'Program.cs').write_text(source, encoding='utf-8')
    (fixture / 'Fixture.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup>
  <ItemGroup><PackageReference Include="Microsoft.Data.Sqlite" Version="8.0.11" />
    <EmbeddedResource Include="Patch/translation-patch.json"><LogicalName>Patch/translation-patch.json</LogicalName></EmbeddedResource>
    <EmbeddedResource Include="Patch/gamedata-tooltips.json"><LogicalName>Patch/gamedata-tooltips.json</LogicalName></EmbeddedResource>
  </ItemGroup></Project>''', encoding='utf-8')

    cache = fixture / 'cache'
    game_db = cache / 'GameData.db'
    key = '39856059637695f4e47c8866777e5396'
    english = 'When you sell this, make your leftmost item Tiny'
    patch = json.loads((ROOT / 'Patch/translation-patch.json').read_text(encoding='utf-8'))['translations']
    with sqlite3.connect(game_db) as db:
        db.execute('CREATE TABLE cards (Id TEXT PRIMARY KEY, Data BLOB)')
        db.execute('INSERT INTO cards VALUES (?, ?)', ('test', json.dumps(
            {'Localization': {'Text': {'Key': key, 'Text': english}}}).encode()))
        db.execute('CREATE TABLE tooltips (Id TEXT PRIMARY KEY, Data BLOB)')
        db.execute('INSERT INTO tooltips VALUES (?, ?)', ('test', json.dumps(
            {'Poison': {'Tag': 'Poison', 'Keyword': 'Damages Players every second'}}).encode()))
    db.close()
    with sqlite3.connect(cache / 'translations/ru-RU.bytes') as db:
        db.execute('CREATE TABLE translation (hash TEXT PRIMARY KEY, text TEXT NOT NULL) WITHOUT ROWID')
    db.close()
    archive = cache / 'GameData.db.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(game_db, 'GameData.db')
        z.writestr('marker.txt', 'preserve this entry')
    manifest = cache / 'manifest.json'
    manifest.write_text('{"Entries":{"GameData":{"ETag":"server-etag"}}}', encoding='utf-8')
    original_archive = sha(archive)
    original_game = sha(game_db)
    original_manifest = sha(manifest)

    run([dotnet, 'build', str(fixture / 'Fixture.csproj'), '-c', 'Release'])
    env = os.environ.copy()
    env['BAZAAR_TEST_CACHE'] = str(cache)
    command = [dotnet, str(fixture / 'bin/Release/net8.0/Fixture.dll'), '--steam-only']
    run(command + ['--check'], env=env)
    assert sha(archive) == original_archive and sha(game_db) == original_game
    run(command + ['--install', '--yes'], env=env)
    assert sha(manifest) == original_manifest
    backups = list((cache / '.rus_patch_backups').glob('*/GameData.db.zip'))
    assert len(backups) == 1 and sha(backups[0]) == original_archive

    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and z.read('marker.txt') == b'preserve this entry'
        data = z.read('GameData.db')
    with sqlite3.connect(':memory:') as db:
        db.deserialize(data)
        assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
        card = json.loads(db.execute('SELECT Data FROM cards').fetchone()[0])
        tips = json.loads(db.execute('SELECT Data FROM tooltips').fetchone()[0])
        assert card['Localization']['Text']['Text'] == patch[key]
        assert tips['Poison']['Keyword'] == 'Наносит урон игрокам каждую секунду'
    db.close()

    # The client extracts the ZIP on every launch, including after HTTP 304.
    game_db.write_bytes(data)
    check = run(command + ['--check'], env=env)
    assert 'GameData.db.zip: переводимых строк не найдено' in check
    assert 'GameData.db: переводимых строк не найдено' in check
    print('PASS: dry run, archive translation, backup, ETag, extra entries, startup extraction and idempotency')
