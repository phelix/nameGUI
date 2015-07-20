#define version "0.2"

#define sourceFolder "dist\nameguiwin"
#define progname "nameGUI"
#define exefile "nameguiwin.exe"

[Messages]
WelcomeLabel2=%nThis will install [name/ver] on your computer.%n
ConfirmUninstall=Are you sure you want to remove %1?%n%nThis will leave logs and name_new database files alone.
UninstalledAll=%1 was successfully removed from your computer.%n%nThere might still be logs and data in %APPDATA%\nameGUI

[Setup]
AppVerName={#progname} {#version}
AppName={#progname}
DefaultDirName={pf}\{#progname}
DefaultGroupName={#progname}
UninstallDisplayIcon={uninstallexe}
Compression=lzma2/ultra
SolidCompression=yes
OutputDir=.\installer
OutputBaseFilename={#progname}_v{#version}_setup

[Files]
Source: "{#sourceFolder}\{#exefile}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#sourceFolder}\*.*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Tasks]
Name: quicklaunchicon; Description: "Create a &Quick Launch icon for the current user"; Flags: unchecked

Name: desktopicon; Description: "Create a &desktop icon"
Name: desktopicon\common; Description: "For all users"; Flags: exclusive unchecked
Name: desktopicon\user; Description: "For the current user only"; Flags: exclusive unchecked

[Icons]
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#progname}"; Filename: "{app}\{#exefile}"; Tasks: quicklaunchicon

Name: "{group}\{#progname}"; Filename: "{app}\{#exefile}"
Name: "{commondesktop}\{#progname}"; Filename: "{app}\{#exefile}"; Tasks: desktopicon\common
Name: "{userdesktop}\{#progname}"; Filename: "{app}\{#exefile}"; Tasks: desktopicon\user

Name: "{group}\uninstall"; Filename: "{uninstallexe}";

[Run]
Filename: "{app}\{#exefile}"; Description: "Launch application"; Flags: postinstall skipifsilent nowait
