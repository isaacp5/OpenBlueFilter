[Setup]
AppName=OpenBlueFilter
AppVersion=1.0
AppPublisher=Your Name
AppPublisherURL=https://github.com/yourusername/OpenBlueFilter
DefaultDirName={autopf}\OpenBlueFilter
DefaultGroupName=OpenBlueFilter
UninstallDisplayIcon={app}\OpenBlueFilter.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=OpenBlueFilter_Setup
; SetupIconFile=resources\icon.png  ; PNG is not supported, needs ICO format

[Files]
; Single file executable
Source: "dist\OpenBlueFilter.exe"; DestDir: "{app}"; Flags: ignoreversion
; Resources folder
Source: "resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include src directory to resolve imports
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"
Name: "{autoprograms}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"
Name: "{autodesktop}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"

[Run]
Filename: "{app}\OpenBlueFilter.exe"; Description: "Launch OpenBlueFilter"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "OpenBlueFilter"; ValueData: """{app}\OpenBlueFilter.exe"""; Flags: uninsdeletevalue