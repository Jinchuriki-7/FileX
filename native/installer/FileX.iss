; Script generated for FileX Windows Desktop Application
; Inno Setup 6 Script

#define MyAppName "FileX"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "FileX Software"
#define MyAppURL "https://github.com/Jinchuriki-7/FileX"
#define MyAppExeName "FileX.exe"
#define MyAppSourceDir "..\..\dist\FileX"

[Setup]
; Basic Application Info
AppId={{5C1D8269-8A15-46D4-A57E-692B45CD9F3C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Architecture
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; Output
OutputDir=..\dist\installer
OutputBaseFilename=FileX_Setup
SetupIconFile=..\..\assets\images\logo.ico
UninstallDisplayIcon={app}\assets\images\logo.ico

; Compression & Styling
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Visual Branding
DisableWelcomePage=no
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Launch FileX automatically on Windows startup"; GroupDescription: "Windows Integration:"; Flags: unchecked

[Files]
; Standalone Windows Application files
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\images\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\images\logo.ico"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon; IconFilename: "{app}\assets\images\logo.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\FileX"
