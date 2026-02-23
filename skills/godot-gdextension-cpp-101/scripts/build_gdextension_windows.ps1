param(
  [Parameter(Mandatory = $true)][string]$NativeDir,
  [string]$GodotExe = $env:GODOT_WIN_EXE,
  [string]$GodotDir = "",
  [ValidateSet("2019", "2022")]
  [string]$PreferVs = "2022",
  [switch]$DebugOnly,
  [switch]$ReleaseOnly,
  [switch]$All,
  [switch]$RegenBindings,
  [string]$Arch = "x86_64",
  [string[]]$ExtraSconsArgs = @()
)

$ErrorActionPreference = "Stop"

function Require-Command([string]$name, [string]$hint) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "Missing command: $name. $hint" }
}

function Resolve-GodotExe {
  if ($GodotExe -and (Test-Path $GodotExe)) { return (Resolve-Path $GodotExe).Path }
  if ($GodotDir -and (Test-Path $GodotDir)) {
    $candidates = @(
      (Get-ChildItem -Path $GodotDir -Filter "*console*.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1),
      (Get-ChildItem -Path $GodotDir -Filter "*.exe" -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch "godot_vshost|mono|sharp" } | Select-Object -First 1)
    ) | Where-Object { $_ -ne $null }
    if ($candidates.Count -gt 0) { return $candidates[0].FullName }
  }
  throw "Godot executable not found. Set env:GODOT_WIN_EXE or pass -GodotExe (recommended) or -GodotDir."
}

function Find-VsDevCmdBat {
  $vswhere = $null
  $vswhereCandidates = @(
    (Get-Command vswhere.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer\\vswhere.exe"
  ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

  if ($vswhereCandidates.Count -gt 0) { $vswhere = $vswhereCandidates[0] }
  if (-not $vswhere) { return "" }

  $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($installPath)) { return "" }

  $vsdevcmd = Join-Path $installPath "Common7\\Tools\\VsDevCmd.bat"
  if (Test-Path $vsdevcmd) { return $vsdevcmd }
  return ""
}

function Invoke-InMsvcEnv([string]$command) {
  $hasCl = (Get-Command cl.exe -ErrorAction SilentlyContinue) -ne $null
  if ($hasCl) {
    & cmd.exe /c $command
    return $LASTEXITCODE
  }

  $vsdevcmd = Find-VsDevCmdBat
  if ([string]::IsNullOrWhiteSpace($vsdevcmd)) {
    throw "MSVC not found (cl.exe missing) and VsDevCmd.bat not found via vswhere. Install Visual Studio Build Tools (C++ workload), or run this script inside a 'x64 Native Tools Command Prompt'."
  }

  $cmd = """$vsdevcmd"" -no_logo -arch=amd64 -host_arch=amd64 >nul && $command"
  & cmd.exe /c $cmd
  return $LASTEXITCODE
}

Require-Command "scons" "Install with: python -m pip install --user -U scons"

$nativeDirPath = (Resolve-Path $NativeDir).Path
$godot = Resolve-GodotExe

$godotCppScons = Join-Path $nativeDirPath "thirdparty\\godot-cpp\\SConstruct"
if (-not (Test-Path $godotCppScons)) {
  throw "Missing godot-cpp: $godotCppScons`nPlace godot-cpp under native/thirdparty/godot-cpp (submodule or junction)."
}

$apiDir = Join-Path $nativeDirPath "build\\godot_api"
$apiFile = Join-Path $apiDir "extension_api.json"
$needApiDump = (-not (Test-Path $apiFile)) -or $RegenBindings

$generatedHeader = Join-Path $nativeDirPath "thirdparty\\godot-cpp\\gen\\include\\godot_cpp\\classes\\object.hpp"
$needBindings = (-not (Test-Path $generatedHeader)) -or $RegenBindings

if ($needApiDump -or $needBindings) {
  New-Item -ItemType Directory -Force -Path $apiDir | Out-Null
  Push-Location $apiDir
  try {
    Write-Host "[INFO] Dumping extension_api.json via Godot..."
    & $godot --dump-extension-api | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Godot --dump-extension-api failed (exit=$LASTEXITCODE)" }
  } finally {
    Pop-Location
  }
} else {
  Write-Host "[SKIP] extension_api.json already exists."
}

if (-not (Test-Path $apiFile)) { throw "Expected extension_api.json not found: $apiFile" }

$buildDebug = $true
$buildRelease = $false
if ($All) { $buildDebug = $true; $buildRelease = $true }
elseif ($ReleaseOnly) { $buildDebug = $false; $buildRelease = $true }
elseif ($DebugOnly) { $buildDebug = $true; $buildRelease = $false }

$bindingsArg = ""
if ($needBindings) {
  $bindingsArg = " generate_bindings=yes"
  if ($RegenBindings) {
    Write-Host "[INFO] -RegenBindings enabled: forcing godot-cpp bindings regeneration (slow)."
  } else {
    Write-Host "[INFO] godot-cpp bindings not found; generating bindings (first build, slow)."
  }
}

function Run-Scons([string]$target) {
  $extra = ""
  if ($ExtraSconsArgs.Count -gt 0) { $extra = " " + ($ExtraSconsArgs -join " ") }
  $cmd = "cd /d ""$nativeDirPath"" && scons platform=windows target=$target arch=$Arch$bindingsArg custom_api_file=""$apiFile""$extra"
  Write-Host "[INFO] $cmd"
  $code = Invoke-InMsvcEnv $cmd
  if ($code -ne 0) { throw "Build failed (target=$target), exit=$code" }
}

if ($buildDebug) { Run-Scons "template_debug" }
if ($buildRelease) { Run-Scons "template_release" }

Write-Host "[OK] Build finished."

