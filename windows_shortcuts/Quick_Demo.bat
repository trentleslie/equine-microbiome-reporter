@echo off
:: Quick Demo - Shows the pipeline with test data
color 0B
cls
echo ========================================
echo   EQUINE MICROBIOME REPORTER - DEMO
echo   See the pipeline in action!
echo ========================================
echo.
echo This will process test data to demonstrate
echo the pipeline capabilities.
echo.
echo Press any key to start the demo...
pause >nul

:: Run demo in WSL2
wsl -d Ubuntu -e bash -c "cd ~/equine-microbiome-reporter && conda activate equine-microbiome && ./demo.sh"

echo.
echo ========================================
echo Demo complete! Check the demo_output folder
echo ========================================
pause