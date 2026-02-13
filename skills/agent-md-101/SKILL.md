---
name: agent-md-101
description: Use when starting a new repo or onboarding an AI agent and you need to create or overhaul an AGENTS.md so work stays safe, testable, and consistent across environments (e.g., Godot + SDK + demo apps), especially when the project has strict tooling, sandboxes, or multiple "products" in one codebase.
---

# 101 项目规约初始化技能：写出合格的 `AGENTS.md`

## Overview

`AGENTS.md` 是给 AI/新人看的"工程现实说明书"：把**能跑起来、不会误伤、可验证**的规则写清楚（而不是写漂亮但不可执行的口号）。

核心原则（综合 agents.md 官网 + OpenAI Codex 文档）：

- `AGENTS.md` 就是一个普通 Markdown 文件，**没有强制字段/格式**；但要尽量短、可扫描、可复制粘贴。
- **注意大小限制**：Codex 默认 `project_doc_max_bytes = 32768`（32 KiB）。超出会被截断，关键指令可能丢失。如果内容过多，拆分到子目录的 `AGENTS.md` 中。
- 可以在 repo 中放多个 `AGENTS.md`：**哪个目录就近/更具体，就以哪个为准**（子目录的规则覆盖父目录）。
- `AGENTS.md` 是**活文档**（living documentation）——每次架构变更、流程调整后都应同步更新，而不是写完就扔。
- 它与 `README.md` 互补而非替代：README 面向人类贡献者（快速上手、项目描述），`AGENTS.md` 面向 AI agent（构建步骤、测试命令、代码约定、安全边界等可能让 README 臃肿的细节）。
- 建议写你希望 agent "每次都遵守"的内容：项目概览、常用命令（安装/构建/测试/格式化）、代码约定、危险操作边界、安全/隐私注意事项等。

（参考：[agents.md 官网](https://agents.md/) · [GitHub 仓库](https://github.com/agentsmd/agents.md) · [OpenAI Codex AGENTS.md 指南](https://developers.openai.com/codex/guides/agents-md)）

## When To Use

- 新仓库刚建立，缺少工程规约/AI 开发规约
- 老项目 `AGENTS.md` 只写了"怎么跑"，但没有架构与禁忌，导致反复踩坑
- 一个 repo 里同时包含 SDK + 应用（或多 demo），容易把验证策略搞混
- 跨平台/跨边界执行很痛（WSL/Windows exe、CI、沙盒路径等）
- Agent 生成的代码风格混乱、不符合项目约定，需要统一规范

## Required Sections（最低合格线）

### 0) Quick Commands（让 agent 先跑起来）

写 3~6 条"最短可用命令"，并标注运行前置条件（Node/Python/Unity/Godot 版本、需要的系统依赖）。

至少包含：

- **安装依赖**：例如 `npm ci` / `uv sync`
- **本地开发**：例如 `npm run dev`
- **构建产物**：例如 `npm run build`
- **测试**：例如 `npm test` / `pytest`
- **格式化/Lint**：例如 `npm run lint` / `ruff check .`（如果项目有的话）

> 原则：命令要能直接复制执行；如果 Windows/WSL/Linux 不同，分开写。

### 1) Project Overview & Architecture（项目概览与架构）

#### 1a) Project Summary（一句话概览）

用 1~3 句话说清楚：**这个项目是什么、解决什么问题、面向谁**。Agent 需要这个上下文来做出合理的设计决策。

#### 1b) Architecture Overview（架构概览）

写清楚 3 件事：

- **系统拆分**：这个 repo 里有哪些"产品/子系统"（例如 SDK / 主应用 / demo）
- **关键路径**：每个子系统的入口文件、关键模块、核心数据结构的文件路径
- **数据流向**：从 UI/调用方 → 核心服务 → 外部依赖 → 回写/持久化 的路径（最好画一个 10 行以内的 ASCII 图）

必须包含：

- 配置入口（环境变量/配置文件/Autoload/启动参数）
- 持久化目录约定（尤其是 `user://` / `~/.config` / `AppData` 这种）

### 2) Code Style & Conventions（代码风格与约定）

> 官网首页示例的核心章节之一。Agent 生成的代码如果风格不统一，review 成本极高。

写清楚项目的**编码约定**，让 agent 生成的代码一次就符合规范。按需覆盖以下维度：

**语言与类型系统：**
- 使用的语言/版本（例如 TypeScript 5.x strict mode / Python 3.13+）
- 类型检查策略（例如 `strict: true` / `mypy --strict` / 无类型要求）

**格式化规则：**
- 缩进（空格 vs Tab、宽度）
- 引号风格（单引号 vs 双引号）
- 分号（有 vs 无）
- 行尾/换行符（LF vs CRLF）
- 最大行宽

**命名约定：**
- 文件/目录命名（kebab-case / snake_case / PascalCase）
- 变量/函数命名（camelCase / snake_case）
- 类/组件命名（PascalCase）
- 常量命名（UPPER_SNAKE_CASE）

**代码组织偏好：**
- 编程范式偏好（函数式 vs OOP vs 混合）
- import 排序规则（stdlib → third-party → local，是否使用自动排序工具）
- 模块/文件拆分原则（单一职责、最大行数等）

**自动化工具：**
- 格式化工具及配置（Prettier / Black / Ruff format）
- Lint 工具及配置（ESLint / Ruff / Clippy）
- 提交前检查（pre-commit hooks / husky + lint-staged）

> 原则：如果项目已有 `.editorconfig` / `.prettierrc` / `pyproject.toml [tool.ruff]` 等配置文件，在这里**指向它们**即可，不必重复内容。但要写清楚"以哪个配置文件为准"。

### 3) Safety & Conventions（"千万别这样做"）

写"事故预防清单"，而不是"编码风格建议"。

每条规则都用这个格式：

- **禁止事项**：不要做什么（明确到行为/文件/模块）
- **为什么**：会造成什么后果（安全/数据丢失/测试挂死/接口破坏）
- **替代方案**：该怎么做（具体命令/步骤/脚本）
- **验证方式**：怎么确认你做对了（测试命令/检查脚本）

常见必写项：

- "不要靠手测回归"
- "不要提交 secrets（密钥/Token/私有证书）"
- "不要绕过 sandbox / workspace 约束"
- "不要动生成物目录（如 `dist/`、`build/`、`vendor/`，除非有明确流程）"
- "涉及真实用户数据/线上资源时：先做 dry-run 或使用测试环境"

#### 3a) Security Considerations（安全注意事项）

> 官网 "Cover what matters" 明确列出的独立关注点。

- **密钥管理**：密钥/Token 存放位置（环境变量 / `.env` / vault），绝不硬编码、绝不提交到版本控制
- **依赖安全**：添加新依赖前是否需要审批、是否运行 `npm audit` / `pip-audit`
- **数据隐私**：哪些数据是敏感的（PII / 用户数据），处理时的脱敏/加密要求
- **网络边界**：哪些外部 API/服务可以调用，哪些不可以；是否需要走代理
- **权限最小化**：文件系统/数据库/云资源的访问权限原则

### 4) Testing Strategy（测试策略）

按"产品/模块"分组给出**最短可用命令**：

- **全量测试**（一条命令）
- **单个测试/单模块测试**（一条命令）
- **常见故障排查**（例如：卡死/超时/资源泄漏/verbose）

必须写清楚：

- 在不同环境下怎么跑（Windows / WSL / Linux）
- 避免 hung tests 的策略（每用例 timeout）
- 哪些测试属于 SDK，哪些属于应用层（避免只跑 demo 测试误判）
- **改了代码就要加/改测试**——即使没人要求（官网示例原文："Add or update tests for the code you change, even if nobody asked."）

### 5) Scope & Precedence（多份 `AGENTS.md` 的覆盖关系）

把覆盖规则写明白，避免在 monorepo 里"照错规矩办事"。

#### 5a) 基本覆盖规则

- 根目录 `AGENTS.md`：默认规则（适用全仓库）
- 子目录 `AGENTS.md`：对该子目录树生效，**覆盖**根目录同主题规则
- 如有冲突：以**更具体（更靠近文件）的 `AGENTS.md`** 为准；用户的显式指令始终优先

#### 5b) Override 机制（Codex 特性）

- 同一目录下，`AGENTS.override.md` 优先于 `AGENTS.md`（前者存在时后者被忽略）
- 用途：临时覆盖某个目录的规则，而不需要修改/删除原始 `AGENTS.md`
- 移除 override 文件即可恢复原始规则

#### 5c) 全局指令（~/.codex/AGENTS.md）

- Codex 在每次运行时，先读取 `~/.codex/AGENTS.md`（或 `~/.codex/AGENTS.override.md`），再读取项目级文件
- 适合放置跨项目通用的个人偏好（如"优先用 pnpm"、"修改 JS 文件后必须跑测试"）
- 可通过 `CODEX_HOME` 环境变量切换不同的全局配置 profile

#### 5d) 发现顺序（Codex 实现细节）

Codex 的指令链构建顺序：
1. **全局**：`~/.codex/AGENTS.override.md` → `~/.codex/AGENTS.md`（取第一个非空文件）
2. **项目**：从 Git 根目录向下逐级扫描到当前工作目录，每级检查 `AGENTS.override.md` → `AGENTS.md` → fallback filenames（每级最多取一个文件）
3. **合并**：按从根到叶的顺序拼接，后出现的内容覆盖先出现的

> 注意：如果你的项目已有其他名称的指令文件（如 `TEAM_GUIDE.md`），可在 `~/.codex/config.toml` 中配置 `project_doc_fallback_filenames`。

## Recommended Sections（强烈建议）

- **Repo Safety / Permissions**：哪些操作会触发跨边界审批、怎么最小化审批
- **Runtime Config**：关键 env vars（示例：`OPENAI_API_KEY`、`*_BASE_URL`、`*_MODEL`）；只写变量名/示例值，避免写真实密钥
- **PR / Review**：标题格式（如 `[<module>] <Title>`）、必跑检查（lint/test/typecheck）、合并门槛；提交前必须运行的命令清单
- **Commit Message Convention**：格式（Conventional Commits / 自定义）、scope 列表、示例
- **Release / Export / Deployment Notes**：发布/打包/上架要点与陷阱；部署步骤（尤其是需要特殊权限或审批的）
- **Documentation Policy**：改了公共 API/行为时，是否需要同步更新 `docs/` 目录
- **Legacy note**：如果历史上存在 `AGENT.md`，建议统一迁移到 `AGENTS.md`（必要时用符号链接保持兼容：`mv AGENT.md AGENTS.md && ln -s AGENTS.md AGENT.md`）
- **Codex-specific Config Tips**：
  - `project_doc_fallback_filenames`：自定义备选文件名
  - `project_doc_max_bytes`：调整大小上限（默认 32 KiB）
  - 验证命令：`codex --ask-for-approval never "Summarize the current instructions."`

## Template（可复制）

```md
# Agent Notes (<Project Name>)

## Project Overview
<!-- 1~3 句话：这个项目是什么、解决什么问题 -->

## Quick Commands
- Install: `<command>`
- Dev: `<command>`
- Build: `<command>`
- Lint: `<command>`
- Test (full): `<command>`
- Test (single): `<command>`

## Architecture Overview
### Areas
- SDK:
  - entry: `path/to/entry`
  - core: `path/to/core`
- App:
  - main: `path/to/main`
  - modules: `path/to/modules`
- Demos:
  - `path/to/demo`

### Data Flow
<!-- 10 行以内 ASCII 图 -->

### Persistence
- config: `...`
- data: `...`
- logs: `...`

## Code Style
<!-- 指向配置文件，或直接列出关键规则 -->
- Language: <language> <version>
- Formatter: <tool> (config: `<path>`)
- Linter: <tool> (config: `<path>`)
- Naming: files=`kebab-case`, vars=`camelCase`, classes=`PascalCase`
- Quotes: <single/double>, Semicolons: <yes/no>
- Imports: <ordering rule>
- Paradigm preference: <functional/OOP/mixed>

## Safety & Conventions
- Do not ...
  - Why:
  - Do instead:
  - Verify:

### Security
- Secrets: never hardcode; use env vars / `.env` (gitignored)
- New deps: require review / audit
- Sensitive data: <handling rules>

## Testing Strategy
### Full
`<command>`
### Module
`<command>`
### Debugging
`<command>`
### Rules
- Always add/update tests for changed code.
- All tests must pass before merge.

## PR Instructions
- Title format: `[<module>] <Title>`
- Before committing: `<lint>` and `<test>`
- Update docs if public behavior changes.

## Scope & Precedence
- Root `AGENTS.md` applies by default.
- Subdir `AGENTS.md` overrides within its subtree.
- `AGENTS.override.md` in the same dir takes priority over `AGENTS.md`.
- User's explicit chat instructions override everything.
- Global `~/.codex/AGENTS.md` provides cross-project defaults.
```

## Red Flags（看到就停）

- "先把功能写了，测试后面再补"
- "手动点点看没问题"
- "顺手把 demo 也改一下"
- "这次不需要写进 AGENTS.md"
- "反正我知道路径/命令，写不写都一样"
- "代码风格无所谓，能跑就行"
- "AGENTS.md 写一次就够了，不用更新"
- "32 KiB 不够就全塞一个文件里"