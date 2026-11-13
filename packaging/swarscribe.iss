; Inno Setup script: turns dist\swarscribe.exe into a real installer
; with a Start Menu entry. Build the exe first (build-windows.bat),
; then compile this file with Inno Setup 6.
[Setup]
AppName=SwarScribe
AppVersion=0.6.0
AppPublisher=Saif Modan
AppPublisherURL=https://www.devbysaif.in/
DefaultDirName={autopf}\SwarScribe
DefaultGroupName=SwarScribe
OutputBaseFilename=SwarScribe-Setup
Compression=lzma
SolidCompression=yes
LicenseFile=..\LICENSE

[Files]
Source: "..\dist\swarscribe.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SwarScribe"; Filename: "{app}\swarscribe.exe"
Name: "{group}\SwarScribe Tray"; Filename: "{app}\swarscribe.exe"; Parameters: "tray"
