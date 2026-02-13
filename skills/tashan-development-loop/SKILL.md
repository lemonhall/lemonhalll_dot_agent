---
name: tashan-development-loop
description: 适用于需要 PRD/Spec + 版本化执行计划（docs/plan/vN-*）+ 端到端验证的项目。通过严格的 PRD ↔ 计划 ↔ 测试 ↔ 代码追溯链，防止文档漂移与返工，直到愿景与实现之间无差异、无保留、无妥协。
---

# 塔山项目循环（愿景 → 分解计划 → 里程碑 → 执行 → 回顾差异 → 新版本计划…直到收敛）

## 命名由来

> 1948 年辽沈战役期间，东北野战军在塔山阻击国军援锦部队。塔山不过是一个百余户人家的小村庄，无塔无山，唯一的价值是锦西通往锦州的公路铁路从此穿过。六天六夜，国军以 11 个师、海空火力猛攻，解放军以 8 个师死守，阵地九度易手。战斗最激烈时，东北野战军司令员林彪向第二兵团司令员程子华下令：
>
> **"我不要伤亡数字，我只要塔山。"**
>
> 塔山最终未失，锦州攻克，辽沈战役胜局奠定。坚守塔山的第 4 纵队第 12 师第 34 团战后仅余 21 人，被授予"塔山英雄团"称号。
>
> 本循环取名"塔山"，取其精神：**目标一旦锁定，不讲条件、不找借口、不打折扣，用纪律和证据一寸一寸地守住，直到拿下。**

---

## 目录

- [Overview](#overview)
- [适用范围与不适用场景](#适用范围与不适用场景)
- [Quick Reference（10 步速查）](#quick-reference10-步速查)
- [层级关系图](#层级关系图)
- [PRD / Spec（设计图）](#prd--spec设计图)
- [变更通知单（ECN）](#变更通知单ecn)
- [文档与命名约定（doc/plan）](#文档与命名约定docplan)
- [计划文件模板（vN-topic.md）](#计划文件模板vn-topicmd)
- [DoD 硬度自检（强制 Gate）](#dod-硬度自检强制-gate)
- [文档完整性自检（Doc QA Gate）](#文档完整性自检doc-qa-gate)
- [执行计划：塔山开发循环（Strict）](#执行计划塔山开发循环strict)
- [端到端测试（E2E Gate）](#端到端测试e2e-gate)
- [测试用例编写规范](#测试用例编写规范)
- [回顾差异（愿景 vs. 现实）](#回顾差异愿景-vs-现实)
- [提交与推送（强制）](#提交与推送强制)
- [计划变更处理规则](#计划变更处理规则)
- [Pressure Scenarios（常见跳步诱因）](#pressure-scenarios常见跳步诱因)
- [Red Flags — STOP and Start Over](#red-flags--stop-and-start-over)
- [Rationalization Table（Close the Loops）](#rationalization-tableclose-the-loops)
- [Anti-Patterns](#anti-patterns)
- [自动检查（推荐）](#自动检查推荐)

---

## Overview

塔山项目循环的目标不是"写代码"，而是让项目从愿景出发，经过可执行的计划与里程碑，进入可验证的开发闭环；每一轮交付都要回顾"实现与愿景的差异"，并形成下一版本计划，循环往复，直至愿景与实现之间无差异、无保留、无妥协为止。

核心关系：

- **PRD / Spec**（设计图）：回答"要造什么、为什么、边界与验收是什么"。
- **vN 计划文档**（施工计划）：回答"这一版怎么交付、如何验证、风险是什么"。
- **变更通知单（ECN）**：回答"施工过程中发现了什么设计偏差、如何修正"。

这三者必须有**可追溯关系**，否则一定会出现：

- PRD 写得很漂亮，但计划/测试/代码跑偏；
- 计划写得很硬，但 PRD 缺关键约束，导致返工；
- 施工中发现设计问题，口头修改但不留痕，后续无法追溯；
- 文档越来越多，但没有统一口径与证据链，只能靠记忆推进。

---

## 适用范围与不适用场景

### 适用

- 需要 PRD/Spec 的中大型功能开发
- 多轮迭代、多人协作的项目
- 需要可追溯验收证据的交付

### 不适用

- **10 行 bugfix**：直接写测试 → 修复 → 提交，不需要走全流程
- **纯探索性 spike**：写一个时间盒（timeboxed）的探索文档，记录发现，不需要 PRD
- **文档/配置微调**：直接提交，不需要 vN 计划

### 多人协作注意

本 SKILL 默认假设**单线程执行**（一个人或一个 agent）。多人并行时需额外约定：谁拥有 `vN-index` 的写权限、plan 冲突如何合并、ECN 的审批流程。

---

## Quick Reference（10 步速查）

| # | 步骤 | 产物 | 详见章节 |
|---|------|------|----------|
| 0 | 写 PRD / Spec | `docs/prd/PRD-NNNN-<topic>.md` | [PRD / Spec](#prd--spec设计图) |
| 1 | 建立愿景 | 写在 PRD 顶部或独立文档 | [PRD / Spec](#prd--spec设计图) |
| 2 | 分解执行计划 | `docs/plan/vN-<topic>.md` | [计划文件模板](#计划文件模板vn-topicmd) |
| 3 | 建立里程碑 | `docs/plan/vN-index.md` | [文档与命名约定](#文档与命名约定docplan) |
| 4 | DoD 硬度自检 | 通过后才允许写代码 | [DoD 硬度自检](#dod-硬度自检强制-gate) |
| 5 | 文档完整性自检 | 通过后才允许写代码 | [文档完整性自检](#文档完整性自检doc-qa-gate) |
| 6 | 执行计划（塔山开发循环） | 红→绿→重构，证据优先 | [执行计划](#执行计划塔山开发循环strict) |
| 7 | 端到端测试 | E2E 测试通过 | [端到端测试](#端到端测试e2e-gate) |
| 8 | 回顾差异 | 差异清单写入 `vN-index` | [回顾差异](#回顾差异愿景-vs-现实) |
| 9 | 形成新版本计划 + 提交推送 | `v(N+1)-index.md` + git push | [提交与推送](#提交与推送强制) |

---

## 层级关系图

```
塔山项目循环（本文档）
├── 0. PRD / Spec（设计图）── PRD-NNNN-<topic>.md
│     └── 变更通知单（ECN）── ECN-NNNN-<topic>.md
├── 1. 愿景（写在 PRD 顶部或独立文档）
├── 2. 分解计划 ── vN-<topic>.md
├── 3. 里程碑 ── vN-index.md
├── 4. DoD 硬度自检（Gate）
├── 5. 文档完整性自检（Gate）
├── 6. 执行 ← 塔山开发循环（Red → Green → Refactor）
│     ├── 单元测试 / 集成测试（TDD 驱动）
│     └── 端到端测试（E2E Gate）
├── 7. 回顾差异
├── 8. 新版本计划 + 提交推送
└── 9. 重复直到收敛
```

---

## PRD / Spec（设计图）

PRD 的目标不是"看起来很完整"，而是提供**稳定口径**与**可追溯锚点**，让后续计划/测试/代码都能引用它。

### 命名规则

```
docs/prd/PRD-NNNN-<topic>.md
```

- `NNNN`：四位顺序编号，从 `0001` 开始，全局唯一递增。
- `<topic>`：简短英文描述，用连字符分隔（如 `user-auth`、`data-pipeline`）。
- 示例：`docs/prd/PRD-0001-user-auth.md`、`docs/prd/PRD-0002-payment-flow.md`

### 写法要求

- 每条需求都有 **Req ID**（格式 `REQ-NNNN-NNN`，前四位对应 PRD 编号，后三位为需求序号）。
  - 示例：`REQ-0001-001`（PRD-0001 的第 1 条需求）
- 每条需求写清：**动机、范围、非目标、验收口径**（可二元判定）。
- 术语与数据结构有统一命名（避免同一概念在不同文档里换名）。
- 把关键"**约束/不接受什么/不做什么**"写清楚（这是返工的最大来源）。

### 愿景

愿景写在 PRD 顶部的 `## Vision` 段落，或独立为 `docs/prd/VISION.md`。要求：

- 可验收的文字/指标/行为定义（不是口号）
- 至少包含：最终用户是谁、核心价值是什么、成功长什么样

### 推荐模板与检查清单

- PRD 模板：`references/prd-template-openspec.md`
- 文档自检清单：`references/doc-review-checklist.md`
- 追溯矩阵模板：`references/traceability-matrix-template.md`

---

## 变更通知单（ECN）

在施工（执行计划）过程中，如果发现 PRD 设计与实际情况不符、或设计未考虑到的问题，**不得口头修改后继续施工**。必须走变更通知单流程。

### 命名规则

```
docs/ecn/ECN-NNNN-<topic>.md
```

- `NNNN`：四位顺序编号，从 `0001` 开始，全局唯一递增。
- `<topic>`：简短英文描述。
- 示例：`docs/ecn/ECN-0001-auth-token-expiry.md`

### ECN 模板

```markdown
# ECN-NNNN: <标题>

## 基本信息

- **ECN 编号**：ECN-NNNN
- **关联 PRD**：PRD-XXXX
- **关联 Req ID**：REQ-XXXX-XXX（如果是新增需求则写"新增"）
- **发现阶段**：vN-<topic> 的第 N 步
- **日期**：YYYY-MM-DD

## 变更原因

（描述发现了什么问题、为什么 PRD 原设计不适用或不完整）

## 变更内容

### 原设计

（引用 PRD 原文或摘要）

### 新设计

（写清楚变更后的设计，包括新的验收口径）

## 影响范围

- 受影响的 Req ID：
- 受影响的 vN 计划：
- 受影响的测试：
- 受影响的代码文件：

## 处置方式

- [ ] PRD 已同步更新（标注 ECN 编号）
- [ ] vN 计划已同步更新
- [ ] 追溯矩阵已同步更新
- [ ] 相关测试已同步更新
```

### 处理规则

1. **发现问题 → 立即写 ECN**（哪怕只是一段话），不要"先改了再说"。
2. **ECN 写完后同步更新 PRD**：在 PRD 对应段落标注 `[已由 ECN-NNNN 变更]`。
3. **ECN 写完后同步更新 vN 计划**：如果影响当前计划，在 vN-index 的差异列表中记录。
4. **小变更**（不改变需求范围/验收口径）：ECN 可以简化为 3-5 行，但必须留痕。
5. **大变更**（新增/删除需求、改变验收口径）：ECN 必须完整填写，并考虑是否需要开 v(N+1)。

---

## 文档与命名约定（doc/plan）

每一轮计划用一个版本号 `vN`（`N` 从 1 开始）：

- `docs/plan/v1-index.md`：总论与索引
- `docs/plan/v1-<topic>.md`：单项计划
- 下一轮迭代：`docs/plan/v2-index.md`、`docs/plan/v2-<topic>.md`……

### vN-index 必须包含

| 段落 | 内容 |
|------|------|
| **愿景** | 链接到 PRD/愿景文档（或直接写在 index 里） |
| **里程碑** | 名称、范围、DoD、验证命令/测试、状态（todo/doing/done） |
| **计划索引** | 链接到所有 `vN-<topic>.md` |
| **追溯矩阵** | `Req ID → vN-xxx → tests/commands → 证据`（任何断链都要补齐） |
| **ECN 索引** | 本轮涉及的所有 ECN 编号与摘要 |
| **差异列表** | 本轮结束后仍未达成的差异（用于生成 v(N+1)） |

---

## 计划文件模板（vN-topic.md）

每个计划必须可执行、可验收、可验证，至少包含：

- **Goal**：这一项完成后，愿景的哪个部分被满足？
- **PRD Trace**：对应的 `Req ID`（至少 1 条；没有就说明为什么这不是需求实现而是基础设施/偿债）。
- **Scope**：做什么/不做什么（边界写清楚）。
- **Acceptance**：验收标准（尽量能转成测试断言或可重复验证命令）。
- **Files**：会创建/修改/测试哪些路径（精确到文件）。
- **Steps**（严格按顺序）：
  1. 写失败测试（红）
  2. 运行到红（给命令 + 预期失败原因）
  3. 实现（绿）：实现满足测试与验收的行为
  4. 运行到绿（给命令 + 预期通过）
  5. 必要重构（仍绿）
  6. E2E 测试（如适用）
- **Risks**：本计划的主要风险与缓解方式。

---

## DoD 硬度自检（强制 Gate）

在进入 `TDD Red` 之前，必须对本轮计划的 DoD/Acceptance 做一次硬度自检。**不过关就停止写代码。**

### 硬度标准（必须全部满足）

1. 每条 DoD 必须**可二元判定**（pass/fail）或**可量化**（数字/阈值/比例），禁止"看起来 / 差不多 / 尽量 / 优化一下 / 改善质量"。
2. 每条 DoD 必须绑定一个**可重复的验证方式**：命令/测试/脚本 + 预期输出（exit code、关键日志关键词、文件产物路径）。
3. DoD 必须包含至少 1 条**反作弊条款**，能阻止"只做改名 / 空壳 / 空实现 / 只跑通"就宣称完成。
4. Scope 必须写清楚**不做什么**，避免无边界扩张或用"之后再说"逃逸。

### 失败处理

只要上述任意一条不满足：**停止**，回到 Analysis/Design/Plan 重写 DoD（必要时拆分为更小的 `vN-<topic>`），直到全部满足。在 DoD 写硬之前：**禁止写实现、禁止"先糊一个再补测试"**。

### 示例对照

| 软 DoD（禁止） | 硬 DoD（推荐） |
|---|---|
| "把 smoke 测试改名" | "`tests/**` 下无 `*smoke*` 文件名" |
| "加一个基本测试" | "每个 `test_*.py` ≥ 10 个 test case，覆盖正常/异常/边界" |
| "功能应该没问题" | "`scripts/run_tests.sh --suite X` 全绿 + exit code 0" |
| "跑起来不崩" | "E2E 测试覆盖核心用户流程，Playwright 脚本全绿" |

---

## 文档完整性自检（Doc QA Gate）

在写任何实现之前，必须完成一次文档完整性自检，目标是把返工前置到文档阶段。

### 最低要求

- PRD 中每条 `Req ID` 都有：范围、非目标、验收口径（可二元判定）、优先级/阶段归属。
- vN 的每条计划都能追溯到 `Req ID`（或明确说明这是基础设施/偿债，不属于需求交付）。
- vN 的每条验收都带验证命令 + 预期输出（不能只写"应该可以/看起来/优化"）。
- 术语一致：同一概念/字段/ID 在 PRD、计划、测试与代码中命名一致。
- 所有 ECN 已同步到 PRD 和 vN 计划。

更详细的自检清单见 `references/doc-review-checklist.md`。

---

## 执行计划：塔山开发循环（Strict）

目标：把纪律固化成默认行为。不要先写实现、不要先堆工程量、不要凭感觉说完成。只认：可复现的分析、可执行的计划、可跑的测试、可验证的输出。

### Checklist（Copy/Paste 到 update_plan）

严格按顺序推进，一次只做一个 `in_progress`：

1. **Analysis**：收集事实 + 约束 + 成功标准
2. **Design**：方案选择 + 取舍（如果已由计划锁定方案，写"引用 vN-xxx 的方案选择"）
3. **Plan**：拆任务 + 明确文件/命令/预期（并把 `Req ID` 写进每条计划）
4. **TDD Red**：写失败测试 + 跑到红（包括单元测试和边界条件测试）
5. **TDD Green**：实现 + 跑到绿
6. **Refactor**：必要重构（仍绿）
7. **E2E**：运行端到端测试（如适用），确保用户流程完整
8. **Review**：复盘 + 风险 + 更新 PRD/追溯矩阵/ECN，避免文档漂移
9. **Ship**：`git commit` + `git push`（按版本/里程碑组织提交信息）

### 红绿灯（证据优先）

在声称"完成/修复/通过"之前：

1. 跑最相关的**单元/集成测试**，以输出为证据
2. 跑**端到端测试**（如适用），以输出为证据
3. 再跑更大范围的验证（按里程碑执行）

---

## 端到端测试（E2E Gate）

TDD 驱动的单元测试和集成测试保证了"零件"的正确性，但**不能替代端到端测试**。E2E 测试验证的是"整条用户流程是否跑通"，是最接近真实验收的自动化手段。

### 强制要求

- 每个里程碑至少有 **1 个 E2E 测试**覆盖其核心用户流程。
- E2E 测试必须是**自动化的、可重复的、有明确断言的**（不是"手动点一遍看看"）。
- E2E 测试的通过是里程碑 DoD 的一部分，不通过不算完成。

### 技术栈推荐

| 项目类型 | 推荐 E2E 工具 | 说明 |
|----------|--------------|------|
| Web 前端 / 全栈 Web | **Playwright** | 跨浏览器、支持截图/录屏、API 拦截、可视化调试 |
| Web API / 后端服务 | **Playwright API testing** 或 **pytest + httpx** | 验证完整请求链路 |
| 移动端 | **Detox**（React Native）/ **Maestro** | 真机/模拟器自动化 |
| CLI 工具 | **Shell 脚本 + 断言** 或 **bats-core** | 验证完整命令链路 |
| 桌面应用 | **Playwright**（Electron）/ **PyAutoGUI** | 视具体框架选择 |
| 游戏 / Godot | **GdUnit4** + 场景级测试 | 验证完整游戏流程 |

### E2E 测试编写规范

```
tests/e2e/
├── test_user_registration_flow.py    # 一个文件 = 一个用户流程
├── test_payment_checkout_flow.py
├── test_data_export_flow.py
└── conftest.py                       # 共享 fixtures
```

每个 E2E 测试必须：

1. **有明确的用户故事**：注释写清"作为 X，我做 Y，期望 Z"。
2. **覆盖完整流程**：从入口到出口，不跳步。
3. **有失败时的诊断信息**：截图、日志、网络请求记录。
4. **可独立运行**：不依赖其他测试的执行顺序或副作用。

### Playwright 示例（Web 项目）

```python
# tests/e2e/test_user_login_flow.py
import pytest
from playwright.sync_api import Page, expect

def test_user_can_login_and_see_dashboard(page: Page):
    """
    用户故事：作为已注册用户，我输入正确的邮箱和密码，
    期望看到 Dashboard 页面并显示我的用户名。
    对应 Req ID: REQ-0001-003
    """
    # 1. 导航到登录页
    page.goto("/login")
    expect(page.get_by_role("heading", name="Login")).to_be_visible()

    # 2. 填写表单
    page.get_by_label("Email").fill("test@example.com")
    page.get_by_label("Password").fill("secure-password-123")
    page.get_by_role("button", name="Sign In").click()

    # 3. 验证跳转到 Dashboard
    expect(page).to_have_url("/dashboard")
    expect(page.get_by_text("Welcome, Test User")).to_be_visible()

def test_user_sees_error_on_wrong_password(page: Page):
    """
    用户故事：作为已注册用户，我输入错误密码，
    期望看到错误提示，不跳转。
    对应 Req ID: REQ-0001-004
    """
    page.goto("/login")
    page.get_by_label("Email").fill("test@example.com")
    page.get_by_label("Password").fill("wrong-password")
    page.get_by_role("button", name="Sign In").click()

    expect(page.get_by_text("Invalid credentials")).to_be_visible()
    expect(page).to_have_url("/login")  # 未跳转
```

---

## 测试用例编写规范

测试不是"写几个 happy path 就完事"。测试是**需求的可执行表达**，必须覆盖正常、异常、边界三类场景。

### 三类必写场景

| 类型 | 说明 | 示例 |
|------|------|------|
| **正常路径（Happy Path）** | 标准输入 → 预期输出 | 用户输入合法邮箱和密码 → 登录成功 |
| **异常路径（Error Path）** | 非法/缺失/冲突输入 → 预期错误处理 | 空密码 → 报错；重复注册 → 报错 |
| **边界条件（Boundary）** | 极值/临界/特殊字符/并发/超时 | 密码恰好 8 位（最小长度）；密码 128 位（最大长度）；Unicode 用户名 |

### 边界条件检查清单

每次写测试时，对照以下清单逐条检查是否需要覆盖：

- [ ] **空值 / null / undefined / 空字符串**
- [ ] **最小值 / 最大值 / 刚好超出范围**
- [ ] **零 / 负数 / 极大数**
- [ ] **特殊字符**：`<script>`、SQL 注入、Unicode、emoji、换行符
- [ ] **重复操作**：连续提交两次、重复创建
- [ ] **并发 / 竞态**：两个请求同时修改同一资源
- [ ] **超时 / 网络异常**：请求超时、连接断开
- [ ] **权限边界**：未登录访问、越权访问、过期 token
- [ ] **数据量边界**：空列表、单条、大量数据（分页边界）
- [ ] **状态转换边界**：从 A 状态到 B 状态的合法/非法转换

### 测试命名规范

```
test_<被测行为>_<输入条件>_<预期结果>
```

示例：
- `test_login_with_valid_credentials_returns_token`
- `test_login_with_empty_password_returns_400`
- `test_login_with_expired_token_returns_401`
- `test_create_user_with_duplicate_email_returns_409`

### 测试与 Req ID 的追溯

每个测试文件或测试函数的 docstring 中必须标注对应的 `Req ID`：

```python
def test_password_minimum_length():
    """
    REQ-0001-005: 密码最小长度为 8 位
    边界条件：7 位应失败，8 位应成功
    """
    assert validate_password("1234567") == False   # 7 位 → 失败
    assert validate_password("12345678") == True    # 8 位 → 成功
```

## 回顾差异（愿景 vs. 现实）

回顾的产物不是"总结"，而是**差异清单**：

| 类型 | 内容 | 要求 |
|------|------|------|
| **已满足** | 哪些愿景点已满足 | 必须附证据：测试通过截图/命令输出/日志/链接 |
| **未满足** | 哪些仍未满足 | 写清：缺什么、为什么缺、影响是什么、是否进入下一轮 |
| **新增发现** | 本轮新增发现 | 需求澄清/约束变化/真实用户反馈/施工中发现的设计缺陷 |

### 处理流程

1. 把差异写进本轮 `vN-index` 的差异列表。
2. 如果差异涉及 PRD 设计问题 → 先写 ECN，再更新 PRD。
3. 把每条未满足差异落到下一轮 `v(N+1)-<topic>` 的可执行计划中。
4. 新增发现如果是需求级别的 → 补充 PRD 的 Req ID（通过 ECN 流程）。

---

## 提交与推送（强制）

保持"每个 slice 一个 commit + push"，即每一个 feature 或每一批新生成的文档，都需要做一个提交和 push。

```bash
git status --porcelain=v1
git add -A
git commit -m "vN: <short message>"
git push
```

### 提交信息规范

```
vN: <类型>: <简短描述>

类型包括：
- feat:     新功能实现
- test:     新增/修改测试
- doc:      文档（PRD/plan/ECN）
- fix:      缺陷修复
- refactor: 重构（不改变行为）
- chore:    基础设施/工具链
```

示例：
- `v1: doc: PRD-0001 user-auth 初稿`
- `v1: test: REQ-0001-003 登录流程 E2E 测试（红）`
- `v1: feat: REQ-0001-003 登录流程实现（绿）`
- `v1: doc: ECN-0001 token 过期策略变更`

### 推送失败处理

如果推送失败（网络/权限/远程未配置），必须在 `vN-index` 的回顾区明确记录失败原因与下一步；**不得"假装已交付"**。

---

## 计划变更处理规则

执行过程中发现计划本身有误（不是"差异"，而是"计划写错了"），按以下规则处理：

| 情况 | 处理方式 |
|------|----------|
| **未开始执行的条目** | 可以原地修改 vN 计划，在文档顶部记录变更原因与日期 |
| **已开始执行的条目（小改）** | 写 ECN → 更新 PRD → 修改 vN 计划并标注 `[由 ECN-NNNN 变更]` |
| **已开始执行的条目（大改）** | 在 vN-index 标注该条目废弃原因，差异进入 v(N+1) |
| **发现 PRD 设计缺陷** | 必须走 ECN 流程，不得口头修改后继续施工 |

---

## Pressure Scenarios（常见跳步诱因）

| # | 压力类型 | 典型表现 |
|---|----------|----------|
| 1 | 时间压力 | "先做出来再补测试/文档。" |
| 2 | 范围压力 | "工程量无所谓，先把大架子都搭好。" |
| 3 | 权威压力 | "别管愿景/里程碑，先写实现。" |
| 4 | 沉没成本 | "都写了这么多了，别改计划，补补就行。" |
| 5 | 不确定性压力 | "愿景还没定，先写点代码探索。" |
| 6 | 交接/摩擦压力 | "这次先不提交/不推送，之后再说。" |
| 7 | 测试逃逸压力 | "E2E 太重了，手动点一遍就行。" |
| 8 | 设计变更逃逸 | "这个小改动不用写 ECN，直接改代码。" |

---

## Red Flags — STOP and Start Over

听到以下任何一句话（包括自己对自己说的），**立即停止，回到分析/计划/红测**：

**跳过计划类：**
- "愿景先放一边，先把功能做了再说"
- "计划写不写都一样，反正我知道要做什么"

**跳过测试类：**
- "先写实现更快，测试后补也一样"
- "我已经手动测过了"
- "这次不一样，TDD 太慢"
- "先把架子搭完再补红测"
- "E2E 太重了，单元测试够了"
- "手动点一遍没问题就行"

**跳过纪律类：**
- "反正工程量不是问题，先铺开"
- "先不提交/不推送，之后再说"
- "DoD 先写个大概，后面再补硬"
- "只要跑通/能 instantiate 就算 done"

**跳过变更管理类：**
- "这个小改动不用写 ECN"
- "PRD 先不更新，代码里改了就行"
- "口头说一下就好，不用留文档"

---

## Rationalization Table（Close the Loops）

| 常见自我说服 | 反制语句（强制执行） |
|---|---|
| "先写实现更快，测试后补" | 先写红测；否则没有目标函数，只有随机游走。 |
| "我已经手动测过了" | 手动不是回归；必须把成功标准固化成自动化测试。 |
| "这次不一样，TDD 太慢" | 一旦说"这次不一样"，说明风险更高，更要 TDD。 |
| "先把架子搭完再补红测" | 这是沉没成本陷阱；先把一条可验收路径做通（红→绿），再扩展。 |
| "工程量无所谓，先铺开" | 铺开会放大返工；先按验收驱动推进，并持续维护追溯矩阵。 |
| "提交/推送太麻烦" | 这是交接风险：**每个工程计划完成都必须 commit+push**，否则不算交付。 |
| "E2E 太重了，不值得" | 没有 E2E 就没有用户视角的验收；单元测试全绿但用户流程跑不通 = 没完成。 |
| "这个改动太小，不用写 ECN" | 小改动不留痕 = 大返工的种子；ECN 可以只写 3 行，但必须存在。 |
| "边界条件太多，测不完" | 用边界条件检查清单逐条过，至少覆盖空值/极值/权限/并发。 |

---

## Anti-Patterns

| Anti-Pattern | 为什么有害 | 正确做法 |
|---|---|---|
| 写"宏大目标"但没有可执行步骤/命令/预期输出 | 无法验证完成度 | 每条目标必须绑定验证命令 |
| 把测试当成验收报告（测试后于实现） | 测试沦为橡皮图章 | 测试必须先于实现（红→绿） |
| 用"看起来没问题"替代验证命令 | 不可重复、不可回归 | 必须有自动化验证 |
| 完成工程计划但不提交/不推送 | 状态不可追溯 | 每个 slice 必须 commit+push |
| DoD 写得过软 | 无法判定完成 | 过 DoD 硬度自检 Gate |
| 只写 happy path 测试 | 边界/异常场景爆雷 | 三类必写：正常/异常/边界 |
| 只有单元测试没有 E2E | 零件都对但整车不跑 | 每个里程碑至少 1 个 E2E |
| 施工中发现设计问题但不写 ECN | 设计与实现脱节，后续无法追溯 | 走 ECN 流程 |
| PRD 需求编号随意或缺失 | 追溯链断裂 | 严格遵守 `PRD-NNNN` / `REQ-NNNN-NNN` 编号规则 |

---

## 自动检查（推荐在 Review 前跑一次）

用法示例（在仓库根目录执行）：

```bash
python3 /path/to/skills/tashan-development-loop/scripts/doc_hygiene_check.py --root .
```

检查内容：

| 检查项 | 说明 |
|--------|------|
| 模糊表达扫描 | 扫描 Markdown 中的"看起来/差不多/尽量/优化一下"等模糊词 |
| Req ID 追溯 | PRD 的 `REQ-NNNN-NNN` 是否在 `docs/plan/` 中被引用 |
| Plan 追溯 | plan 文档是否包含 PRD Trace（或明确写明基础设施/偿债） |
| ECN 同步 | ECN 是否已同步到 PRD 和 vN 计划 |
| 编号连续性 | PRD-NNNN / ECN-NNNN / REQ-NNNN-NNN 编号是否连续、无跳号 |
| 断链检查 | Markdown 内部链接是否指向存在的文件/锚点 |

> **注意**：此脚本需要用户根据项目实际情况实现。上表为推荐检查项的接口规范，具体实现可参考 `references/doc-hygiene-check-spec.md`。

---

## 附录：完整目录结构示例

```
project-root/
├── docs/
│   ├── prd/
│   │   ├── VISION.md                          # 愿景文档（可选，也可写在 PRD 顶部）
│   │   ├── PRD-0001-user-auth.md              # 第 1 份 PRD
│   │   ├── PRD-0002-payment-flow.md           # 第 2 份 PRD
│   │   └── ...
│   ├── ecn/
│   │   ├── ECN-0001-auth-token-expiry.md      # 第 1 份变更通知单
│   │   ├── ECN-0002-password-policy-update.md  # 第 2 份变更通知单
│   │   └── ...
│   └── plan/
│       ├── v1-index.md                        # v1 总论与索引
│       ├── v1-auth-backend.md                 # v1 计划：认证后端
│       ├── v1-auth-frontend.md                # v1 计划：认证前端
│       ├── v2-index.md                        # v2 总论与索引
│       ├── v2-payment-integration.md          # v2 计划：支付集成
│       └── ...
├── tests/
│   ├── unit/                                  # 单元测试
│   │   ├── test_auth_service.py
│   │   └── ...
│   ├── integration/                           # 集成测试
│   │   ├── test_auth_api.py
│   │   └── ...
│   └── e2e/                                   # 端到端测试
│       ├── test_user_registration_flow.py
│       ├── test_login_flow.py
│       ├── test_payment_checkout_flow.py
│       └── conftest.py
└── src/                                       # 源代码
    └── ...
```

---

## 附录：追溯矩阵示例

| Req ID | PRD | vN Plan | 单元/集成测试 | E2E 测试 | 证据 | 状态 |
|--------|-----|---------|--------------|----------|------|------|
| REQ-0001-001 | PRD-0001 §2.1 | v1-auth-backend §Step1 | `test_auth_service.py::test_create_user_*` | `test_user_registration_flow.py` | CI log #42 | ✅ done |
| REQ-0001-002 | PRD-0001 §2.2 | v1-auth-backend §Step3 | `test_auth_service.py::test_login_*` | `test_login_flow.py` | CI log #43 | ✅ done |
| REQ-0001-003 | PRD-0001 §2.3 | v1-auth-frontend §Step1 | `test_auth_api.py::test_token_*` | `test_login_flow.py` | — | 🔴 blocked |
| REQ-0001-004 | PRD-0001 §2.4 [已由 ECN-0001 变更] | v1-auth-backend §Step5 | `test_auth_service.py::test_token_expiry_*` | — | — | 🟡 in progress |

> 任何一行出现"—"（断链），都必须补齐后才能宣称该需求已交付。

---

## 附录：版本变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v2.0 | 2026-02-09 | 重大重构：新增 ECN 变更通知单机制；新增 E2E 测试 Gate；新增测试用例编写规范（三类必写 + 边界条件检查清单）；PRD/ECN 统一编号规则；新增计划变更处理规则；新增适用范围说明；新增塔山命名由来；合并去重 Red Flags；结构重组与目录导航 |
| v1.0 | — | 初始版本 |