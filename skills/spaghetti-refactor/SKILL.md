---
name: spaghetti-refactor
description: Use when a single file/class has grown into tightly coupled “spaghetti” (mixed UI, IO, state, input, gameplay), making changes risky, tests hard to write, and refactors frequently break behavior—especially under strict type/warning-as-error environments like Godot 4.x.
---

# 意大利面重构技能（Spaghetti Refactor）

## Overview

目标不是“变优雅”，而是把“高风险的一坨代码”拆成**可验证的小模块**：保持行为稳定、保持对外 API 稳定、让后续功能可以“在边上加模块”而不是继续往中心堆。

这份技能来自 `vr_offices/VrOffices.gd` 的多轮重构经验（v7–v9，以及后续迭代的延续实践）。

## When To Use

符合任意 2 条就该触发：

- 单文件/单类 > 300–500 行，且同时包含：输入处理、UI、数据、持久化、业务规则、第三方调用
- “改一个小功能 → 破三个地方”，你只能靠手测回归
- 你不敢重构，因为没有测试能兜底
- 严格模式让你寸步难行（warnings-as-errors / strict typing / lint 很凶）
- 需求还会继续加（未来功能多），继续堆只会更糟

不要用于：

- 只需要修一个明确 bug（先修 bug，再考虑重构）
- 项目还没任何测试/跑不起来（先建立最小 smoke test）

## Core Pattern（来自 v7–v9 的经验）

### 1) 先立“护栏”，再动刀（最关键）

- **先跑全套测试**拿到 baseline；没有测试就先写 1–2 个 smoke tests（能 headless 跑）。
- 明确“本轮不改玩法/不改 UI 结构/不动 demo_xxx”（除非就是目标）。
- 把“必须保留的 public API”写成清单（测试/场景依赖它们）。

### 2) 先抽“最稳定的层”：数据与 IO

把不会频繁变动的东西先抽走，收益最大、风险最小：

- 常量/配置/映射表 → `Data.gd`
- 世界状态读写 → `WorldState.gd`
- save/load glue → `SaveController.gd`

要点：**数据与 IO 从业务里剥离**，否则每次改业务都在改 IO。

### 3) 再抽“可替换的外设”：输入、移动、对话、音频

把“外设驱动”拆成 controller，主脚本只做 wiring：

- InputController：只负责事件路由与 gating（例如：对话框打开时屏蔽相机/鼠标）
- MoveController：只负责 raycast/夹紧边界/移动指示器
- DialogueController：只负责对话生命周期 + 镜头/角色姿态协调
- Bgm：只负责音频加载/循环/释放

原则：**一个 controller 只负责一种变化维度**。

### 4) 主脚本保持“编排层”（Orchestrator）

主脚本（例如 `VrOffices.gd`）只做：

- `@onready` 取节点
- new 各 controller/manager 并 connect 信号
- 保留薄 wrapper API（把调用转发出去）

这样后续功能（比如 workspaces）可以“新增模块 + 接线”，不会把主脚本再写回意大利面。

### 5) 严格模式下的坑位清单（Godot 4.x 特别重要）

- 避免 `var x := null` 让类型推断失败；用 `var x: Node = null` 或者不显式类型
- 避免变量名遮蔽（`name`, `scale`, `floor` 等）
- RegEx / Variant / Array 的类型推断谨慎处理（宁可显式转换）

## Step-by-Step Checklist（可直接照做）

1. **Define DoD**
   - “目标行数”只是结果，不是目的；DoD 必须包含：模块边界、保留 API、测试通过。
2. **Write/Strengthen Guard Tests**
   - smoke：场景能加载、关键节点存在、关键 API 可调用
   - persistence：save → reload 数据一致
3. **Extract Stable Modules First**
   - Data → IO → Controllers
4. **Keep Diffs Small**
   - 每次只搬一个职责；跑相关测试；commit；push。
5. **Refactor After Green**
   - 只在 tests green 后做清理（重命名、拆函数、去重复）。
6. **Verify Like a Robot**
   - 单测/集成测全绿；必要时加 `--verbose` 查泄漏/资源释放。

## Pressure Scenarios（“技能测试用例”）

1) **“我就想加个小功能，顺手把结构也改一改”**
- 期望行为：先写/跑 smoke test；再小步提取一个模块；不要“顺手重写半个系统”。

2) **“严格模式一直报错：类型推断/遮蔽/await”**
- 期望行为：先把这些警告归零（v9 风格）；再继续功能性重构。

3) **“文件太大，我想一次性拆成 10 个文件”**
- 期望行为：拆分按职责优先级分批做；每批都要能跑回归并可回滚。

## Deliverables（重构轮次的交付物）

- `docs/plan/vN-index.md`：写清楚目标、DoD、证据、验证命令
- 最少 1 个新的测试（或加强现有 smoke）来锁定行为
- 2–5 个小 commit（每个 slice 一个 commit + push）

