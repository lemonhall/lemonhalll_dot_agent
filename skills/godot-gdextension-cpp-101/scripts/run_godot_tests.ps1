Param(
  [string]$GodotExe = $env:GODOT_WIN_EXE,
  # If empty: assume this script lives in <project>/scripts and use its parent dir.
  [string]$ProjectRoot = "",
  # Suite name. If -SuiteDir is not set:
  # - "all" => tests/**/test_*.gd
  # - otherwise => tests/<Suite>/**/test_*.gd (Suite can be a nested path like "addons/jediterm")
  [string]$Suite = "all",
  # Optional explicit suite dir under project root (preferred when suites are custom).
  [string]$SuiteDir = "",
  # Optional single test script path (relative to project root or absolute).
  [string]$One = "",
  [int]$TimeoutSec = $(if ($env:GODOT_TEST_TIMEOUT_SEC) { [int]$env:GODOT_TEST_TIMEOUT_SEC } else { 120 }),
  [string[]]$ExtraArgs = @()
)

$ErrorActionPreference = "Stop"

function Quote-Arg([string]$a) {
  if ($null -eq $a) { return '""' }
  if ($a -match '[\s"]') {
    $escaped = $a -replace '"', '\\"'
    return '"' + $escaped + '"'
  }
  return $a
}

function Run-ProcessCapture {
  Param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string[]]$Args,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [Parameter(Mandatory = $true)][int]$TimeoutSec,
    [Parameter(Mandatory = $true)][hashtable]$Env
  )

  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $FilePath
  $psi.WorkingDirectory = $WorkingDirectory
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true
  $psi.Arguments = (($Args | ForEach-Object { Quote-Arg $_ }) -join ' ')
  foreach ($k in $Env.Keys) { $psi.Environment[$k] = [string]$Env[$k] }

  $p = [System.Diagnostics.Process]::new()
  $p.StartInfo = $psi

  [void]$p.Start()
  $outTask = $p.StandardOutput.ReadToEndAsync()
  $errTask = $p.StandardError.ReadToEndAsync()

  $timedOut = -not $p.WaitForExit($TimeoutSec * 1000)
  if ($timedOut) {
    try { $p.Kill($true) } catch { try { Stop-Process -Id $p.Id -Force } catch {} }
  }

  $p.WaitForExit()

  $stdoutText = ""
  $stderrText = ""
  try { $stdoutText = $outTask.GetAwaiter().GetResult() } catch { $stdoutText = "" }
  try { $stderrText = $errTask.GetAwaiter().GetResult() } catch { $stderrText = "" }

  return @{
    timed_out = $timedOut
    exit_code = [int]$p.ExitCode
    stdout = $stdoutText
    stderr = $stderrText
  }
}

function Usage {
  Write-Host @"
Run Godot headless test scripts from Windows (PowerShell).

Usage:
  scripts/run_godot_tests.ps1 [-GodotExe <path>] [-ProjectRoot <path>] [-Suite <name>] [-SuiteDir <path>] [-One <test_script.gd>] [-TimeoutSec <seconds>] [-ExtraArgs <args...>]

Examples:
  scripts/run_godot_tests.ps1
  scripts/run_godot_tests.ps1 -One tests\\native_smoke\\test_gdextension_smoke.gd
  scripts/run_godot_tests.ps1 -Suite addons\\jediterm
  scripts/run_godot_tests.ps1 -SuiteDir tests\\addons\\jediterm

Notes:
  - Prefer the *console* exe for reliable headless output.
  - Set GODOT_WIN_EXE to avoid passing -GodotExe every time.
  - To avoid hung tests, set GODOT_TEST_TIMEOUT_SEC or pass -TimeoutSec.
"@
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
} else {
  $ProjectRoot = Resolve-Path $ProjectRoot
}

if ([string]::IsNullOrWhiteSpace($GodotExe) -or !(Test-Path $GodotExe)) {
  Write-Host "Godot exe not found. Set GODOT_WIN_EXE or pass -GodotExe."
  Usage
  exit 2
}

function Ensure-Dir([string]$p) { if (!(Test-Path $p)) { [void](New-Item -ItemType Directory -Force -Path $p) } }

# Isolate Godot user:// to keep tests reproducible and avoid polluting real user profile.
$GodotUserRoot = Join-Path $ProjectRoot ".godot-user"
$AppDataRoaming = Join-Path $GodotUserRoot "AppData\\Roaming"
$AppDataLocal = Join-Path $GodotUserRoot "AppData\\Local"
$UserProfile = Join-Path $GodotUserRoot "User"
Ensure-Dir $AppDataRoaming
Ensure-Dir $AppDataLocal
Ensure-Dir $UserProfile

$Env = @{
  "APPDATA" = $AppDataRoaming
  "LOCALAPPDATA" = $AppDataLocal
  "USERPROFILE" = $UserProfile
}

$tests = @()
if (![string]::IsNullOrWhiteSpace($One)) {
  $tests = @($One)
} else {
  $suitePath = ""
  if (![string]::IsNullOrWhiteSpace($SuiteDir)) {
    $suitePath = $SuiteDir
  } elseif ($Suite -eq "all") {
    $suitePath = "tests"
  } else {
    $suitePath = Join-Path "tests" $Suite
  }

  $suiteFull = $suitePath
  if (!(Test-Path $suiteFull)) { $suiteFull = Join-Path $ProjectRoot $suitePath }
  if (!(Test-Path $suiteFull)) {
    Write-Host ("Suite directory not found: {0}" -f $suitePath)
    Usage
    exit 2
  }

  $tests = Get-ChildItem -Path $suiteFull -Recurse -Filter "test_*.gd" -File |
    Sort-Object FullName |
    ForEach-Object { $_.FullName }

  if ($tests.Count -eq 0) {
    Write-Host ("No tests found under {0}\\**\\test_*.gd" -f $suiteFull)
    exit 2
  }
}

$status = 0
foreach ($t in $tests) {
  $scriptPath = $t
  if (!(Test-Path $scriptPath)) { $scriptPath = Join-Path $ProjectRoot $t }
  if (!(Test-Path $scriptPath)) {
    Write-Host "Missing test script: $t"
    $status = 1
    continue
  }

  Write-Host "--- RUN $t"
  $args = @()
  if ($ExtraArgs.Count -gt 0) { $args += $ExtraArgs }
  $args += @("--headless", "--rendering-driver", "dummy", "--path", $ProjectRoot.Path, "--script", $scriptPath)

  $res = Run-ProcessCapture -FilePath $GodotExe -Args $args -WorkingDirectory $ProjectRoot.Path -TimeoutSec $TimeoutSec -Env $Env

  if ($res.stdout) { $res.stdout.TrimEnd() | Write-Host }
  if ($res.stderr) { $res.stderr.TrimEnd() | Write-Host }
  if ($res.timed_out) {
    Write-Host ("[TIMEOUT] {0} (after {1}s)" -f $t, $TimeoutSec)
    $status = 1
  } elseif ($res.exit_code -ne 0) {
    Write-Host ("[FAIL] {0} (exit={1})" -f $t, $res.exit_code)
    $status = 1
  } else {
    Write-Host ("[OK] {0}" -f $t)
  }
}

exit $status

