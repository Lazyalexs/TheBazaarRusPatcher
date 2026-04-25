# =============================================================================
# Build script: TheBazaarRusSteamPatcher
# Требования: .NET SDK 8+
# =============================================================================


$project   = "TheBazaarRusSteamPatcher.csproj"
$outputDir = "publish-steam"

Write-Host ""
Write-Host "=== The Bazaar Rus Steam Patcher — сборка ===" -ForegroundColor Cyan
Write-Host ""

# Проверяем наличие .NET SDK
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "ОШИБКА: dotnet не найден. Установите .NET SDK 8+" -ForegroundColor Red
    Write-Host "https://dotnet.microsoft.com/download" -ForegroundColor Yellow
    exit 1
}

$sdkVersion = dotnet --version
Write-Host "dotnet SDK: $sdkVersion"

# Проверяем наличие .csproj
if (-not (Test-Path $project)) {
    Write-Host "ОШИБКА: файл $project не найден в текущей папке." -ForegroundColor Red
    Write-Host "Запускайте скрипт из корня репозитория." -ForegroundColor Yellow
    exit 1
}

# Проверяем наличие патч-файлов
$requiredPatchFiles = @(
    "Patch\steam-translation-patch.json",
    "Patch\steam-quality-overrides.json",
    "Patch\steam-glossary.json"
)

$missingFiles = $requiredPatchFiles | Where-Object { -not (Test-Path $_) }
if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ОШИБКА: не найдены файлы патча:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Убедитесь, что папка Patch\ содержит все три файла." -ForegroundColor Yellow
    exit 1
}

Write-Host "Файлы патча: OK" -ForegroundColor Green

# Очищаем предыдущую сборку
if (Test-Path $outputDir) {
    Write-Host "Очищаем $outputDir ..."
    Remove-Item -Recurse -Force $outputDir
}

Write-Host ""
Write-Host "Собираем $project ..." -ForegroundColor Cyan
Write-Host ""

dotnet publish $project `
    -c Release `
    -r win-x64 `
    --self-contained true `
    /p:PublishSingleFile=true `
    /p:EnableCompressionInSingleFile=true `
    /p:IncludeNativeLibrariesForSelfExtract=true `
    /p:RestoreFallbackFolders= `
    -o $outputDir

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ОШИБКА: сборка завершилась с кодом $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Join-Path $outputDir "TheBazaarRusSteamPatcher.exe"
if (-not (Test-Path $exe)) {
    Write-Host "ОШИБКА: $exe не найден после сборки." -ForegroundColor Red
    exit 1
}

$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)

Write-Host ""
Write-Host "=== Сборка успешна ===" -ForegroundColor Green
Write-Host "Файл : $exe"
Write-Host "Размер: $sizeMb MB"
Write-Host ""
Write-Host "Проверка (dry-run):" -ForegroundColor Cyan
Write-Host "  .\$outputDir\TheBazaarRusSteamPatcher.exe --check"
Write-Host ""
Write-Host "Установка:" -ForegroundColor Cyan
Write-Host "  .\$outputDir\TheBazaarRusSteamPatcher.exe --install --yes"
Write-Host ""
