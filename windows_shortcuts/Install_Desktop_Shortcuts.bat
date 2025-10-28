@echo off
:: Install Desktop Shortcuts for Equine Microbiome Reporter
color 0A
cls
echo ========================================
echo   Installing Desktop Shortcuts
echo ========================================
echo.

:: Get the desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

:: Create shortcuts using PowerShell
echo Creating shortcuts on your desktop...

:: Main Pipeline shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Microbiome Pipeline.lnk'); $Shortcut.TargetPath = '%~dp0Pipeline_GUI.ps1'; $Shortcut.IconLocation = 'C:\Windows\System32\imageres.dll,3'; $Shortcut.Description = 'Process equine microbiome samples'; $Shortcut.Save()"

:: Process Samples shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Process Samples.lnk'); $Shortcut.TargetPath = '%~dp0Process_Samples.bat'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,145'; $Shortcut.Description = 'Process FASTQ files'; $Shortcut.Save()"

:: Quick Demo shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Pipeline Demo.lnk'); $Shortcut.TargetPath = '%~dp0Quick_Demo.bat'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,76'; $Shortcut.Description = 'Run pipeline demo'; $Shortcut.Save()"

:: Update shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Update Pipeline.lnk'); $Shortcut.TargetPath = '%~dp0Update_Pipeline.bat'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,238'; $Shortcut.Description = 'Update to latest version'; $Shortcut.Save()"

echo.
echo ========================================
echo   Shortcuts created successfully!
echo ========================================
echo.
echo The following shortcuts are now on your desktop:
echo.
echo   1. Microbiome Pipeline - Main GUI interface
echo   2. Process Samples - Quick batch processing
echo   3. Pipeline Demo - Test with sample data
echo   4. Update Pipeline - Get latest updates
echo.
echo ========================================
echo.
pause