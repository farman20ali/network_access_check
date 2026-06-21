!define PRODUCT_NAME "netcheck"
!define PRODUCT_VERSION "{version}"
!define PRODUCT_PUBLISHER "Network Tools Team"
!define PRODUCT_WEB_SITE "https://github.com/farman20ali/network_access_check"

SetCompressor lzma

Name "${PRODUCT_NAME}"
OutFile "dist\\win\\netcheck-${PRODUCT_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES64\\${PRODUCT_NAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\win\\netcheck.exe"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_VERSION}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"

    # Add to system PATH (using registry)
    ReadRegStr $0 HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path"
    WriteRegExpandStr HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path" "$0;$INSTDIR"
    
    # Broadcast environment change (WM_SETTINGCHANGE)
    SendMessage 0x001A 0 0 /TIMEOUT=5000
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\netcheck.exe"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}"
SectionEnd
