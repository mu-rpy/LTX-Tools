@echo off
setlocal enabledelayedexpansion

if exist "src\data\.setup_done" goto :run_script

:setup
if exist "src\data\LICENSE" (
    type "src\data\LICENSE"
    echo.
)

set /p choice="Do you accept the license terms? (y/n): "
if /i "%choice%" neq "y" exit /b 0

echo [PHASE 2] Checking Python 3.10...
py -3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python 3.10 not found. Downloading...
    curl.exe -L -o python_installer.exe https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    echo [INFO] Installing Python 3.10...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

if not exist "src\ffmpeg.exe" (
    echo [INFO] Downloading FFmpeg...
    curl.exe -L -o ffmpeg.zip https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip
    powershell -Command "Expand-Archive -Path ffmpeg.zip -DestinationPath temp_ffmpeg -Force"
    for /r "temp_ffmpeg" %%i in (ffmpeg.exe) do move /y "%%i" "src\"
    rd /s /q temp_ffmpeg
    del /f /q ffmpeg.zip
)

echo [PHASE 3] Configuring AI Dependencies...
py -3.10 -m pip install --quiet --upgrade pip
py -3.10 -m pip install --quiet pipenv
cd src
pipenv --rm
pipenv --python 3.10
pipenv install diffusers transformers accelerate sentencepiece

:: Detect NVIDIA GPU
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] GPU detected. Installing CUDA 12.1 Torch...
    pipenv run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] No GPU found. Installing CPU Torch...
    pipenv run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

pipenv run python integrity.py
if %errorlevel% neq 0 (
    set /p cont="Integrity failed. Continue? (y/n): "
    if /i "!cont!" neq "y" exit /b 1
)
echo. > data\.setup_done
cd ..

:run_script
cls
set "ver_val=Unknown"
if exist "src\data\version" set /p ver_val=<"src\data\version"

echo [32m
type src\data\logo.txt
echo.
echo.
echo                                     [96mAuthor: Mu_rpy[0m
echo                                    [92mVersion: %ver_val%[0m
echo.
echo [0m1. Apply AI Filter
echo 2. Install Latest Updates
echo 3. Exit
echo.
set /p menu="Select an option (1-3): "

if "%menu%"=="1" (
    cd src && pipenv run python main.py
    cd ..
    goto :run_script
)
if "%menu%"=="2" (
    cd src && pipenv run python updater.py
    cd ..
    goto :run_script
)
if "%menu%"=="3" exit /b 0
goto :run_script