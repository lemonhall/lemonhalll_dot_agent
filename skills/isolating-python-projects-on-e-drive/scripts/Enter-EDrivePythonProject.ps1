[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$Proxy = ''
)

$ErrorActionPreference = 'Stop'

$fullProjectPath = [System.IO.Path]::GetFullPath($ProjectPath)
$projectRoot = [System.IO.Path]::GetPathRoot($fullProjectPath)
if ($projectRoot -ne 'E:\') {
    throw "ProjectPath must be on E:; received '$fullProjectPath'."
}

$paths = [ordered]@{
    Project = $fullProjectPath
    Home = Join-Path $fullProjectPath '.home'
    LocalAppData = Join-Path $fullProjectPath '.home\AppData\Local'
    RoamingAppData = Join-Path $fullProjectPath '.home\AppData\Roaming'
    Cache = Join-Path $fullProjectPath '.cache'
    Temp = Join-Path $fullProjectPath '.tmp'
    UvCache = Join-Path $fullProjectPath '.uv-cache'
    UvPython = Join-Path $fullProjectPath '.uv-python'
    UvPythonBin = Join-Path $fullProjectPath '.uv-python-bin'
    UvTools = Join-Path $fullProjectPath '.uv-tools'
    UvToolBin = Join-Path $fullProjectPath '.uv-tool-bin'
    PythonUser = Join-Path $fullProjectPath '.python-user'
    PythonCache = Join-Path $fullProjectPath '.pycache'
    XdgData = Join-Path $fullProjectPath '.xdg\data'
    XdgConfig = Join-Path $fullProjectPath '.xdg\config'
    XdgState = Join-Path $fullProjectPath '.xdg\state'
    XdgBin = Join-Path $fullProjectPath '.xdg\bin'
    Cargo = Join-Path $fullProjectPath '.cargo'
    Rustup = Join-Path $fullProjectPath '.rustup'
}

foreach ($path in $paths.Values) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

$env:HOME = $paths.Home
$env:USERPROFILE = $paths.Home
$env:HOMEDRIVE = 'E:'
$env:HOMEPATH = $paths.Home.Substring(2)
$env:APPDATA = $paths.RoamingAppData
$env:LOCALAPPDATA = $paths.LocalAppData

$env:XDG_CACHE_HOME = $paths.Cache
$env:XDG_DATA_HOME = $paths.XdgData
$env:XDG_CONFIG_HOME = $paths.XdgConfig
$env:XDG_STATE_HOME = $paths.XdgState
$env:XDG_BIN_HOME = $paths.XdgBin

$env:TEMP = $paths.Temp
$env:TMP = $paths.Temp
$env:TMPDIR = $paths.Temp

$env:UV_CACHE_DIR = $paths.UvCache
$env:UV_PYTHON_INSTALL_DIR = $paths.UvPython
$env:UV_PYTHON_BIN_DIR = $paths.UvPythonBin
$env:UV_TOOL_DIR = $paths.UvTools
$env:UV_TOOL_BIN_DIR = $paths.UvToolBin
$env:UV_PROJECT_ENVIRONMENT = Join-Path $fullProjectPath '.venv'
$env:UV_MANAGED_PYTHON = '1'
$env:UV_PYTHON_INSTALL_REGISTRY = '0'
$env:UV_LINK_MODE = 'copy'
$env:UV_KEYRING_PROVIDER = 'disabled'

$env:PIP_CACHE_DIR = Join-Path $paths.UvCache 'pip'
$env:PIP_CONFIG_FILE = 'NUL'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:PIP_NO_INPUT = '1'
$env:PIP_REQUIRE_VIRTUALENV = '1'

$env:PYTHONUSERBASE = $paths.PythonUser
$env:PYTHONPYCACHEPREFIX = $paths.PythonCache
$env:PYTHON_HISTORY = Join-Path $paths.Home '.python_history'
$env:IPYTHONDIR = Join-Path $paths.Home '.ipython'
$env:JUPYTER_CONFIG_DIR = Join-Path $paths.Home '.jupyter'
$env:MPLCONFIGDIR = Join-Path $paths.Home '.matplotlib'

$env:CARGO_HOME = $paths.Cargo
$env:RUSTUP_HOME = $paths.Rustup
$env:VIRTUAL_ENV = $null
$env:CONDA_PREFIX = $null

if ($Proxy) {
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
}

Set-Location -LiteralPath $fullProjectPath

$paths
