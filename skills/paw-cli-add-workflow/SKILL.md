---
name: paw-cli-add-workflow
description: Use when adding a new pseudo-terminal (whitelisted) CLI command and its built-in SKILL.md to kotlin-agent-app, including per-command source file placement, TerminalCommands registry update, AgentsWorkspace asset install, and Robolectric unit tests.
---

# paw-cli-add-workflow

## Overview

本项目用一个工具 `terminal_exec` 提供“伪终端 / 白名单 CLI”能力：看起来像执行命令行，但底层只会路由到 App 内置 Kotlin 实现（**无 shell、无外部进程**），并且每次执行会审计落盘到：

- `.agents/artifacts/terminal_exec/runs/<run_id>.json`

这份流程用于指引“如何给这个项目新增一个 CLI 命令 + 配套的内置 Skill（`SKILL.md`）”，参考 v11 的 `hello`/`hello-world` 最小闭环实现。

## When to Use

- 需要给 `terminal_exec` 新增一个可调用的白名单命令（例如：`doc extract`、`table to-csv`、`image ocr` 等）。
- 需要新增/更新一个内置 skill，让 Agent 能按文档说明书调用该命令并验证输出。
- 需要确保命令被正确注册、可测试、可审计、可在 App 内工作区稳定复现。

## Hard Constraints（别踩雷）

- `terminal_exec` 只接受**单行**命令；包含换行会被拒绝。
- 明确禁止 shell-like token：`;`、`&&`、`||`、`|`、`>`、`<`、`` ` ``、`$(`（见 `TerminalExecTool.parseAndValidateCommand`）。
- 命令解析仅支持“最小 argv + 双引号 + 反斜杠转义”，不支持 pipe/redirection/glob。
- 不要引入外部进程执行（上架风险）；能力必须由 App 内置代码实现。
- stdout/stderr 会被截断（默认 stdout 16k / stderr 8k），需要大输出时用 artifacts 落盘并返回引用。
- **Help 必须可用**：所有白名单命令必须支持 `--help`/`help`（含子命令 help），并且 help 调用必须 `exit_code=0`（详见下文约定）。

## Project Rules（必须遵守：防止单文件膨胀）

- `TerminalCommands.kt` **只能**做“命令注册表/默认 registry 构建”，禁止在里面实现任何命令逻辑。
  - 文件：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalCommands.kt`
- 公共协议类型（`TerminalCommand*` / `TerminalArtifact` 等）集中在核心文件，其他命令只 import：
  - 文件：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalCommandCore.kt`
- 每个**顶层命令**（例如 `hello`、`git`、未来的 `doc`、`apn`）必须独立成文件/目录：
  - 小命令：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/commands/<Name>Command.kt`
  - 大命令：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/commands/<cmd>/*`（例如 `commands/git/GitCommand.kt`）
- 以后新增命令时，**不要改** `TerminalExecTool` 的 registry 初始化逻辑；统一在 `TerminalCommands.defaultRegistry(...)` 里注册。

## Workflow（TDD 优先）

### 1) 设计命令协议（先写下来）

为新命令确定：

- `name`：建议全小写；如需子命令，走 argv（例如 `doc extract ...`）。
- argv 约定：哪些是 flag（`--in`/`--out`），哪些是位置参数。
- 输出契约：
  - `stdout`：给人看的摘要/进度/结果摘要
  - `result`：结构化 JSON（给 Agent 稳定消费）
  - `artifacts[]`：产物文件引用（path/mime/description）
  - `exitCode`：0 成功；非 0 失败
  - `errorCode` / `errorMessage`：失败必须可解释（例如 `InvalidArgs` / `NotSupported`）

### 1.1) Help 约定（强制：避免 Agent 反复撞墙）

Agent 很常见会先试探 `--help`，因此**每个顶层命令必须实现 help**，并且子命令也必须有 help：

- 入口（必须全部支持）：
  - `<cmd> --help`
  - `<cmd> help`
  - `<cmd> <subcmd> --help`
  - `<cmd> help <subcmd>`
- 约定：
  - help 调用必须返回 `exit_code=0`
  - `stdout`：一段简洁的人类可读 usage（不要太长；超长内容用 artifacts）
  - `result`：结构化字段（建议）：
    - `ok=true`
    - `command="<cmd> help"` 或 `"<cmd> <subcmd> help"`
    - `usage: string`
    - `subcommands: [string]`（如有）
    - `flags: [{name, required, description}]`（如有）
    - `examples: [string]`（如有）

### 1.2) Secrets / 私密配置约定（.env + secrets 目录）

凡是命令需要凭据（API Key、密码、token、私钥路径等），必须采用统一的**skill-local secrets** 约定（参考 `qqmail-cli` / `irc-cli` / `ssh-cli` / `stock-cli`）：

- 存放路径（强制）：
  - `.agents/skills/<skill-name>/secrets/.env`
- Asset 模板文件（强制）：
  - `app/src/main/assets/builtin_skills/<skill-name>/secrets/env.example`
  - 说明：Android assets 不稳定支持以 `.` 开头的文件名，因此用 `env.example`，App 初始化时拷贝为 `.env`（仅首次创建，绝不覆盖用户真实 secrets）。
- 读取方式（建议）：
  - 用统一的 DotEnv 解析器读取 UTF-8 `.env`，并对缺失字段返回可解释错误（`error_code="MissingCredentials"`）。
- 安全要求（强制）：
  - **禁止**通过 argv 传递 secrets（例如 `--password/--token/...` 或 `KEY=...`）；需要在命令实现中显式扫描 argv 并拒绝（`error_code="SensitiveArgv"` 或 `ForbiddenArg`）。
  - 日志/stdout/stderr/result 里**不得回显 secrets**（包括部分截断后的 token）。

### 1.3) 文本编码/字符集边界（建议写进设计与测试）

涉及“外部文件/归档/网络文本”的命令，很容易遇到编码坑：

- zip/tar 等归档文件名可能不是 UTF-8（Windows 打包常见 CP936/GBK、日文环境常见 CP932），甚至会触发 Java `MALFORMED[...]` 解码错误。
- 最佳实践：
  - 提供 `--encoding <...>`（例如 `utf-8/cp932/gbk`）与 `--encoding auto` 的回退策略
  - 为“非 UTF-8 名称”补 1 个回归测试（至少覆盖：不会崩溃、解压后文件名正确）

### 2) RED：先加测试（推荐直接扩 `TerminalExecToolTest.kt`）

在 `app/src/test/java/.../TerminalExecToolTest.kt` 增加用例：

- `tool.exec("<你的命令行>")` 返回 `exit_code==0` 且 stdout/result 符合预期
- 错误参数返回 `exit_code!=0` 且 `error_code` 可解释
- （如适用）artifact 文件确实存在/可读
- （如果你新增了额外禁用 token / 限制）补对应的拒绝测试

提示：现有 harness 已把 `.agents` 工作区初始化好，并能从 tool output 读到 `run_id`，可顺手验证审计落盘存在。

### 3) GREEN：实现命令（TerminalCommand）

在以下位置实现命令逻辑（按现有风格）：

- 小命令：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/commands/<Name>Command.kt`
- 大命令：`app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/commands/<cmd>/<Cmd>Command.kt`

最小实现形态参考 `HelloCommand`：

- 新增 `internal object XxxCommand : TerminalCommand`
- 在 `run(argv, stdin)` 中解析参数并返回 `TerminalCommandOutput`
- 需要写文件/产物时：写到 `.agents/artifacts/...`（或其它明确目录），并在 `artifacts` 返回引用

### 4) 注册命令到白名单（TerminalCommands registry）

把新命令加入 registry 初始化列表：

- `app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalCommands.kt`
  - `TerminalCommands.defaultRegistry(...)` 的 `listOf(...)` 里新增你的命令

未注册的命令会统一返回 `UnknownCommand`（保持这一口径）。

### 5) 新增“内置 Skill”文档（builtin_skills）

新增目录与文件：

- `app/src/main/assets/builtin_skills/<skill-name>/SKILL.md`

写法参考 `hello-world`：

- YAML frontmatter 只写 `name` / `description`（`name` 建议与目录一致）
- 明确写出要调用的工具与单行命令，例如：
  - 工具：`terminal_exec`
  - 命令：`<你的命令行>`
- 写清楚可验证的期望（stdout 关键字、result 字段、artifact 路径规则）
- Rules 里强制：
  - 必须实际调用 `terminal_exec`，不要臆造输出
  - `exit_code!=0` 或包含 `error_code`：直接报告错误并停止

### 6) 让 App 初始化时把内置 skill 安装进 `.agents/skills`

在 `AgentsWorkspace.ensureInitialized()` 增加一条安装：

- `app/src/main/java/com/lsl/kotlin_agent_app/agent/AgentsWorkspace.kt`
  - `installBundledSkillDir(name = "<skill-name>", assetDir = "builtin_skills/<skill-name>", overwrite = overwrite)`

不加这步：asset 虽然存在，但 `.agents/skills/<skill-name>/SKILL.md` 可能不会出现，导致 SkillTool 读不到。

### 7) Verify

PowerShell：

- `.\gradlew.bat :app:testDebugUnitTest`

至少要覆盖：

- 新命令成功路径测试
- 关键失败路径测试（invalid args / unknown / 禁用 token 等）

## Quick Reference（关键文件）

- `app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalExecTool.kt`（命令解析/禁用 token/审计落盘/白名单路由）
- `app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalCommands.kt`（唯一注册表：把新命令加到这里）
- `app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalCommandCore.kt`（公共协议类型：TerminalCommand/Output/Registry/Artifact）
- `app/src/main/java/com/lsl/kotlin_agent_app/agent/tools/terminal/commands/`（每个顶层命令的实现放这里）
- `app/src/test/java/com/lsl/kotlin_agent_app/agent/tools/terminal/TerminalExecToolTest.kt`（Robolectric 单测 harness）
- `app/src/main/assets/builtin_skills/<skill-name>/SKILL.md`（面向 Agent 的“命令式说明书”）
- `app/src/main/java/com/lsl/kotlin_agent_app/agent/AgentsWorkspace.kt`（内置 skills 安装到 `.agents/skills`）

## Common Mistakes

- 忘了在 `TerminalCommands.defaultRegistry(...)` 注册命令 → 只会得到 `UnknownCommand`。
- 忘了在 `AgentsWorkspace` 安装内置 skill → App 启动后 `.agents/skills` 里没有该 skill。
- 在命令行里使用 `;` / `|` / `>` 等 → 会被 `InvalidCommand` 拒绝。
- stdout/stderr/result 太大 → 被截断导致 Agent 误判；该落盘就落盘并用 artifacts 引用。
- Skill 文档里“自己写输出”而不调用工具 → 失去可审计与可验证性（违反闭环目标）。
