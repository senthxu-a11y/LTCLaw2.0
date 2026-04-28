; LTCLAW-GY.X Desktop NSIS installer. Run makensis from repo root after
; building dist/win-unpacked (see scripts/pack/build_win.ps1).
; Usage: makensis /DQWENPAW_VERSION=1.2.3 /DOUTPUT_EXE=dist\LTCLAW-GY.X-Setup-1.2.3.exe scripts\pack\desktop.nsi

!include "MUI2.nsh"
!define MUI_ABORTWARNING
; Use custom icon from unpacked env (copied by build_win.ps1)
!define MUI_ICON "${UNPACKED}\icon.ico"
!define MUI_UNICON "${UNPACKED}\icon.ico"

!ifndef QWENPAW_VERSION
  !define QWENPAW_VERSION "0.0.0"
!endif
!ifndef OUTPUT_EXE
  !define OUTPUT_EXE "dist\LTCLAW-GY.X-Setup-${QWENPAW_VERSION}.exe"
!endif

Name "LTCLAW-GY.X Desktop"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\LTCLAW-GY.X"
InstallDirRegKey HKCU "Software\LTCLAW-GY.X" "InstallPath"
RequestExecutionLevel user

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

; Pass /DUNPACKED=full_path from build_win.ps1 so path works when cwd != repo root
!ifndef UNPACKED
  !define UNPACKED "dist\win-unpacked"
!endif

Section "LTCLAW-GY.X Desktop" SEC01
  SetOutPath "$INSTDIR"
  File /r "${UNPACKED}\*.*"
  WriteRegStr HKCU "Software\LTCLAW-GY.X" "InstallPath" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Main shortcut - uses VBS to hide console window
  CreateShortcut "$SMPROGRAMS\LTCLAW-GY.X Desktop.lnk" "$INSTDIR\LTCLAW-GY.X Desktop.vbs" "" "$INSTDIR\icon.ico" 0
  CreateShortcut "$DESKTOP\LTCLAW-GY.X Desktop.lnk" "$INSTDIR\LTCLAW-GY.X Desktop.vbs" "" "$INSTDIR\icon.ico" 0
  
  ; Debug shortcut - shows console window for troubleshooting
  CreateShortcut "$SMPROGRAMS\LTCLAW-GY.X Desktop (Debug).lnk" "$INSTDIR\LTCLAW-GY.X Desktop (Debug).bat" "" "$INSTDIR\icon.ico" 0
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\LTCLAW-GY.X Desktop.lnk"
  Delete "$SMPROGRAMS\LTCLAW-GY.X Desktop (Debug).lnk"
  Delete "$DESKTOP\LTCLAW-GY.X Desktop.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\LTCLAW-GY.X"
SectionEnd
