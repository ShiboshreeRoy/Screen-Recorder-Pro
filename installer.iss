; -- Installer Script for Screen Recorder Pro --

[Setup]
AppName=Screen Recorder Pro
AppVersion=1.0
DefaultDirName={pf}\Screen Recorder Pro
DefaultGroupName=Screen Recorder Pro
OutputBaseFilename=ScreenRecorderProSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\screen_recorder.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion
; Add any additional resources here

[Icons]
Name: "{group}\Screen Recorder Pro"; Filename: "{app}\screen_recorder.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\screen_recorder.exe"; Description: "Launch Screen Recorder Pro"; Flags: nowait postinstall skipifsilent
