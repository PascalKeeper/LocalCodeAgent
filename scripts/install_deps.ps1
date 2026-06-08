# LocalCodeAgent v2.7 — full dependency ship installer (Windows)
# Usage:
#   .\scripts\install_deps.ps1              # CPU llama-cpp + all deps
#   .\scripts\install_deps.ps1 -Cuda        # GTX 1070 CUDA wheel (recommended)
#   .\scripts\install_deps.ps1 -SkipLlm     # RAG/scanner deps only
param(
    [switch]$Cuda,
    [switch]$CpuOnly,
    [switch]$SkipLlm
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "install_deps_$Stamp.log"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $Message -ForegroundColor $Color
}

function Test-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        throw "Python not found on PATH. Install Python 3.11+ and re-run."
    }
    $version = (python --version 2>&1).ToString().Trim()
    Write-Log "Detected $version" "Cyan"
}

function Ensure-Dirs {
    $dirs = @(
        (Join-Path $Root "models"),
        (Join-Path $Root "Projects"),
        (Join-Path $Root "RAG_Index"),
        (Join-Path $Root "prompts"),
        (Join-Path $Root "logs")
    )
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "Created directory: $dir" "Green"
        }
    }
}

function Install-Requirements {
    Write-Log "Upgrading pip..." "Cyan"
    python -m pip install --upgrade pip

    Write-Log "Installing base requirements (colorama, chromadb, pypdf, pyinstaller)..." "Cyan"
    python -m pip install "colorama>=0.4.6" "chromadb>=0.5.23" "pypdf>=5.1.0" "pyinstaller>=6.3.0"
}

function Install-LlamaCpp {
    if ($SkipLlm) {
        Write-Log "Skipping llama-cpp-python (-SkipLlm)" "Yellow"
        return
    }

    if ($Cuda) {
        Write-Log "Installing llama-cpp-python with CUDA (GTX 1070 / cu124 wheel)..." "Cyan"
        python -m pip uninstall llama-cpp-python -y 2>$null | Out-Null
        python -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
        return
    }

    if ($CpuOnly) {
        Write-Log "Installing llama-cpp-python (CPU build)..." "Cyan"
        python -m pip install "llama-cpp-python>=0.3.4"
        return
    }

    Write-Log "Installing llama-cpp-python (CPU build). Use -Cuda for GTX 1070 GPU acceleration." "Cyan"
    python -m pip install "llama-cpp-python>=0.3.4"
}

function Test-Imports {
    $checks = @(
        @{ Name = "colorama"; Code = "import colorama; print(colorama.__version__)" },
        @{ Name = "chromadb"; Code = "import chromadb; print(chromadb.__version__)" },
        @{ Name = "pypdf";    Code = "import pypdf; print(pypdf.__version__)" }
    )

    if (-not $SkipLlm) {
        $checks += @{ Name = "llama_cpp"; Code = "import llama_cpp; print('ok')" }
    }

    $failed = @()
    foreach ($check in $checks) {
        $out = python -c $check.Code 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log ("  OK  {0} -> {1}" -f $check.Name, $out) "Green"
        } else {
            $failed += $check.Name
            Write-Log ("  FAIL {0} -> {1}" -f $check.Name, $out) "Red"
        }
    }

    if ($failed.Count -gt 0) {
        throw "Import verification failed for: $($failed -join ', ')"
    }
}

function Show-NextSteps {
    Write-Log "" 
    Write-Log "=== LocalCodeAgent v2.7 — Install Complete ===" "Green"
    Write-Log "1. Place a quantized GGUF model in: $Root\models" "Yellow"
    Write-Log "   Recommended: Q4_K_M (fits GTX 1070 8GB VRAM)" "Yellow"
    Write-Log "2. Set config.json -> llm.model_filename to your .gguf name" "Yellow"
    Write-Log "3. Run agent:  python main.py" "Yellow"
    Write-Log "4. Build EXE:  pyinstaller LocalCodeAgent.spec" "Yellow"
    Write-Log "Log saved: $LogFile" "Cyan"
}

Set-Location $Root
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

Write-Log "=== LocalCodeAgent v2.7 Dependency Ship ===" "Cyan"
Write-Log "Root: $Root" "Cyan"

Test-Python
Ensure-Dirs
Install-Requirements
Install-LlamaCpp
Test-Imports
Show-NextSteps

exit 0
