# 元循环构建指南（模式 B）

本文件说明如何从零设计一个新的循环，并给出它依赖的方法基础和必须明确回答的开放问题。每一步都对应 [rubric.md](rubric.md) 中的一个或多个评分维度。

## 9 个步骤

1. **先命名唯一核心产物和它的 oracle。** 写一句话：“这个循环运行后，用户真的能用这个产物完成 X。” 然后确定产物类型和它的 **oracle**，也就是判断 X 是否成立的检查。两条分支：
   - **代码**：使用可执行或真值 oracle，例如测试通过、编译通过、工具返回成功；先写失败测试（TDD）。
   - **文本**：使用分解评分表，例如已有评审清单；评分标准必须在评审产物之前或独立于产物固定下来。通过评分表只是必要非充分条件，弱于可执行 oracle。

   不要因为没有可执行 oracle 就拒绝构建循环。固定评分表也是有效但更弱的 oracle。评价器-优化器的前提只是：存在清晰评价标准，而且反馈能证明会改进产物。

2. **选择 maker/checker 结构并强制独立性。** 默认采用分离的评价器-优化器，而不是让 maker 自己当 judge；单个模型常常看不见自己的错误。checker 应在新鲜/隔离上下文中运行，使用对抗式提示（“假设这里有问题，请找出来”）和预设评分表，不要继续 maker 的推理链。有真值时，使用独立生成的参考进行判断。高风险或难判断产物才升级到不同模型族或小组评审，而不是开启昂贵辩论。提前加入偏差控制：成对判断时交换顺序，不一致则降为平局；中和长度偏差；复用被追踪的 reviewer，而不是每次发明新角色。

3. **设置目标点和严重度门禁。** 完成条件是 **严重度下限**，不是“直到干净”。“直到干净”无边界，因为 reviewer 永远能再提一个小问题。把严重度词汇绑定到已有共享尺度。决定哪些级别阻塞，哪些进入非阻塞携带列表。checker 必须输出逐条发现、逐步骤严重度；每条发现都必须被处置：复现后修复 / 有证据地拒绝误报 / 无法判断则默认阻塞。禁止静默丢弃。

4. **设置迭代边界和发散/回归升级。** 设置小的硬轮次上限，默认 3 轮通常合理。最后一轮修复就是最终动作；达到上限时升级，而不是继续自动宣称成功。给每个阻塞发现一个签名：代码中可用失败测试或 lint id；文本中可用重复的评分维度。若一个签名重复出现在未解决集合中，说明卡住，应升级。若一个已经解决的签名重新出现，说明回归，也应升级。两种升级都不抹掉本轮其他修复，也不单独终止整个循环。

5. **选择触发器并使其可靠。** 把触发可靠性当成一等公民：不运行的循环毫无价值。触发应绑定到完成里程碑上的 **可检测硬动作**，例如 pre-commit 或 pre-PR hook，并迫使有意识确认。诚实说明哪些里程碑没有可 hook 的硬动作，例如纯文本“我完成了”的总结；这些只能用文字约定和跳过率审计覆盖。要监控确认动作，避免它退化成条件反射式绕过。

6. **决定记忆：运行内 vs 跨运行。** 运行内记忆包括前轮未解决签名、已尝试修复签名和收尾备忘。跨运行记忆是追加式 catch-rate 日志：记录便宜机器层漏掉了什么、用了几轮、花了多少成本，并连接到 **废弃/缩窄标准**。如果某类发现反复出现，应尽量固化为永久检查。还要明确是否需要 Reflexion 风格的跨产物学习；大多数循环不需要，应该把“不需要”写成有意识选择。

7. **设置权限上限。** 明确自治等级。默认是 **只负责质量**：循环提高草稿质量，但永不宣称完成、永不合并，总是交给人类或 CI。完成是和循环通过并列的独立门禁。循环应 fail-open（最多留下较弱草稿），不能 fail-through（把错误当作完成放行）。更高自治等级，例如自动开 PR 或自动合并，必须作为未来显式决策并附带额外控制。

8. **设置成本上限和验证节奏。** 每轮应比收尾门禁便宜：轮内只跑目标检查，例如复现失败、受影响单测、最小 lint/typecheck；完整重矩阵留到收尾。记录每轮成本，并设置明确单次预算上限或熔断器；只记录不设上限没有用。每增加一轮或一个 critic，都必须和更便宜替代方案比较。太贵的循环最终会被跳过，进而破坏触发可靠性。

9. **决定循环如何验证自己。** 规定收尾记录和跨运行日志行。第一次被这个循环评审的产物应该是循环自己的设计。明确哪些东西故意不做机器检查，例如“循环是否真的运行”常常无法可靠机器判断，就用 catch-rate 审计和人工判定替代。从第一天接入废弃标准，并承诺最小样本量和 catch-rate 下限，避免凭少数轶事决定保留或删除循环。

## 机械契约：控制骨架与输出 schema

上面 9 步负责判断；控制流和输出格式负责避免歧义。两个称职设计者读同一段 prose，也可能对“最后一轮修复是否复查”“回归是否终止循环”理解不同。因此要用标准骨架钉住机制。下面不是可运行代码，而是判断脚手架；需要填入 `BLOCKING_BAND`、`sig()` 和具体检查。

```text
# 循环体之外最容易漏掉的部分：
# trigger：可检测硬动作触发循环。若不触发，下面全是 0 分。
# cost-governor：第 1 轮前设置单次预算上限。过贵会导致跳过。
# completion-gate：循环后另有人工/CI 完成门禁。“循环通过”不等于“完成”。

loop(artifact, oracle, max_rounds = 3):
    resolved   = {}  # 已确认修复的签名；再次出现即回归
    unresolved = {}  # 尝试修复后仍出现的签名；再次出现即卡住
    attempted  = {}  # 上一轮修复、等待本轮确认的签名
    fixed_any  = false

    for round in 1..max_rounds:
        if over_budget(): break
        findings = check(artifact, fresh_ctx, adversarial, rubric)
        blocking = [f in findings if f.severity in BLOCKING_BAND]

        resolved   = resolved + (attempted - sig(blocking))
        unresolved = unresolved + (attempted - resolved)

        if blocking is empty:
            return PASS(record)

        for f in blocking:
            if sig(f) in resolved:
                escalate(REGRESSION, f)
            elif sig(f) in unresolved:
                escalate(STUCK, f)

        fixable = [f in blocking if not escalated(f)]
        if fixable is non-empty:
            fix(fixable)
            fixed_any = true
        attempted = sig(fixable)

    if fixed_any:
        confirm(last_fix_repros)
    escalate_to_human(residual)
```

这段骨架钉住两个容易歧义的点：

1. 每次修复都由下一轮完整检查确认，所以 `PASS` 必须建立在一次干净检查之上。若最后一轮修复没有下一轮，只能做该修复自身复现的目标确认，并且仍然交接；达到上限永不自动 PASS。
2. 回归和卡住一样：升级但继续，不抹掉其他修复，也不单独终止循环。

### 输出 schema

```yaml
closing_record:
  status: PASS | HALTED(escalated) | HALTED(cap) | HALTED(budget) | DEGRADED(loop-crashed → human)
  core_output: 产物现在让用户能做什么
  rounds: 运行了几轮 / 哪个条件停止
  blocking_fixed:
    - signature: ...
      severity: ...
      repro_ref: ...
      round_found: ...
      round_fixed: ...
  rejected:
    - signature: ...
      evidence: ...  # 拒绝误报必须有证据
  escalated:
    - signature: ...
      kind: STUCK | REGRESSION | CANT_TELL
      rounds_seen: ...
  cant_tell: 默认阻塞，交给人类判断
  non_blocking: 非阻塞携带列表
  residual_risk: 循环没检查或不能检查的内容
  cost:
    spent: ...
    cap: ...
    breaker_tripped: ...
  handoff: to-human | to-ci
  invariant: status = PASS ⇒ escalated == [] AND cant_tell == []

log_line:
  ts | run_id | artifact_ref | trigger(ran | skipped+reason) | status | rounds |
  blocking P0/P1/P2 | n_escalated(stuck+regression) | caught_beyond_machine |
  cost | breaker_tripped | ack_present
```

`caught_beyond_machine` 是 kill criterion 的分子：便宜机器层漏掉、循环抓到的阻塞发现。分母必须是全部运行，包括跳过，不允许只挑有利样本。若达到预先承诺样本量后 catch-rate 近似为 0，就应该缩窄或删除循环。

## 方法依据

- **TDD / 测试即规格**：Kent Beck《TDD By Example》；测试是必要非充分条件，测试充分性和 mutation testing 文献说明测试会过拟合。
- **LLM 迭代修正**：Self-Refine、Reflexion、Constitutional AI、Self-Consistency、Chain-of-Verification，以及关于单模型自我纠错局限的研究。
- **过程监督 vs 结果监督**：Lightman 等人的 “Let’s Verify Step by Step”，步骤级监督优于只看结果。
- **LLM-as-judge / 评估**：MT-Bench 关于位置、冗长、自我增强偏差；G-Eval 的分解可审计评分；panel-of-LLM-judges。
- **Agentic 模式**：Anthropic《Building Effective Agents》中的 evaluator-optimizer 模式、从环境获取 ground truth、成本和误差累积原则。
- **失败模式**：Goodhart 定律；CI 中“保持构建快速”的经验。

## 开放设计问题

1. 同模型“新鲜上下文 + 对抗提示”是否足够独立？高风险产物是否必须跨模型或小组？
2. 是否要携带 Reflexion 风格跨运行学习，还是只保留运行内记忆和组织级 catch-rate？
3. 文本产物怎样可靠检测“无进展”？代码有测试/lint 签名，文本只能用评分维度等弱签名。
4. 没有硬触发动作的里程碑如何覆盖？接受 fail-open，还是发明一个合成硬动作？
5. 自治阶梯的合理停止点在哪里？什么证据足以让循环自动开 PR 或自动合并？
6. 如何防止确认动作退化成新的绕过方式？
7. kill threshold 怎么定？需要预先承诺最小样本量和 catch-rate 下限。
