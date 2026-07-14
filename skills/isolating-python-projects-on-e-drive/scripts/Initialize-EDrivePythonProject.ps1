[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$PythonVersion = '3.12',

    [string]$Proxy = '',

    [switch]$SkipSync
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv is not available on PATH.'
}

$fullProjectPath = [System.IO.Path]::GetFullPath($ProjectPath)
if ([System.IO.Path]::GetPathRoot($fullProjectPath) -ne 'E:\') {
    throw "ProjectPath must be on E:; received '$fullProjectPath'."
}

New-Item -ItemType Directory -Force -Path $fullProjectPath | Out-Null
. "$PSScriptRoot\Enter-EDrivePythonProject.ps1" -ProjectPath $fullProjectPath -Proxy $Proxy | Out-Null

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Assert-EPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path.Trim())
    if ([System.IO.Path]::GetPathRoot($fullPath) -ne 'E:\') {
        throw "$Name escapes E: and resolves to '$fullPath'."
    }
}

function Ensure-GitIgnoreEntry {
    param([string]$Entry)

    $gitIgnore = Join-Path $fullProjectPath '.gitignore'
    $existing = if (Test-Path -LiteralPath $gitIgnore) {
        [System.IO.File]::ReadAllText($gitIgnore)
    }
    else {
        ''
    }

    $lines = $existing -split "`r?`n"
    if ($lines -notcontains $Entry) {
        $prefix = if ($existing -and -not $existing.EndsWith("`n")) { "`n" } else { '' }
        $utf8 = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::AppendAllText($gitIgnore, "$prefix$Entry`n", $utf8)
    }
}

Invoke-NativeChecked -Description 'uv managed Python installation' -Command {
    uv python install $PythonVersion --no-bin --no-registry
}

if (-not (Test-Path -LiteralPath (Join-Path $fullProjectPath 'pyproject.toml'))) {
    Invoke-NativeChecked -Description 'uv project initialization' -Command {
        uv init --python $PythonVersion --vcs git .
    }
}

$venvConfig = Join-Path $fullProjectPath '.venv\pyvenv.cfg'
if (-not (Test-Path -LiteralPath $venvConfig)) {
    Invoke-NativeChecked -Description 'virtual environment creation' -Command {
        uv venv --python $PythonVersion --managed-python --allow-existing .venv
    }
}

if (-not $SkipSync) {
    Invoke-NativeChecked -Description 'dependency synchronization' -Command {
        uv sync
    }
}

@(
    '.venv/'
    '.home/'
    '.cache/'
    '.tmp/'
    '.uv-cache/'
    '.uv-python/'
    '.uv-python-bin/'
    '.uv-tools/'
    '.uv-tool-bin/'
    '.python-user/'
    '.pycache/'
    '.xdg/'
    '.cargo/'
    '.rustup/'
) | ForEach-Object { Ensure-GitIgnoreEntry -Entry $_ }

$uvCache = (& uv cache dir).Trim()
if ($LASTEXITCODE -ne 0) { throw 'uv cache dir failed.' }
$uvPython = (& uv python dir).Trim()
if ($LASTEXITCODE -ne 0) { throw 'uv python dir failed.' }
$uvTools = (& uv tool dir).Trim()
if ($LASTEXITCODE -ne 0) { throw 'uv tool dir failed.' }

$pythonExe = Join-Path $fullProjectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Virtual environment Python is missing at '$pythonExe'."
}

$pythonJson = & $pythonExe -c "import json, sys; print(json.dumps({'executable': sys.executable, 'base_prefix': sys.base_prefix}))"
if ($LASTEXITCODE -ne 0) { throw 'Python path inspection failed.' }
$pythonInfo = $pythonJson | ConvertFrom-Json

$checks = [ordered]@{
    Project = $fullProjectPath
    Home = $env:HOME
    Temp = $env:TEMP
    UvCache = $uvCache
    UvPython = $uvPython
    UvTools = $uvTools
    VenvPython = $pythonInfo.executable
    BasePython = $pythonInfo.base_prefix
    PipCache = $env:PIP_CACHE_DIR
    Pycache = $env:PYTHONPYCACHEPREFIX
}

foreach ($check in $checks.GetEnumerator()) {
    Assert-EPath -Name $check.Key -Path $check.Value
}

Write-Host ''
Write-Host "E-drive Python project is ready: $fullProjectPath"
Write-Host "Python: $($pythonInfo.executable)"
Write-Host "Base Python: $($pythonInfo.base_prefix)"
Write-Host "uv cache: $uvCache"
Write-Host "uv managed Python: $uvPython"
Write-Host 'Run the Enter script with dot-sourcing in each new PowerShell session.'
