---
name: isolating-python-projects-on-e-drive
description: Use when creating or repairing a uv-managed Python project on Windows where interpreters, virtual environments, dependencies, caches, temporary files, bytecode, and application-controlled state must stay on the E drive instead of C or D.
---

# Python 项目 E 盘隔离

## 核心边界

把 uv/Python 及其子进程可控制的写入全部放入 E 盘项目目录。技能文件本身位于公共目录，可能在 C 盘，但只作为只读入口。

不要声称普通 Windows 会话能实现物理意义上的“C/D 零写入”：Defender、事件日志、注册表 hive、Prefetch 等系统组件不受 Python 环境变量控制。需要强证明时使用 ProcMon 审计进程树，或使用 VM/沙箱强制隔离。

## 标准工作流

1. 确认目标绝对路径以 `E:\` 开头；其他盘直接停止。
2. 运行初始化脚本。它只设置当前 PowerShell 进程环境，安装 uv-managed Python 时禁用 Windows 注册，并在项目内创建 `.venv`、缓存、临时目录和运行目录。
3. 以后进入项目时点源环境脚本，再运行 `uv add`、`uv sync`、`uv run` 或 Python。
4. 新增依赖后检查其专属缓存变量；例如 Hugging Face、Playwright、Jupyter 可能需要额外重定向。
5. 用脚本输出和 ProcMon（严格验收时）验证，而不是凭目录外观看起来干净就下结论。

## 快速命令

创建或幂等恢复项目：

```powershell
& "$HOME\.agents\skills\isolating-python-projects-on-e-drive\scripts\Initialize-EDrivePythonProject.ps1" `
  -ProjectPath 'E:\development\my-project' -PythonVersion '3.12' `
  -Proxy 'http://127.0.0.1:7897'
```

以后每次打开新的 PowerShell 会话：

```powershell
. "$HOME\.agents\skills\isolating-python-projects-on-e-drive\scripts\Enter-EDrivePythonProject.ps1" `
  -ProjectPath 'E:\development\my-project' -Proxy 'http://127.0.0.1:7897'
uv add requests
uv run python -c "import sys; print(sys.executable)"
```

点源符号 `.` 很重要；否则环境修改只在脚本调用期间可靠可用。

## 必须保持的隔离项

| 类别 | 项目内位置/控制变量 |
|---|---|
| Python | `.uv-python`, `UV_PYTHON_INSTALL_DIR`, `UV_MANAGED_PYTHON=1` |
| Windows 注册 | `UV_PYTHON_INSTALL_REGISTRY=0` 或 `uv python install --no-registry` |
| 虚拟环境 | `.venv`, `UV_PROJECT_ENVIRONMENT` |
| uv/pip 缓存 | `.uv-cache`, `UV_CACHE_DIR`, `PIP_CACHE_DIR` |
| 临时文件 | `.tmp`, `TEMP`, `TMP`, `TMPDIR` |
| 用户/应用状态 | `.home`, `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` |
| XDG/工具状态 | `.xdg`, `XDG_*`, `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR` |
| Python 状态 | `.python-user`, `.pycache`, `PYTHONUSERBASE`, `PYTHONPYCACHEPREFIX` |
| 原生构建 | `.cargo`, `.rustup`, `CARGO_HOME`, `RUSTUP_HOME` |

## 验证规则

- `uv cache dir`、`uv python dir`、`uv tool dir`、`sys.executable` 和 `sys.base_prefix` 必须全部位于 E 盘。
- 不要仅因 `.venv` 在 E 盘就判定通过；它可能引用 C/D 盘解释器。
- 不要自动删除已有 `.venv`。若它引用其他盘，报告路径并让用户明确决定是否重建。
- 不要使用 `setx`、用户级 pip 配置或全局 uv 配置；它们会污染其他项目。
- 不要使用旧的 `UV_PYTHON_PREFERENCE=only-managed`。当前 uv 使用 `UV_MANAGED_PYTHON=1` / `--managed-python`。
- `UV_LINK_MODE=copy` 牺牲少量空间，避免虚拟环境依赖缓存中的链接，适合强调可搬运和透明性的项目。

## 常见遗漏

- 只移动 `.venv`，却让 uv、pip、PEP 517 构建临时文件仍写 `%LOCALAPPDATA%` 和 `%TEMP%`。
- 忘记 `--no-registry`，导致 uv 安装 Python 时写 Windows 注册表。
- 在隔离环境外执行后续的 `uv add` 或 `pip install`。
- 重定向 `HOME` 后发现云凭据不可见；按需显式传入凭据环境变量，不要复制秘密到项目或提交 Git。
- 把操作系统自身写入误算为 Python 项目写入，或反过来宣称没有系统写入。

## 资源

- `scripts/Initialize-EDrivePythonProject.ps1`：创建/恢复项目、安装 managed Python、同步依赖并验证路径。
- `scripts/Enter-EDrivePythonProject.ps1`：为当前 PowerShell 会话设置隔离环境并进入项目。
