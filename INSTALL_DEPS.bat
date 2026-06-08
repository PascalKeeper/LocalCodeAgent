@echo off
REM One-click CUDA dependency install (GTX 1070 recommended path)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_deps.ps1" -Cuda
if errorlevel 1 (
    echo.
    echo Install failed. See logs\install_deps_*.log
    pause
    exit /b 1
)
echo.
echo Install complete. Place GGUF in models\ then run: python main.py
pause
