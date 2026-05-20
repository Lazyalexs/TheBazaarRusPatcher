# =============================================================================
# Build script: TheBazaarRusPatcher console patcher (single .exe)
# Produces dist\TheBazaarRusPatcher.exe — a self-contained Windows binary
# the user runs directly from a terminal (or by double-clicking) to apply
# the Russian translation patch to The Bazaar.
#
# Requires: .NET SDK 8+
# =============================================================================

$ErrorActionPreference = 'Stop'

$project   = "TheBazaarRusPatcher.csproj"
$publish   = "publish-release"
$dist      = "dist"

Write-Host ""
Write-Host "=== The Bazaar Russian Patcher — Build ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: dotnet not found. Install .NET SDK 8+" -ForegroundColor Red
    Write-Host "https://dotnet.microsoft.com/download" -ForegroundColor Yellow
    exit 1
}
Write-Host "dotnet SDK: $(dotnet --version)"

if (-not (Test-Path "Patch\translation-patch.json")) {
    Write-Host "ERROR: Patch\translation-patch.json missing" -ForegroundColor Red
    exit 1
}
Write-Host "Patch files: OK" -ForegroundColor Green

if (Test-Path $publish) {
    Remove-Item -Recurse -Force $publish
}

Write-Host ""
Write-Host "Building $project (Release, win-x64, self-contained, single-file)..." -ForegroundColor Cyan
dotnet publish $project `
    -c Release `
    -r win-x64 `
    --self-contained true `
    /p:PublishSingleFile=true `
    /p:EnableCompressionInSingleFile=true `
    /p:IncludeNativeLibrariesForSelfExtract=true `
    -o $publish

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: dotnet publish failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Join-Path $publish "TheBazaarRusPatcher.exe"
if (-not (Test-Path $exe)) {
    Write-Host "ERROR: $exe not found after build" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $dist)) {
    New-Item -ItemType Directory -Path $dist | Out-Null
}
Copy-Item $exe (Join-Path $dist "TheBazaarRusPatcher.exe") -Force

$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "  $dist\TheBazaarRusPatcher.exe ($sizeMb MB)"
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  TheBazaarRusPatcher.exe                       — interactive menu"
Write-Host "  TheBazaarRusPatcher.exe --install --yes       — apply patch to all detected"
Write-Host "  TheBazaarRusPatcher.exe --install --tempo-only — Tempo Launcher only"
Write-Host "  TheBazaarRusPatcher.exe --install --steam-only — Steam only"
Write-Host "  TheBazaarRusPatcher.exe --restore             — restore from backup"
Write-Host "  TheBazaarRusPatcher.exe --check               — verify state"
