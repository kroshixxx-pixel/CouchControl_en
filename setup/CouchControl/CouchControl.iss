#define MyAppName "CouchControl"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "CouchControl"

[Setup]
AppId={{B1A5E3D4-8A27-4F2A-9A6C-CC0123A45D67}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\CouchControl
DefaultGroupName=CouchControl
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=CouchControl-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional tasks:"; Flags: checkedonce
Name: "autostart"; Description: "Start CouchControl automatically when you sign in to Windows"; GroupDescription: "Additional tasks:"; Flags: checkedonce

[Files]
Source: "bot.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "web_server.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "install.ps1"; DestDir: "{app}"; Flags: ignoreversion; AfterInstall: InstallRuntime
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CouchControl"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\bot.py"""; WorkingDir: "{app}"
Name: "{autodesktop}\CouchControl"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\bot.py"""; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\CouchControl"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\bot.py"""; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\bot.py"""; WorkingDir: "{app}"; Description: "Launch CouchControl now"; Flags: nowait postinstall skipifsilent

[Code]
var
  TelegramPage: TInputQueryWizardPage;

procedure InstallRuntime;
var
  ResultCode: Integer;
  PowerShellPath: String;
  Parameters: String;
begin
  PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Parameters := '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{app}\install.ps1') + '"';

  if not Exec(PowerShellPath, Parameters, ExpandConstant('{app}'),
    SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    RaiseException('Could not start the Python and CouchControl component setup.');

  if ResultCode <> 0 then
    RaiseException('CouchControl installation failed. Exit code: ' +
      IntToStr(ResultCode) + '. Check the log in the TEMP folder.');
end;

procedure InitializeWizard;
begin
  TelegramPage := CreateInputQueryPage(wpSelectDir,
    'Telegram setup',
    'Enter your Telegram bot details',
    'Get a token from @BotFather using /newbot. ' +
    'You can find your numeric Telegram User ID using @userinfobot.');
  TelegramPage.Add('Bot Token:', True);
  TelegramPage.Add('Telegram User ID:', False);
end;

function IsDigitsOnly(const S: string): Boolean;
var
  I: Integer;
begin
  Result := (S <> '');
  for I := 1 to Length(S) do
    if (S[I] < '0') or (S[I] > '9') then
    begin
      Result := False;
      Exit;
    end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = TelegramPage.ID then
  begin
    if Trim(TelegramPage.Values[0]) = '' then
    begin
      MsgBox('Enter your Telegram bot token.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsDigitsOnly(Trim(TelegramPage.Values[1])) or
       (Trim(TelegramPage.Values[1]) = '0') then
    begin
      MsgBox('Enter a numeric Telegram User ID.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvText: string;
begin
  if CurStep = ssPostInstall then
  begin
    EnvText := 'BOT_TOKEN=' + Trim(TelegramPage.Values[0]) + #13#10 +
               'ALLOWED_USER_ID=' + Trim(TelegramPage.Values[1]) + #13#10;
    if not SaveStringToFile(ExpandConstant('{app}\.env'), EnvText, False) then
      RaiseException('Could not save Telegram settings to .env');
  end;
end;
