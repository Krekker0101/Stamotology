[Setup]
AppName=Стоматология
AppVersion=1.0.0
DefaultDirName={pf}\Стоматология
DefaultGroupName=Стоматология
OutputBaseFilename=LaboratoryManagementSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\LaboratoryManagement.exe
SetupIconFile=img\logo.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked

[Files]
Source: "dist\LaboratoryManagement.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "img\logo.png"; DestDir: "{app}\img"; Flags: ignoreversion
Source: "img\logo.ico"; DestDir: "{app}\img"; Flags: ignoreversion
Source: "img\logo.svg"; DestDir: "{app}\img"; Flags: ignoreversion

[Icons]
Name: "{group}\Стоматология"; Filename: "{app}\LaboratoryManagement.exe"; IconFilename: "{app}\img\logo.ico"
Name: "{group}\Удалить Стоматология"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Стоматология"; Filename: "{app}\LaboratoryManagement.exe"; IconFilename: "{app}\img\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\LaboratoryManagement.exe"; Description: "Запустить Стоматология"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{app}\data"
Name: "{app}\backups"
Name: "{app}\files"
Name: "{app}\img"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create empty database file if it doesn't exist
    if not FileExists(ExpandConstant('{app}\data\laboratory.db')) then
    begin
      FileCreate(ExpandConstant('{app}\data\laboratory.db'));
    end;
  end;
end;
