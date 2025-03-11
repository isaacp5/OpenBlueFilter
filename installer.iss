[Setup]
AppName=OpenBlueFilter
AppVersion=1.0.0
WizardStyle=modern
DefaultDirName={autopf}\OpenBlueFilter
DefaultGroupName=OpenBlueFilter
UninstallDisplayIcon={app}\OpenBlueFilter.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\dist
OutputBaseFilename=OpenBlueFilter_Setup
SetupIconFile=resources\icon.png
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a &start menu icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startup"; Description: "Run on Windows startup"; GroupDescription: "Startup options:"; Flags: unchecked

[Files]
Source: "dist\OpenBlueFilter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"
Name: "{group}\Uninstall OpenBlueFilter"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"; Tasks: desktopicon
Name: "{commonstartmenu}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"; Tasks: startmenuicon
Name: "{commonstartup}\OpenBlueFilter"; Filename: "{app}\OpenBlueFilter.exe"; Tasks: startup

[Run]
Filename: "{app}\OpenBlueFilter.exe"; Description: "Launch OpenBlueFilter"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /f /im OpenBlueFilter.exe 2>nul"; Flags: runhidden 