@echo off
setlocal EnableExtensions
title LocalCodeAgent v2.7 - Continue Ship (Dependencies)

cd /d "%~dp0"

echo.
echo ============================================================
echo   LocalCodeAgent v2.7 - CONTINUE SHIP
echo   Dependency installer for GTX 1070 local stack
echo ============================================================
echo.
echo [1] Full install with CUDA llama-cpp  (recommended)
echo [2] Full install CPU-only llama-cpp
echo [3] Base deps only (skip llama-cpp)
echo [4] Verify installed packages
echo [Q] Quit
echo.

set /p CHOICE="Select option [1]: "
if "%CHOICE%"=="" set CHOICE=1
if /I "%CHOICE%"=="Q" goto :EOF
if /I "%CHOICE%"=="4" goto VERIFY

if "%CHOICE%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_deps.ps1" -Cuda
    goto DONE
)
if "%CHOICE%"=="2" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_deps.ps1" -CpuOnly
    goto DONE
)
if "%CHOICE%"=="3" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_deps.ps1" -SkipLlm
    goto DONE
)

echo Invalid choice. Defaulting to CUDA install...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_deps.ps1" -Cuda
goto DONE

:VERIFY
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\verify_deps.ps1"
goto DONE

:DONE
echo.
if errorlevel 1 (
    echo [ERROR] Install failed. Check logs\install_deps_*.log
) else (
    echo [OK] Ship step complete.
)
echo.
pause
endlocal
