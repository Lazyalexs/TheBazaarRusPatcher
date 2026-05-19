; The Bazaar Russian Patcher — Inno Setup installer
; Builds: dist\TheBazaarRusPatcher-<version>-setup.exe
;
; Build via: ISCC.exe installer.iss
; Expects: publish-release\TheBazaarRusPatcher.exe (build via build-steam.ps1 or dotnet publish)

#define MyAppName        "The Bazaar Russian Patcher"
#define MyAppVersion     "0.4.7"
#define MyAppPublisher   "Lazyalexs"
#define MyAppURL         "https://github.com/Lazyalexs/TheBazaarRusPatcher"
#define MyAppExeName     "TheBazaarRusPatcher.exe"
#define MyAppExeSource   "publish-release\TheBazaarRusPatcher.exe"

[Setup]
AppId={{F6E2612B-D52F-46D9-B5A9-5E9003D7FBFD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=TheBazaarRusPatcher-{#MyAppVersion}-setup
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
DisableProgramGroupPage=auto
VersionInfoVersion=0.4.7.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
russian.LauncherPageCaption=Версия игры
russian.LauncherPageDescription=Выберите для какой версии The Bazaar применить русификатор. Найденные варианты подсвечены.
russian.TempoLabel=Tempo Launcher (бета)
russian.SteamLabel=Steam
russian.BothLabel=Обе версии
russian.DetectedFmt=Найдено: %1
russian.NotDetectedFmt=Не найдено (можно установить позже)
russian.InstallNow=Применить русификатор сразу после установки
russian.LaunchInteractive=Запустить патчер в интерактивном режиме после установки
english.LauncherPageCaption=Game version
english.LauncherPageDescription=Choose which copy of The Bazaar to patch. Detected installs are highlighted.
english.TempoLabel=Tempo Launcher (beta)
english.SteamLabel=Steam
english.BothLabel=Both
english.DetectedFmt=Detected at: %1
english.NotDetectedFmt=Not detected (can install later)
english.InstallNow=Apply Russian patch immediately after install
english.LaunchInteractive=Launch the patcher in interactive mode after install

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppExeSource}"; DestDir: "{app}"; Flags: ignoreversion
Source: "publish-release\e_sqlite3.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Patch\translation-patch.json"; DestDir: "{app}\Patch"; Flags: ignoreversion
Source: "Patch\steam-translation-patch.json"; DestDir: "{app}\Patch"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Patch\steam-glossary.json"; DestDir: "{app}\Patch"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Patch\steam-quality-overrides.json"; DestDir: "{app}\Patch"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "DISCLAIMER.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Apply patch automatically using the launcher choice the user made
Filename: "{app}\{#MyAppExeName}"; Parameters: "{code:GetPatchArgs}"; \
    Description: "{cm:InstallNow}"; Flags: postinstall nowait skipifsilent runascurrentuser; \
    Check: ShouldAutoApply
; Or launch interactively if user prefers
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchInteractive}"; Flags: postinstall nowait skipifsilent runascurrentuser unchecked; \
    Check: not ShouldAutoApply

[Code]
const
  LAUNCHER_TEMPO = 0;
  LAUNCHER_STEAM = 1;
  LAUNCHER_BOTH  = 2;

var
  LauncherPage: TInputOptionWizardPage;
  TempoDetectedAt: String;
  SteamDetectedAt: String;

function GetTempoPath: String;
var
  Base: String;
begin
  Base := ExpandConstant('{userappdata}\Tempo Launcher - Beta\game\buildx64\TheBazaar_Data\StreamingAssets');
  if DirExists(Base) and FileExists(Base + '\cards.json') then
    Result := Base
  else
    Result := '';
end;

function GetSteamInstallPath: String;
var
  SteamPath: String;
begin
  Result := '';
  if RegQueryStringValue(HKLM64, 'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath', SteamPath) then
  begin
    Result := SteamPath;
    exit;
  end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath', SteamPath) then
  begin
    Result := SteamPath;
    exit;
  end;
  if RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', SteamPath) then
    Result := SteamPath;
end;

function FindSteamGamePath: String;
var
  Steam: String;
  Candidate: String;
begin
  // Check default Steam library only. The C# patcher itself parses
  // libraryfolders.vdf and finds games on alternate libraries, so missing
  // detection here is purely cosmetic for the wizard page.
  Result := '';
  Steam := GetSteamInstallPath;
  if Steam = '' then exit;
  Candidate := Steam + '\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets';
  if DirExists(Candidate) and FileExists(Candidate + '\cards.json') then
    Result := Candidate;
end;

procedure InitializeWizard;
var
  TempoLabel, SteamLabel, BothLabel: String;
  TempoIdx, SteamIdx, BothIdx: Integer;
begin
  TempoDetectedAt := GetTempoPath;
  SteamDetectedAt := FindSteamGamePath;

  // Build labels showing detection status
  if TempoDetectedAt <> '' then
    TempoLabel := ExpandConstant('{cm:TempoLabel}') + '  —  ' + Format(ExpandConstant('{cm:DetectedFmt}'), [TempoDetectedAt])
  else
    TempoLabel := ExpandConstant('{cm:TempoLabel}') + '  —  ' + ExpandConstant('{cm:NotDetectedFmt}');

  if SteamDetectedAt <> '' then
    SteamLabel := ExpandConstant('{cm:SteamLabel}') + '  —  ' + Format(ExpandConstant('{cm:DetectedFmt}'), [SteamDetectedAt])
  else
    SteamLabel := ExpandConstant('{cm:SteamLabel}') + '  —  ' + ExpandConstant('{cm:NotDetectedFmt}');

  BothLabel := ExpandConstant('{cm:BothLabel}');

  LauncherPage := CreateInputOptionPage(
    wpSelectTasks,
    ExpandConstant('{cm:LauncherPageCaption}'),
    ExpandConstant('{cm:LauncherPageDescription}'),
    '',
    True, False);

  TempoIdx := LauncherPage.Add(TempoLabel);
  SteamIdx := LauncherPage.Add(SteamLabel);
  BothIdx  := LauncherPage.Add(BothLabel);

  // Pre-select sensible default
  if (TempoDetectedAt <> '') and (SteamDetectedAt <> '') then
    LauncherPage.SelectedValueIndex := BothIdx
  else if TempoDetectedAt <> '' then
    LauncherPage.SelectedValueIndex := TempoIdx
  else if SteamDetectedAt <> '' then
    LauncherPage.SelectedValueIndex := SteamIdx
  else
    LauncherPage.SelectedValueIndex := BothIdx;  // user will pick after install
end;

function ChosenLauncher: Integer;
begin
  Result := LauncherPage.SelectedValueIndex;
end;

function ShouldAutoApply: Boolean;
begin
  // Auto-apply when at least one launcher was detected
  Result := (TempoDetectedAt <> '') or (SteamDetectedAt <> '');
end;

function GetPatchArgs(Param: String): String;
begin
  case ChosenLauncher of
    LAUNCHER_TEMPO: Result := '--install --yes --tempo-only';
    LAUNCHER_STEAM: Result := '--install --yes --steam-only';
    LAUNCHER_BOTH:  Result := '--install --yes';
  else
    Result := '--install --yes';
  end;
end;
