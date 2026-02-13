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


## 私人SKILL

### agent-md-101

为新仓库或 AI agent 入驻生成/重构 `AGENTS.md`，让多环境协作（Godot + SDK + demo apps）保持安全、可测、一致。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill agent-md-101 -g -y --agent codex
```

### apn-pushtool

本地 APNs 推送 CLI（`.env` 配置 + 可选 E2E 真推送），适用于 Windows 11 + PowerShell。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill apn-pushtool -g -y --agent codex
```

### github-daily-brief

每日 GitHub 趋势速报——热门仓库 + 当日新建仓库，输出中文摘要 + Markdown/HTML 文件。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill github-daily-brief -g -y --agent codex
```

### greenflash-tab5

M5Stack Tab5（ESP32-P4）固件刷写自动化——设备进入下载模式（"绿闪了"）后，一键 build → flash → boot → monitor 日志抓取循环。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill greenflash-tab5 -g -y --agent codex
```

### md-to-modern-pptx

Markdown → 精美 PPTX 幻灯片，内置主题调色板 + PptxGenJS 确定性生成 + markitdown QA 校验。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill md-to-modern-pptx -g -y --agent codex
```

### meiju-acctl-home-comfort

美的美居空调控制——当你说"太冷了/太热了"，agent 会共情回应并（经确认后）通过 `meiju-acctl` CLI 调节空调。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill meiju-acctl-home-comfort -g -y --agent codex
```

### pypi-release-workflow

Python 包发布到 PyPI 的可重复检查清单——版本号 bump → 测试 → 构建 → twine check/upload，Windows/PowerShell 友好。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill pypi-release-workflow -g -y --agent codex
```

### spaghetti-refactor

拆解"意大利面条"代码——当单文件/单类耦合了 UI、IO、状态、输入、游戏逻辑，尤其在 Godot 4.x 严格类型/warning-as-error 环境下，安全地逐步解耦。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill spaghetti-refactor -g -y --agent codex
```

### tashan-development-loop

塔山项目循环——PRD/Spec + 版本化执行计划（`docs/plan/vN-*`）+ 端到端验证，严格追溯链防止文档漂移与返工。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill tashan-development-loop -g -y --agent codex
```

### watchdog-approvals

Codex 审批持久化——把反复弹出的安全操作（跑测试、读日志、git 操作）写入 Codex 信任配置，后续会话不再重复确认。

```bash
npx skills add https://github.com/lemonhall/lemonhalll_dot_agent --skill watchdog-approvals -g -y --agent codex
```

## 许可说明

本仓库包含来自不同来源的第三方 skills；它们可能各自携带 `LICENSE.txt` 或在上游仓库声明许可。使用与分发时请遵守对应条款。

