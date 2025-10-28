@echo off
:: Update Pipeline - Pull latest changes from GitHub
color 0E
cls
echo ========================================
echo   UPDATING EQUINE MICROBIOME REPORTER
echo ========================================
echo.
echo This will download the latest updates
echo from GitHub.
echo.
echo Press any key to continue...
pause >nul

:: Pull updates in WSL2
echo.
echo Checking for updates...
wsl -d Ubuntu -e bash -c "cd ~/equine-microbiome-reporter && git pull origin main"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Update successful!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   Update failed - please check your
    echo   internet connection
    echo ========================================
)

echo.
pause