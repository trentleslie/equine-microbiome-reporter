@echo off
:: Equine Microbiome Reporter - Process Samples
:: Double-click to run the pipeline on your FASTQ files

color 0A
cls
echo ========================================
echo   EQUINE MICROBIOME REPORTER
echo   HippoVet+ Automated Pipeline
echo ========================================
echo.

:: Check if WSL2 is available
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: WSL2 is not installed or not running
    echo Please install WSL2 first
    pause
    exit /b 1
)

:: Set default paths (user can modify these)
set "INPUT_DIR=C:\Users\%USERNAME%\Desktop\fastq_files"
set "OUTPUT_DIR=C:\Users\%USERNAME%\Desktop\results_%date:~-4,4%%date:~-10,2%%date:~-7,2%"

:: Ask user for input directory
echo Current input directory: %INPUT_DIR%
echo.
set /p "CUSTOM_INPUT=Enter FASTQ directory path (or press Enter for default): "
if not "%CUSTOM_INPUT%"=="" set "INPUT_DIR=%CUSTOM_INPUT%"

:: Ask user for output directory  
echo.
echo Output will be saved to: %OUTPUT_DIR%
set /p "CUSTOM_OUTPUT=Enter output directory (or press Enter for default): "
if not "%CUSTOM_OUTPUT%"=="" set "OUTPUT_DIR=%CUSTOM_OUTPUT%"

:: Convert Windows paths to WSL paths
set "WSL_INPUT=/mnt/%INPUT_DIR:~0,1%/%INPUT_DIR:~3%"
set "WSL_OUTPUT=/mnt/%OUTPUT_DIR:~0,1%/%OUTPUT_DIR:~3%"
set "WSL_INPUT=%WSL_INPUT:\=/%"
set "WSL_OUTPUT=%WSL_OUTPUT:\=/%"

:: Show what will be processed
echo.
echo ========================================
echo Processing Configuration:
echo Input:  %INPUT_DIR%
echo Output: %OUTPUT_DIR%
echo ========================================
echo.
echo Press any key to start processing...
pause >nul

:: Run the pipeline in WSL2
echo.
echo Starting pipeline...
echo.

wsl -d Ubuntu -e bash -c "cd ~/equine-microbiome-reporter && conda activate equine-microbiome && python scripts/full_pipeline.py --input-dir '%WSL_INPUT%' --output-dir '%WSL_OUTPUT%' 2>&1 | tee -a pipeline.log"

:: Check if successful
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS! Processing complete
    echo ========================================
    echo.
    echo Results saved to: %OUTPUT_DIR%
    echo.
    echo Opening results folder...
    explorer "%OUTPUT_DIR%"
    
    :: Open Excel files if they exist
    if exist "%OUTPUT_DIR%\excel_review\*.xlsx" (
        echo Opening Excel files for review...
        start "" "%OUTPUT_DIR%\excel_review\"
    )
) else (
    echo.
    echo ========================================
    echo   ERROR: Pipeline failed
    echo ========================================
    echo Check pipeline.log for details
)

echo.
echo Press any key to exit...
pause >nul