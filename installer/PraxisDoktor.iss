; Inno Setup script for PraxisDoktor v2
; Builds a single PraxisDoktorSetup.exe that installs the entire stack:
; bundled Postgres, embedded Python with all deps, the app, NSSM services,
; PWA assets. Auto-launches the browser at the end.
;
; Built by the GitHub Actions release workflow on windows-latest.

#define AppName       "PraxisDoktor"
#define AppPublisher  "Liminal Consulting"
#define AppURL        "https://github.com/LiminalConsulting/PraxisDoktor"
#define AppExeName    "praxisdoktor-launch.bat"

; Version is injected from CI: ISCC.exe /DAppVersion=2.0.0
#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif

[Setup]
AppId={{B6C2C8DF-8B17-4E3C-9F4F-9F76F8C0AAAA}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=auto
OutputBaseFilename=PraxisDoktorSetup-{#AppVersion}
OutputDir=output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
LicenseFile=..\LICENSE
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The CI build stages everything under installer\build\stage\
; which becomes the install root.
Source: "build\stage\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PraxisDoktor öffnen"; Filename: "http://localhost:8080"; IconFilename: "{app}\icon.ico"
Name: "{group}\PraxisDoktor (Browser)"; Filename: "{app}\open-browser.bat"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Logs öffnen"; Filename: "{app}\var\logs"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"
Name: "{commondesktop}\PraxisDoktor"; Filename: "http://localhost:8080"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
; Initialize Postgres data directory (idempotent)
Filename: "powershell.exe"; \
	Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\runtime\init-postgres.ps1"" -InstallRoot ""{app}"""; \
	StatusMsg: "Initialisiere Datenbank…"; Flags: runhidden

; If Ollama isn't installed, kick off its installer interactively so the
; user can complete it before service registration.
Filename: "{app}\OllamaSetup.exe"; \
	Description: "Ollama (KI-Laufzeit) installieren"; \
	StatusMsg: "Ollama installieren…"; \
	Check: NeedsOllama; \
	Flags: postinstall skipifsilent

; Run app initialization (alembic upgrade head + seed.py + ollama pull)
Filename: "powershell.exe"; \
	Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\runtime\init-app.ps1"" -InstallRoot ""{app}"""; \
	StatusMsg: "App-Initialisierung läuft (kann mehrere Minuten dauern, lädt KI-Modell)…"; \
	Flags: runhidden

; Register and start NSSM services
Filename: "powershell.exe"; \
	Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\runtime\install-services.ps1"" -InstallRoot ""{app}"""; \
	StatusMsg: "Dienste registrieren…"; Flags: runhidden

; Open the browser
Filename: "{app}\open-browser.bat"; \
	Description: "PraxisDoktor jetzt öffnen"; \
	Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; \
	Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\runtime\uninstall-services.ps1"" -InstallRoot ""{app}"""; \
	Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\var"

[Code]
function NeedsOllama: Boolean;
var
  Path: String;
begin
  Path := ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe');
  Result := not FileExists(Path);
end;
