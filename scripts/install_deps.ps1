# LocalCodeAgent v2.7 dependency installer (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== LocalCodeAgent v2.7 Dependency Install ===" -ForegroundColor Cyan
Set-Location $Root

python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "For CUDA acceleration on GTX 1070, reinstall llama-cpp-python with:" -ForegroundColor Yellow
Write-Host "  pip uninstall llama-cpp-python -y" -ForegroundColor Yellow
Write-Host "  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124" -ForegroundColor Yellow
Write-Host ""
Write-Host "Place a GGUF model in: $Root\models" -ForegroundColor Green
