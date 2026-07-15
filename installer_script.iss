; Inno Setup Installer Script for Laboratory Management System
; This script creates a completely standalone Windows installer
; No external dependencies required - everything is included

#define AppName "Laboratory Management System"
#define AppVersion "1.0.0"
#define AppPublisher "Krekker0101"
#define AppExeName "LaboratoryManagement.exe"
#define AppIconPath "img\logo.ico"

[Setup]
; Basic setup information
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename=LaboratoryManagement_Setup
Compression=lzma2
SolidCompression=yes
; Installer icon
SetupIconFile={#AppIconPath}
; Modern UI
UninstallDisplayIcon={app}\{#AppExeName}
ChangesAssociations=no
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=yes
DisableWelcomePage=no
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes
ShowLanguageDialog=no
AppCopyright=Copyright © 2026 {#AppPublisher}
AppComments=Professional Laboratory Management System
AppContact=
; No external dependencies
PrivilegesRequired=admin
CreateAppDir=yes
UsePreviousAppDir=no
; Output settings
OutputDir=Output
; Ensure standalone - no internet required
SetupLogging=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Main application executable (standalone - includes all dependencies)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Include logo images
Source: "img\logo.png"; DestDir: "{app}\img"; Flags: ignoreversion
Source: "img\logo.ico"; DestDir: "{app}\img"; Flags: ignoreversion

[Icons]
; Start menu shortcut
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\img\logo.ico"; Comment: "Laboratory Management System"
; Desktop shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\img\logo.ico"; Tasks: desktopicon; Comment: "Laboratory Management System"
; Quick launch shortcut (Windows 7 and below)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\img\logo.ico"; Tasks: quicklaunchicon

[Run]
; Run the application after installation
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName,'&','&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Delete application directory on uninstall
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  // Ensure the application is not running during installation
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create additional directories if needed
    if not DirExists(ExpandConstant('{app}\data')) then
      CreateDir(ExpandConstant('{app}\data'));
    if not DirExists(ExpandConstant('{app}\backups')) then
      CreateDir(ExpandConstant('{app}\backups'));
    if not DirExists(ExpandConstant('{app}\reports')) then
      CreateDir(ExpandConstant('{app}\reports'));
    if not DirExists(ExpandConstant('{app}\files')) then
      CreateDir(ExpandConstant('{app}\files'));
  end;
end;
