---
name: pypi-release-workflow
description: Use when publishing a Python package to PyPI and you need a repeatable, non-interactive release checklist (version bump, tests, build, twine check/upload) especially on Windows/PowerShell and when credentials live in a repo-local .pypirc.
---

# PyPI Release Workflow

## Overview

A small, repeatable checklist for releasing a Python package to PyPI with minimal surprises: **bump version → run tests → build → twine check → upload non-interactively → verify on PyPI**.

## When to Use

- Releasing a new version to PyPI (manual or CI).
- You want to avoid “twine 等输入/卡住” caused by interactive password prompts.
- Your token is in a **repo-local** `.pypirc` (not `~/.pypirc`).

## Assumptions / Environment

- Run commands in your project environment (venv / `uv` venv) to avoid installing tools into the wrong Python.
- Examples are for **PowerShell 7.x** on Windows.
- The `tomllib` module is Python **3.11+** stdlib (if you are on 3.10 or older, use `tomli`).

## Quick Checklist (PowerShell)

1) Confirm git state
   - `git status -sb`
   - Ensure you are on the intended branch/tag.

2) Bump version (single source of truth if possible)
   - Update `pyproject.toml` `[project].version`
   - (Recommended) Read old/new version explicitly, then update any mirrors (if your project has them):
     - Read current version:
       - `python -c "import tomllib; from pathlib import Path; f=Path('pyproject.toml').open('rb'); print(tomllib.load(f)['project']['version']); f.close()"`
     - After editing `pyproject.toml`, re-check:
       - `python -c "import tomllib; from pathlib import Path; f=Path('pyproject.toml').open('rb'); print(tomllib.load(f)['project']['version']); f.close()"`
     - Search for common mirrors (adjust patterns per repo conventions):
       - Prefer a clean PowerShell-friendly command (single quotes; no extra escaping):
         - `rg -n -i '__version__\s*=|^version\s*=|setuptools_scm'`
       - If you want case-sensitive matches, drop `-i` and write explicit variants:
         - `rg -n '__version__\s*=|^version\s*=|VERSION\s*=|setuptools_scm'`
     - If you must replace a specific old version string:
       - `rg -n '<OLD_VERSION>'` (replace `<OLD_VERSION>` with the previous version)

3) Run unit tests (must be green)
   - `python -m unittest -q`

4) Ensure build tooling exists
   - Using pip:
     - `python -m pip install -U build twine`
   - Or using uv (if your workflow prefers it):
     - `uv pip install -U build twine`

5) Build to a versioned output folder (avoid mixing artifacts)
   - Recommended (clean folder → create → build):
     - `$ver = "<VERSION>"   # replace with the actual version`
     - `$outDir = ".release_dist\\$ver"`
     - If the folder already exists, delete it first (interactive confirm for safety):
       - `if (Test-Path $outDir) { Remove-Item -Recurse -Force $outDir -Confirm }`
     - `New-Item -ItemType Directory -Force $outDir | Out-Null`
     - `python -m build --outdir $outDir`
   - (Recommended) Add build outputs to `.gitignore`:
     - `.release_dist/`

6) Validate artifacts
   - `python -m twine check .release_dist\\<VERSION>\\*`

7) Commit + Tag (recommended; do this before upload)
   - After bumping version (and updating mirrors) and validating artifacts, commit and tag so the published artifacts map cleanly to a VCS state:
     - `git add pyproject.toml` (and any other version mirror files)
     - `git commit -m "release: v<VERSION>"`
     - `git tag v<VERSION>`
     - `git push origin HEAD --tags`

8) Upload (non-interactive; explicit config file)
   - If using repo-local `.pypirc`:
     - `python -m twine upload --non-interactive --config-file .pypirc -r pypi .release_dist\\<VERSION>\\*`
     - Notes:
       - `-r pypi` refers to the `[pypi]` section in `.pypirc` (see template below).
       - If a previous attempt partially uploaded files and retries fail with “File already exists”, consider `--skip-existing`:
         - `python -m twine upload --non-interactive --skip-existing --config-file .pypirc -r pypi .release_dist\\<VERSION>\\*`
         - Risk: if you forgot to bump the version, `--skip-existing` may silently skip uploads and make you think you shipped new code.
   - If using env vars instead:
     - `$env:TWINE_USERNAME="__token__" ; $env:TWINE_PASSWORD="pypi-..." ; python -m twine upload --non-interactive -r pypi .release_dist\\<VERSION>\\*`

9) Verify the release exists on PyPI
   - Prefer checking `releases` by version (more reliable than filename prefix due to normalization differences):
     - `python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/<DISTNAME>/json')); print('<VERSION>' in d.get('releases',{}))"`
   - Note: PyPI normalizes project names (PEP 503), e.g. `_`/`.` → `-`, and lowercasing. Query using the normalized name if needed.
   - Proxy tip (optional): if your network requires a proxy, set `$env:HTTP_PROXY` / `$env:HTTPS_PROXY` first; `urllib` will typically honor these env vars.
   - Alternative using `curl.exe` (often easier to route via system proxy):
     - `curl.exe -s "https://pypi.org/pypi/<DISTNAME>/json" | python -c 'import sys,json; d=json.load(sys.stdin); print("<VERSION>" in d.get("releases",{}))'`

## Minimal `.pypirc` Template (repo-local)

Put this file at the repo root as `.pypirc` and pass `--config-file .pypirc` when uploading:

```
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Security notes:
- Treat `.pypirc` as a secret if it contains a token/password; add it to `.gitignore` and never commit it.
- Quick guard (adds `.pypirc` / `.release_dist/` to `.gitignore` if missing):
  - `if (-not (Test-Path .gitignore)) { New-Item -ItemType File -Force .gitignore | Out-Null }`
  - `if (-not (Select-String -Path .gitignore -Pattern '^\s*\.pypirc\s*$' -Quiet -ErrorAction SilentlyContinue)) { Add-Content .gitignore "`n.pypirc" }`
  - `if (-not (Select-String -Path .gitignore -Pattern '^\s*\.release_dist\/\s*$' -Quiet -ErrorAction SilentlyContinue)) { Add-Content .gitignore "`n.release_dist/" }`
- Prefer environment variables or a secret manager in CI.
- For CI releases, consider PyPI Trusted Publishers (OIDC) to avoid storing long-lived tokens.

## Common Mistakes

- Twine “卡住/等输入”：没有传 `--non-interactive`，或者 `.pypirc` 不在默认位置（twine 默认读 `~/.pypirc`），导致它回退到交互式 password prompt。
- 上传失败后“重试同版本”：
  - If PyPI returns `400 File already exists`, you cannot overwrite; fix and **bump the version**.
  - If it failed before any file reached PyPI (network/auth/etc.), you can usually fix and retry the same version.
- `dist/` 里残留旧包：建议输出到 `.release_dist/<VERSION>/`，或上传前先清空 `dist/`。

## Red Flags — STOP

- 还没跑 `python -m unittest -q` 就准备上传
- `twine upload` 没带 `--non-interactive`
- 不确定 twine 用的是哪份 `.pypirc`
- 版本号在多个地方不一致
