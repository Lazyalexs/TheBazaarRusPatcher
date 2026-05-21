# =============================================================================
# Build script: TheBazaarRusPatcher
# Produces TWO copies of the console patcher in dist/:
#   - TheBazaarRusPatcher-Tempo.exe  (auto-targets Tempo Launcher beta)
#   - TheBazaarRusPatcher-Steam.exe  (auto-targets Steam install)
# Same binary; the name itself selects which launcher to patch (no need
# to remember --tempo-only / --steam-only). Either copy still accepts the
# flags for explicit override.
#
# Requires: .NET SDK 8+
# =============================================================================

$ErrorActionPreference = 'Stop'

$project   = "TheBazaarRusPatcher.csproj"
$publish   = "publish-release"
$dist      = "dist"

Write-Host ""
Write-Host "=== The Bazaar Russian Patcher - Build ===" -ForegroundColor Cyan
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

# Ship two named copies so each auto-targets its launcher via exe-name detection
$tempoExe = Join-Path $dist "TheBazaarRusPatcher-Tempo.exe"
$steamExe = Join-Path $dist "TheBazaarRusPatcher-Steam.exe"
Copy-Item $exe $tempoExe -Force
Copy-Item $exe $steamExe -Force

$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "  $tempoExe ($sizeMb MB) - patches Tempo Launcher copy"
Write-Host "  $steamExe ($sizeMb MB) - patches Steam copy"
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  TheBazaarRusPatcher-Tempo.exe                  - interactive menu (Tempo)"
Write-Host "  TheBazaarRusPatcher-Tempo.exe --install --yes  - apply patch to Tempo"
Write-Host "  TheBazaarRusPatcher-Steam.exe --install --yes  - apply patch to Steam"
Write-Host "  Either .exe --restore                          - restore from backup"
Write-Host "  Either .exe --check                            - verify state"
