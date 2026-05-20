# =============================================================================
# Build script: TheBazaarRusPatcher installers
# Produces two separate setup.exe files in dist\:
#   - TheBazaarRusPatcher-Tempo-<version>-setup.exe  (Tempo Launcher only)
#   - TheBazaarRusPatcher-Steam-<version>-setup.exe  (Steam only)
# Both bundle the same TheBazaarRusPatcher.exe binary; the difference is
# which patch files are included and which launcher flag the installer
# passes to the patcher on auto-apply.
#
# Requires: .NET SDK 8+, Inno Setup 6 (winget install JRSoftware.InnoSetup)
# =============================================================================

$ErrorActionPreference = 'Stop'

$project    = "TheBazaarRusPatcher.csproj"
$outputDir  = "publish-release"
$tempoIss   = "installer-tempo.iss"
$steamIss   = "installer-steam.iss"

Write-Host ""
Write-Host "=== The Bazaar Russian Patcher — Build Installers ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: dotnet not found. Install .NET SDK 8+" -ForegroundColor Red
    Write-Host "https://dotnet.microsoft.com/download" -ForegroundColor Yellow
    exit 1
}
Write-Host "dotnet SDK: $(dotnet --version)"

$requiredPatchFiles = @(
    "Patch\translation-patch.json"
)
$missing = $requiredPatchFiles | Where-Object { -not (Test-Path $_) }
if ($missing.Count -gt 0) {
    Write-Host "ERROR: missing patch files:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    exit 1
}
Write-Host "Patch files: OK" -ForegroundColor Green

if (Test-Path $outputDir) {
    Remove-Item -Recurse -Force $outputDir
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
    -o $outputDir

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: dotnet publish failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Join-Path $outputDir "TheBazaarRusPatcher.exe"
if (-not (Test-Path $exe)) {
    Write-Host "ERROR: $exe not found after build" -ForegroundColor Red
    exit 1
}
$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Host "Built $exe ($sizeMb MB)" -ForegroundColor Green

$iscc = $null
foreach ($candidate in @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe',
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)) {
    if (Test-Path $candidate) { $iscc = $candidate; break }
}
if (-not $iscc) {
    $isccCmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($isccCmd) { $iscc = $isccCmd.Source }
}
if (-not $iscc) {
    Write-Host ""
    Write-Host "WARN: Inno Setup not found. Skipping installer build." -ForegroundColor Yellow
    Write-Host "      Install via: winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
    Write-Host "      Or manually: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Patcher binary is ready at: $exe" -ForegroundColor Green
    exit 0
}

foreach ($iss in @($tempoIss, $steamIss)) {
    Write-Host ""
    Write-Host "Building installer: $iss" -ForegroundColor Cyan
    & $iscc $iss
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: ISCC failed on $iss (exit $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Installers in dist\ directory:"
Get-ChildItem dist\*.exe | Sort-Object Name | ForEach-Object {
    $mb = [math]::Round($_.Length / 1MB, 1)
    Write-Host "  $($_.Name) ($mb MB)"
}
