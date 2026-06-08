# LocalCodeAgent v2.7 — dependency verification only
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== LocalCodeAgent v2.7 Dependency Verify ===" -ForegroundColor Cyan
Set-Location $Root

function Test-Module {
    param([string]$Name, [string]$Code)
    try {
        $out = python -c $Code 2>&1
        if ($LASTEXITCODE -ne 0) { throw $out }
        Write-Host ("  OK   {0,-12} {1}" -f $Name, $out) -ForegroundColor Green
        return $true
    } catch {
        Write-Host ("  MISS {0,-12} not installed or import failed" -f $Name) -ForegroundColor Red
        return $false
    }
}

python --version
Write-Host ""

$allOk = $true
$allOk = (Test-Module "colorama"  "import colorama; print(colorama.__version__)") -and $allOk
$allOk = (Test-Module "chromadb"  "import chromadb; print(chromadb.__version__)") -and $allOk
$allOk = (Test-Module "pypdf"     "import pypdf; print(pypdf.__version__)") -and $allOk
$allOk = (Test-Module "PyInstaller" "import PyInstaller; print(PyInstaller.__version__)") -and $allOk
$allOk = (Test-Module "llama_cpp" "import llama_cpp; print('ready')") -and $allOk

$modelDir = Join-Path $Root "models"
$gguf = Get-ChildItem -Path $modelDir -Filter "*.gguf" -ErrorAction SilentlyContinue
if ($gguf) {
    Write-Host ("  OK   GGUF model   {0}" -f $gguf[0].Name) -ForegroundColor Green
} else {
    Write-Host "  MISS GGUF model   place .gguf in models\" -ForegroundColor Yellow
}

Write-Host ""
if ($allOk) {
    Write-Host "All Python dependencies verified. Run: python main.py" -ForegroundColor Green
    exit 0
}

Write-Host "Some dependencies missing. Run CONTINUE_SHIP.bat option 1." -ForegroundColor Yellow
exit 1
