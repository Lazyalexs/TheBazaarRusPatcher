; The Bazaar Russian Patcher — Tempo Launcher installer
; Builds: dist\TheBazaarRusPatcher-Tempo-<version>-setup.exe

#define MyAppName        "The Bazaar Russian Patcher (Tempo)"
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
DefaultDirName={autopf}\The Bazaar Russian Patcher (Tempo)
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=TheBazaarRusPatcher-Tempo-{#MyAppVersion}-setup
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
russian.DetectedFmt=Tempo Launcher найден: %1
russian.NotDetectedMsg=Tempo Launcher (бета) не обнаружен. Установка продолжится, патч можно применить позже вручную.
russian.InstallNow=Применить русификатор сразу после установки
russian.LaunchInteractive=Запустить патчер в интерактивном режиме после установки
english.DetectedFmt=Tempo Launcher detected at: %1
english.NotDetectedMsg=Tempo Launcher (Beta) not detected. Install will continue; apply the patch later manually.
english.InstallNow=Apply Russian patch immediately after install
english.LaunchInteractive=Launch the patcher in interactive mode after install

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppExeSource}"; DestDir: "{app}"; Flags: ignoreversion
Source: "publish-release\e_sqlite3.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Patch\translation-patch.json"; DestDir: "{app}\Patch"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "DISCLAIMER.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install --yes --tempo-only"; \
    Description: "{cm:InstallNow}"; Flags: postinstall nowait skipifsilent runascurrentuser; \
    Check: TempoDetected
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchInteractive}"; Flags: postinstall nowait skipifsilent runascurrentuser unchecked; \
    Check: not TempoDetected

[Code]
var
  TempoDetectedAt: String;

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

procedure InitializeWizard;
begin
  TempoDetectedAt := GetTempoPath;
  if TempoDetectedAt = '' then
    MsgBox(ExpandConstant('{cm:NotDetectedMsg}'), mbInformation, MB_OK);
end;

function TempoDetected: Boolean;
begin
  Result := TempoDetectedAt <> '';
end;
