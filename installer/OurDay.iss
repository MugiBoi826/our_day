#define MyAppName "Our Day"
#define MyAppVersion "0.27.0"
#define MyAppPublisher "Our Day"
#define MyAppExeName "OurDay.exe"

[Setup]
AppId={{F86CCAA9-D317-4B0A-81FE-06D5C86D5CE8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Our Day
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer-dist
OutputBaseFilename=OurDay-Setup-{#MyAppVersion}
SetupIconFile=..\assets\our_day.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\OurDay.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Our Day"; Filename: "{app}\OurDay.exe"; WorkingDir: "{app}"; IconFilename: "{app}\OurDay.exe"
Name: "{autodesktop}\Our Day"; Filename: "{app}\OurDay.exe"; WorkingDir: "{app}"; IconFilename: "{app}\OurDay.exe"

[Run]
Filename: "{app}\OurDay.exe"; Description: "Our Day indítása"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
