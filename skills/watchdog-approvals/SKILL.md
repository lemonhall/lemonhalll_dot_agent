---
name: watchdog-approvals
description: Use when Codex repeatedly prompts for the same safe actions (running tests, reading logs, git operations) and the user wants those already-approved actions persisted into Codex approval config (trust levels + allow rules) so future sessions don’t require re-approval.
---

# 看门狗技能（Watchdog Approvals）

## Overview

把“用户已经明确批准过的安全行为”固化进 Codex 的审批配置，让下一次执行同类动作**不再反复弹确认**，同时避免把权限放大到不可控范围。

核心思想：**只持久化“确定安全且高频”的动作**，并且用最小化的 allowlist（可回滚、可审计）。

## What counts as “approved”?

仅指：在当前会话中，用户对某一类操作明确说过“可以/都授权/以后别再问/加入 allowlist”。

不包括：

- 没有得到用户明确授权的高风险动作（删除、执行未知二进制、访问敏感目录等）
- 只做一次的临时动作（除非用户要求持久化）

## Where Codex stores approvals (this environment)

通常需要同时看两处：

1) **Project trust level**（项目信任级别）
   - File: `~/.codex/config.toml`
   - Key: `[projects."<path>"] trust_level = "trusted" | "untrusted"`

2) **Command allow rules**（命令允许列表）
   - File: `~/.codex/rules/default.rules`
   - Format: `prefix_rule(pattern=[...], decision="allow")`
   - 含义：当命令 argv 以 `pattern` 为前缀时，直接允许

> 注意：这是用户机器上的安全边界配置。任何写入都必须可解释、可撤销、可最小化。

## Collaboration Rules（协作规则 / 安全纪律）

写入审批配置前，必须做到：

1) **先提案，后落盘**
   - 列出“候选允许项清单”（每条含：用途、风险、范围）
   - 让用户逐条确认（YES/NO）

2) **最小化授权**
   - 优先 allowlist **仓库内固定脚本**（例如 `scripts/run_*.sh|ps1`），不要直接 allowlist `/bin/bash -lc <任意命令>`
   - 不要 allowlist 带用户输入参数的危险命令（例如 `rm -rf <path>`），除非 path 是固定且安全的
   - 避免全局路径（例如把 `/mnt/e/development` 设为 trusted 会覆盖太多仓库；优先 repo root）

3) **可回滚**
   - 修改前备份：
     - `cp ~/.codex/rules/default.rules ~/.codex/rules/default.rules.bak`
     - `cp ~/.codex/config.toml ~/.codex/config.toml.bak`
   - 每次只加少量规则（1–5 条），并验证通过再继续

4) **可验证**
   - 写入后，立刻执行一次“原本会弹审批”的动作，确认已静默通过

5) **不伪造**
   - 不猜用户想授权什么；只从“用户明确批准过”的行为提炼规则

## How to extract “already approved actions” (practical workflow)

### Step 1 — Build a candidate list during the session

当出现审批提示且用户批准时，立刻记录一条候选项：

- **Action name**：例如 “Run headless Godot tests”
- **Exact command argv**（或更推荐：引导改成固定脚本后再 allowlist 脚本）
- **Scope**：只允许在本仓库？只允许某个固定参数组合？
- **Why safe**：为什么这是安全/可控/高频

### Step 2 — Normalize to a stable allow pattern

优先级（从安全到危险）：

1) allowlist：`scripts/<fixed entrypoint>`（强烈推荐）
2) allowlist：`git push` / `git status` 这类低风险固定子命令
3) allowlist：固定二进制 + 固定参数前缀（需要谨慎）
4) **禁止**：`/bin/bash -lc "<anything>"`（范围过大）

### Step 3 — Present proposal + get confirmation

用表格给用户逐条确认（YES/NO），示例：

| Candidate | Pattern | Why | Risk | Persist? |
|---|---|---|---|---|
| Run tests | `["scripts/run_godot_tests.ps1"]` | CI-equivalent | low | YES |

### Step 4 — Write config + verify

- 追加 `prefix_rule(...)` 到 `~/.codex/rules/default.rules`
- 如需信任仓库，写入 `~/.codex/config.toml` 的 `[projects."<repo-root>"] trust_level="trusted"`
- 运行一次验证命令（应不再弹审批）

## Checklist（执行清单）

- [ ] 列出本次会话里**重复出现**的审批点（命令/行为）
- [ ] 对每个候选项写：用途 / 风险 / 最小 pattern / 是否可改成固定脚本
- [ ] 让用户逐条 YES/NO
- [ ] 备份：
  - [ ] `cp ~/.codex/rules/default.rules ~/.codex/rules/default.rules.bak`
  - [ ] `cp ~/.codex/config.toml ~/.codex/config.toml.bak`
- [ ] 小步写入（1–5 条规则）
- [ ] 立刻验证一次“原本会弹审批”的动作
- [ ] 如果出现意外放权/误匹配：立刻回滚 `.bak` 并重新收敛 pattern

## Red Flags（看到就停）

- “先全部设成 trusted / allow all，省事”
- “给 /bin/bash -lc 做通配 allowlist”
- “加一个 rm -rf * 的规则”
- “没让用户逐条确认就落盘”

## Example: Safe patterns for this repo (参考)

建议优先 allowlist 固定脚本，而不是 Godot 二进制本身：

- Windows：
  - `scripts\\run_godot_tests.ps1`
- WSL/Linux：
  - 先封装一个 `scripts/run_godot_tests_linux.sh`（固定 `GODOT_LINUX_EXE`），再 allowlist 这个脚本

## Outcome

你最终交付的是：

- 更少的重复审批弹窗
- 不被放大的权限边界（最小 allowlist + 可回滚 + 可验证）
- 一套可复制的协作流程（提案 → 逐条确认 → 落盘 → 验证）
