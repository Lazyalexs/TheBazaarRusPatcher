; The Bazaar Russian Patcher — Steam installer
; Builds: dist\TheBazaarRusPatcher-Steam-<version>-setup.exe
;
; This installer puts the patcher TOOL into Program Files, then asks the
; user (or auto-detects) where their Steam copy of The Bazaar lives, and
; passes that path to the patcher via --game-path so non-standard Steam
; libraries are supported.

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
DisableDirPage=yes
DisableReadyPage=no
VersionInfoVersion=0.4.7.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
russian.GamePathCaption=Папка с игрой Steam
russian.GamePathDescription=Укажите папку StreamingAssets вашей копии The Bazaar (Steam). Это НЕ папка установки русификатора — патчер сам ставится в Program Files.
russian.GamePathLabel=Путь к StreamingAssets:
russian.GamePathHint=Обычно это: …\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets
russian.GamePathAutoDetected=Автоматически найдено: %1
russian.GamePathManual=Steam-копия не найдена автоматически. Укажите папку StreamingAssets вручную.
russian.GamePathInvalid=В выбранной папке нет cards.json. Это не похоже на StreamingAssets игры The Bazaar. Выберите другую папку.
russian.GamePathSkip=Пропустить и применить русификатор позже вручную
russian.InstallNow=Применить русификатор сразу после установки
russian.LaunchInteractive=Запустить патчер в интерактивном режиме после установки
english.GamePathCaption=Steam game folder
english.GamePathDescription=Point to the StreamingAssets folder of your Steam copy of The Bazaar. This is NOT the patcher's install directory — the patcher itself goes into Program Files.
english.GamePathLabel=Path to StreamingAssets:
english.GamePathHint=Typically: ...\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets
english.GamePathAutoDetected=Auto-detected: %1
english.GamePathManual=Steam install not auto-detected. Please point to the StreamingAssets folder manually.
english.GamePathInvalid=The selected folder has no cards.json. This does not look like a StreamingAssets folder for The Bazaar. Pick another folder.
english.GamePathSkip=Skip and apply the patch manually later
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
Filename: "{app}\{#MyAppExeName}"; Parameters: "{code:GetPatchArgs}"; \
    Description: "{cm:InstallNow}"; Flags: postinstall nowait skipifsilent runascurrentuser; \
    Check: ShouldAutoApply
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchInteractive}"; Flags: postinstall nowait skipifsilent runascurrentuser unchecked; \
    Check: not ShouldAutoApply

[Code]
var
  GamePathPage: TWizardPage;
  GamePathEdit: TEdit;
  GamePathBrowse: TButton;
  GamePathHint: TLabel;
  GamePathStatus: TLabel;
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

function TryCandidate(const Library: String; var Found: String): Boolean;
var
  Candidate: String;
begin
  Result := False;
  Candidate := Library + '\steamapps\common\The Bazaar\TheBazaar_Data\StreamingAssets';
  if DirExists(Candidate) and FileExists(Candidate + '\cards.json') then
  begin
    Found := Candidate;
    Result := True;
  end;
end;

function ParseLibraryFolders(const VdfPath: String; var Libraries: TArrayOfString): Boolean;
var
  Lines: TArrayOfString;
  i, p1, p2: Integer;
  Line, PathStr: String;
begin
  Result := False;
  SetArrayLength(Libraries, 0);
  if not LoadStringsFromFile(VdfPath, Lines) then exit;
  for i := 0 to GetArrayLength(Lines) - 1 do
  begin
    Line := Trim(Lines[i]);
    if Pos('"path"', LowerCase(Line)) = 0 then continue;
    p1 := Pos('"', Line);
    if p1 = 0 then continue;
    // skip past "path"
    p1 := Pos('"', Copy(Line, p1 + 1, Length(Line))) + p1;
    if p1 <= 1 then continue;
    p2 := Pos('"', Copy(Line, p1 + 1, Length(Line)));
    if p2 = 0 then continue;
    p1 := Pos('"', Copy(Line, p1 + 1, Length(Line))) + p1;
    if p1 <= 1 then continue;
    p2 := Pos('"', Copy(Line, p1 + 1, Length(Line)));
    if p2 = 0 then continue;
    PathStr := Copy(Line, p1 + 1, p2 - 1);
    StringChangeEx(PathStr, '\\', '\', True);
    if PathStr <> '' then
    begin
      SetArrayLength(Libraries, GetArrayLength(Libraries) + 1);
      Libraries[GetArrayLength(Libraries) - 1] := PathStr;
    end;
  end;
  Result := GetArrayLength(Libraries) > 0;
end;

function FindSteamGamePath: String;
var
  Steam, Vdf: String;
  Libraries: TArrayOfString;
  i: Integer;
begin
  Result := '';
  Steam := GetSteamInstallPath;
  if Steam <> '' then
  begin
    if TryCandidate(Steam, Result) then exit;
    Vdf := Steam + '\steamapps\libraryfolders.vdf';
    if FileExists(Vdf) and ParseLibraryFolders(Vdf, Libraries) then
    begin
      for i := 0 to GetArrayLength(Libraries) - 1 do
        if TryCandidate(Libraries[i], Result) then exit;
    end;
  end;
end;

function IsValidGamePath(const P: String): Boolean;
begin
  Result := (P <> '') and DirExists(P) and FileExists(P + '\cards.json');
end;

procedure UpdateGamePathStatus;
var
  P: String;
begin
  if GamePathStatus = nil then exit;
  P := Trim(GamePathEdit.Text);
  if P = '' then
  begin
    GamePathStatus.Caption := '';
    GamePathStatus.Font.Color := clWindowText;
    exit;
  end;
  if IsValidGamePath(P) then
  begin
    GamePathStatus.Caption := 'OK: cards.json найден';
    GamePathStatus.Font.Color := clGreen;
  end
  else
  begin
    GamePathStatus.Caption := ExpandConstant('{cm:GamePathInvalid}');
    GamePathStatus.Font.Color := clRed;
  end;
end;

procedure GamePathEditChange(Sender: TObject);
begin
  UpdateGamePathStatus;
end;

procedure GamePathBrowseClick(Sender: TObject);
var
  Selected: String;
begin
  Selected := GamePathEdit.Text;
  if BrowseForFolder(ExpandConstant('{cm:GamePathLabel}'), Selected, False) then
  begin
    GamePathEdit.Text := Selected;
    UpdateGamePathStatus;
  end;
end;

procedure InitializeWizard;
var
  Hint: String;
begin
  SteamDetectedAt := FindSteamGamePath;

  GamePathPage := CreateCustomPage(
    wpSelectTasks,
    ExpandConstant('{cm:GamePathCaption}'),
    ExpandConstant('{cm:GamePathDescription}'));

  GamePathHint := TLabel.Create(GamePathPage);
  GamePathHint.Parent := GamePathPage.Surface;
  GamePathHint.Left := 0;
  GamePathHint.Top := 0;
  GamePathHint.Width := GamePathPage.SurfaceWidth;
  GamePathHint.AutoSize := False;
  GamePathHint.Height := ScaleY(34);
  GamePathHint.WordWrap := True;
  if SteamDetectedAt <> '' then
    Hint := Format(ExpandConstant('{cm:GamePathAutoDetected}'), [SteamDetectedAt])
  else
    Hint := ExpandConstant('{cm:GamePathManual}');
  GamePathHint.Caption := Hint + #13#10 + ExpandConstant('{cm:GamePathHint}');

  GamePathEdit := TEdit.Create(GamePathPage);
  GamePathEdit.Parent := GamePathPage.Surface;
  GamePathEdit.Left := 0;
  GamePathEdit.Top := ScaleY(44);
  GamePathEdit.Width := GamePathPage.SurfaceWidth - ScaleX(90);
  GamePathEdit.Text := SteamDetectedAt;
  GamePathEdit.OnChange := @GamePathEditChange;

  GamePathBrowse := TButton.Create(GamePathPage);
  GamePathBrowse.Parent := GamePathPage.Surface;
  GamePathBrowse.Left := GamePathPage.SurfaceWidth - ScaleX(85);
  GamePathBrowse.Top := ScaleY(42);
  GamePathBrowse.Width := ScaleX(85);
  GamePathBrowse.Height := ScaleY(23);
  GamePathBrowse.Caption := ExpandConstant('{cm:ButtonBrowse}');
  GamePathBrowse.OnClick := @GamePathBrowseClick;

  GamePathStatus := TLabel.Create(GamePathPage);
  GamePathStatus.Parent := GamePathPage.Surface;
  GamePathStatus.Left := 0;
  GamePathStatus.Top := ScaleY(76);
  GamePathStatus.Width := GamePathPage.SurfaceWidth;
  GamePathStatus.AutoSize := False;
  GamePathStatus.Height := ScaleY(48);
  GamePathStatus.WordWrap := True;

  UpdateGamePathStatus;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  P: String;
begin
  Result := True;
  if CurPageID = GamePathPage.ID then
  begin
    P := Trim(GamePathEdit.Text);
    if P = '' then
    begin
      // empty is allowed — patcher will skip Steam install, user does it later
      Result := True;
      exit;
    end;
    if not IsValidGamePath(P) then
    begin
      MsgBox(ExpandConstant('{cm:GamePathInvalid}'), mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function GetChosenGamePath: String;
begin
  if GamePathEdit = nil then
    Result := SteamDetectedAt
  else
    Result := Trim(GamePathEdit.Text);
end;

function ShouldAutoApply: Boolean;
begin
  Result := IsValidGamePath(GetChosenGamePath);
end;

function GetPatchArgs(Param: String): String;
var
  P: String;
begin
  P := GetChosenGamePath;
  if IsValidGamePath(P) then
    Result := '--install --yes --steam-only --game-path "' + P + '"'
  else
    Result := '--install --yes --steam-only';
end;
