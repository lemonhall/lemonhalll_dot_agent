---
name: versioned-audit-remediation-loop
description: 适用于“先并发审阅某个版本系列或里程碑链路，再形成 prioritized backlog，最后按 issue 顺序逐条修复”的任务。用于用户要求审计 `vN` 系列代码/文档、汇总问题、生成 P0/P1/P2 backlog、回写计划文档、并按 TDD + 验证闭环连续修复时；尤其适合有 `docs/plan/vN-*`、`docs/superpowers/plans/`、版本化 issue 文档和通知要求的仓库。
---

# Versioned Audit Remediation Loop

先把一次版本化治理任务拆成三段，再决定当前所在阶段：

1. **Audit**：并发审阅代码、计划文档、状态机、客户面、后台治理面，产出一份问题清单。
2. **Backlog**：把问题清单重写成可执行 backlog，补优先级、文档回写点、实现方向、最低验收。
3. **Execute**：按 backlog 顺序逐条修复，每条 issue 都同时完成计划文档、代码、测试、验证、状态回写。

如果用户已经完成前两段，只要求“一个一个修过去”，直接进入 `Execute`，不要重新做 audit。

## Quick Start

按下面顺序推进，不要跳步：

1. 先读版本入口文档，通常是 `docs/plan/vN-index.md`、`docs/plan/vN-issue-backlog.md`、相关主题计划文档。
2. 判断当前任务属于 `Audit`、`Backlog` 还是 `Execute`。
3. 如果用户**明确授权** subagent / 并发代理，就按独立审计维度并发分工；否则本地顺序做。
4. 所有结论必须落成仓库内 Markdown，不只停留在聊天里。
5. 进入修复阶段后，严格按 backlog 顺序逐条做，不要平均用力。

审计维度和模板见：

- 审计维度：[references/audit-axes.md](references/audit-axes.md)
- Markdown 模板：[references/templates.md](references/templates.md)

## Phase 1: Audit

先确认 source of truth：

1. 版本入口文档
2. 相关实现代码
3. 现有测试
4. 如果存在，上一轮审计结论或未完成 issue 文档

并发审阅时，只按独立维度拆，不按文件平均切块。优先拆成：

1. 客户交易主链
2. 支付与补偿链
3. 安全与共享环境边界
4. 后台治理、审计、可归责
5. 回归测试与覆盖空洞

每个审阅线程都只回答四件事：

1. 问题是什么
2. 为什么危险
3. 根因在哪里
4. 最小修复方向是什么

审计输出默认写成一份 Markdown 汇总，不在这个阶段直接改代码，除非用户明确要求“边审边修”。

## Phase 2: Backlog

把审计问题重写成 backlog 时，统一收口到：

1. `Issue ID`
2. 标题
3. 优先级 `P0/P1/P2`
4. 问题描述
5. 为什么是这个优先级
6. 需要改的文档
7. 文档改法
8. 实现思路
9. 最低验收

优先级建议：

1. `P0`：安全暴露、错误写状态、共享环境没锁、直接破坏客户交易主链。
2. `P1`：钱单事实不稳、补偿链不闭环、后台动作不可归责。
3. `P2`：正确性、体验一致性、回归保护债。

backlog 不只是问题列表，而是执行入口。写完后，要求任何后续修复都按 backlog 顺序推进，并在完成后回写状态与验证证据。

## Phase 3: Execute

进入逐条修复后，每个 issue 都按同一闭环推进：

1. 先补该 issue 的计划文档，路径默认放 `docs/superpowers/plans/YYYY-MM-DD-vN-issue-XXX-<topic>.md`
2. 先写红测，确认失败原因就是目标缺陷
3. 再做最小实现
4. 再跑绿测和必要 build
5. 再回写相关计划文档、`vN-index`、`vN-issue-backlog`
6. 最后发送通知或交付信号

不要只改代码。每条 issue 完成必须同时满足：

1. 代码问题已修复
2. 文档已回写
3. 测试或验证命令已实际跑过

## Hard Rules

1. 不要跳过 backlog 顺序，除非用户明确重排优先级。
2. 不要只给建议不落地；如果用户要修，就继续修到该 issue 验证完成。
3. 不要把 unrelated dirty worktree 当成可清理对象。
4. 不要在没 fresh verification evidence 时声称“完成”“已修复”“通过”。
5. 不要把“测试补齐”误写成“生产逻辑已修改”；如果只是覆盖债，就明确写清楚实现未变。
6. 如果用户要求 APN、Slack、邮件或其他通知，把它当作完成定义的一部分。

## Decision Tree

**用户说“先审计整个 vN 系列”**
先做 `Audit`，必要时并发代理，最后输出一份审计 Markdown。

**用户说“把这些问题变成 backlog”**
做 `Backlog`，不要急着改代码。

**用户说“按 backlog 一个个修过去”**
直接做 `Execute`，从第一条未完成 issue 开始，持续推进。

**用户说“把这份 backlog/文档用人话说一遍，再一起决策”**
先口语化解释，再把用户决策固化回 backlog 口径，然后继续执行。

## Output Contract

默认输出产物：

1. 一份 audit findings 文档
2. 一份 issue backlog 文档
3. 每个 issue 一份执行计划文档
4. 回写后的版本计划文档

默认最终汇报只说三类信息：

1. 这一条 issue 改了什么
2. 跑了哪些验证
3. 还剩什么下一步

## Resources

在真正写 Markdown 前，按需读取：

- [references/audit-axes.md](references/audit-axes.md)
- [references/templates.md](references/templates.md)
