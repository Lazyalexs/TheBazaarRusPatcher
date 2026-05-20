; The Bazaar Russian Patcher — Steam installer
; Builds: dist\TheBazaarRusPatcher-Steam-<version>-setup.exe

#define MyAppName        "The Bazaar Russian Patcher (Steam)"
#define MyAppVersion     "0.4.7"
#define MyAppPublisher   "Lazyalexs"
#define MyAppURL         "https://github.com/Lazyalexs/TheBazaarRusPatcher"
#define MyAppExeName     "TheBazaarRusPatcher.exe"
#define MyAppExeSource   "publish-release\TheBazaarRusPatcher.exe"

[Setup]
AppId={{A7C3B9D5-4E81-4F72-BC68-9E83D5F4C1A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\The Bazaar Russian Patcher (Steam)
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=TheBazaarRusPatcher-Steam-{#MyAppVersion}-setup
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
russian.DetectedFmt=Steam-версия найдена: %1
russian.NotDetectedMsg=Steam-версия The Bazaar не обнаружена в стандартной библиотеке. Установщик всё равно продолжит работу: патчер при запуске сам разберёт libraryfolders.vdf и найдёт игру в альтернативных библиотеках Steam.
russian.InstallNow=Применить русификатор сразу после установки
russian.LaunchInteractive=Запустить патчер в интерактивном режиме после установки
english.DetectedFmt=Steam version detected at: %1
english.NotDetectedMsg=Steam install of The Bazaar not found in the default library. Install will continue anyway: the patcher itself parses libraryfolders.vdf to find games in alternate Steam libraries.
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
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install --yes --steam-only"; \
    Description: "{cm:InstallNow}"; Flags: postinstall nowait skipifsilent runascurrentuser

[Code]
var
  SteamDetectedAt: String;

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
  // Default Steam library only — the C# patcher parses libraryfolders.vdf
  // for alternate libraries, so missing here is just cosmetic.
  Result := '';
  Steam := GetSteamInstallPath;
  if Steam = '' then exit;
  Candidate := Steam + '\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets';
  if DirExists(Candidate) and FileExists(Candidate + '\cards.json') then
    Result := Candidate;
end;

procedure InitializeWizard;
begin
  SteamDetectedAt := FindSteamGamePath;
  if SteamDetectedAt = '' then
    MsgBox(ExpandConstant('{cm:NotDetectedMsg}'), mbInformation, MB_OK);
end;
