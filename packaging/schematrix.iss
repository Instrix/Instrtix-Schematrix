; Inno Setup script for the Windows installer; packaging/package.py passes Version, Source and OutDir.
;   ISCC /DVersion=0.2.1 /DSource=dist\Schematrix /DOutDir=dist\release packaging\schematrix.iss
#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6E0B3C2A-5F4D-4B7E-9C1A-3D8F2E7A9B41}
AppName=Schematrix
AppVersion={#Version}
AppPublisher=Instrix
AppPublisherURL=https://github.com/Instrix/Instrtix-Schematrix
DefaultDirName={autopf}\Schematrix
DefaultGroupName=Schematrix
DisableProgramGroupPage=yes
; installs for the current user without admin rights, or for everyone when run as admin
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutDir}
OutputBaseFilename=Schematrix-Setup
SetupIconFile=schematrix.ico
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\Schematrix.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Source}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Schematrix"; Filename: "{app}\Schematrix.exe"
Name: "{autodesktop}\Schematrix"; Filename: "{app}\Schematrix.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Schematrix.exe"; Description: "{cm:LaunchProgram,Schematrix}"; Flags: nowait postinstall skipifsilent
