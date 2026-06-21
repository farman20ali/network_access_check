$ErrorActionPreference = 'Stop';

$packageName = 'netcheck'

Write-Host "Uninstalling netcheck..."

# Use the Windows Add/Remove Programs to uninstall
# This attempts to find and run the official uninstaller that the NSIS installer created
$uninstallKeys = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\netcheck',
    'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\netcheck'
)

foreach ($key in $uninstallKeys) {
    if (Test-Path $key) {
        $uninstallString = (Get-ItemProperty $key).UninstallString
        if ($uninstallString) {
            Write-Host "Found uninstaller at: $uninstallString"
            # Run uninstaller with /S for silent mode (NSIS convention)
            Start-Process -FilePath $uninstallString -ArgumentList "/S" -Wait
            Write-Host "Uninstaller completed"
            break
        }
    }
}

Write-Host "netcheck has been removed."
