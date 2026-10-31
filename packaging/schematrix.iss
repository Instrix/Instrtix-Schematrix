; Inno Setup script for the Windows installer; packaging/package.py passes Version, Source, OutDir and WebView2
; (Microsoft's WebView2 bootstrapper, run only on the rare Windows 10 without the WebView2 runtime).
;   ISCC /DVersion=0.2.2 /DSource=dist\Schematrix /DOutDir=dist\release /DWebView2=dist\MicrosoftEdgeWebview2Setup.exe packaging\schematrix.iss
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
Source: "{#WebView2}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: not WebView2Installed

[Icons]
Name: "{autoprograms}\Schematrix"; Filename: "{app}\Schematrix.exe"
Name: "{autodesktop}\Schematrix"; Filename: "{app}\Schematrix.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Installing Microsoft Edge WebView2 (the app window)..."; Flags: waituntilterminated; Check: not WebView2Installed
Filename: "{app}\Schematrix.exe"; Description: "{cm:LaunchProgram,Schematrix}"; Flags: nowait postinstall skipifsilent

[Code]
const WebView2Key = 'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function HasVersion(Root: Integer; Key: String): Boolean;
var V: String;
begin
  Result := RegQueryStringValue(Root, Key, 'pv', V) and (V <> '') and (V <> '0.0.0.0');
end;

// WebView2 ships with Windows 11 and updated Windows 10; install it only where it is missing
function WebView2Installed: Boolean;
begin
  Result := HasVersion(HKLM, 'SOFTWARE\WOW6432Node\' + WebView2Key) or HasVersion(HKLM, 'SOFTWARE\' + WebView2Key)
    or HasVersion(HKCU, 'Software\' + WebView2Key);
end;
