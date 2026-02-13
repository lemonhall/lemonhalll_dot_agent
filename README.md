# .agents（Codex Skills 仓库）

这个仓库用于存放本地 AI 编程助手（如 OpenAI Codex CLI）可加载的 **Skills**。每个 skill 以一个目录存在，入口文件为 `SKILL.md`，必要时附带脚本、模板与参考资料。

> 典型放置路径：`%USERPROFILE%\.agents`（本仓库当前即位于该位置）。你也可以把它放在别处，但需要确保你的 agent 配置指向正确的 skills 目录。

## 目录结构

- `skills/`：skills 根目录
  - `skills/<skill-name>/SKILL.md`：skill 的说明与执行流程（优先阅读）
  - `skills/<skill-name>/scripts/`：可执行脚本（如 `.ps1` / `.py` / `.js`）
  - `skills/<skill-name>/templates/`、`references/`、`assets/`：模板与参考资料（按需）
- `.skill-lock.json`：skills 安装器生成的锁文件（记录来源、版本/commit、更新时间等）
- `skills/superpowers`：到 `~/.codex/superpowers/skills` 的符号链接（便于复用同一套 skills；跨机器克隆时可能失效）

## 如何使用 skills（通用）

1. 找到你要用的 skill：`skills/<skill-name>/SKILL.md`
2. 按 `SKILL.md` 中的“何时使用 / Quick Commands / 工作流”执行
3. 在对话中**直接点名** skill（例如输入 skill 名称），或提出与其描述明显匹配的需求，让 agent 按 skill 流程工作

## PowerShell 约定（本机环境偏好）

- 默认以 **PowerShell 7.x** 为准（非 bash），命令串联用 `;`
- 若要调用 bash/WSL 命令，显式使用：`wsl -e bash -lc '...'`
- `curl` / `wget` 建议用 `curl.exe` / `wget.exe` 指向真实二进制；调用 JSON API 优先 `Invoke-RestMethod`

## 代理（可选）

如需走本地代理（例如 `127.0.0.1:7897`），可在当前会话临时设置：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:7897' ; $env:HTTPS_PROXY='http://127.0.0.1:7897'
```

`npm` / `git` 是否需要额外配置，取决于你的网络与工具链；优先按“项目/仓库级”配置，避免污染全局环境。

## 安全与隐私（重要）

- **不要把密钥写进仓库**：诸如 `.env`、`.p8`、token、证书等应只存在于本机，并加入 `.gitignore`。
- 如果你发现密钥已经进入 git 历史：**按泄露处理**（吊销/重签发/更换 token），而不是继续沿用旧密钥。
- 某些 skills（如推送、家电控制、自动化登录）可能触发真实外部行为：执行前请确保你理解 `SKILL.md` 的安全提示，并在需要时二次确认。

## 更新与维护（可选）

如果你使用 `npx skills` 作为安装/更新工具（见各 skill 的来源与说明）：

- 查找/安装：`npx skills find <query>`、`npx skills add <owner/repo@skill>`
- 检查更新：`npx skills check`
- 更新全部：`npx skills update`

更新后通常会变更 `skills/` 内容与 `.skill-lock.json`，建议一并提交以保证可复现。

## 许可说明

本仓库包含来自不同来源的第三方 skills；它们可能各自携带 `LICENSE.txt` 或在上游仓库声明许可。使用与分发时请遵守对应条款。

