# Deep Research Markdown 约定（供生成 PPTX）

本 skill 的脚本 `scripts/md-deepresearch-to-pptx.js` 假设输入 Markdown 大体遵循下面结构（允许缺失部分小节，但标题最好一致）：

1. `# <标题>`
2. `生成日期：YYYY-MM-DD`（可选）
3. `## Executive Summary`（一段或多段正文）
4. `## Key Findings`（若干 `- ` 项；支持形如 `**加粗标题**：正文` 的写法）
5. `## Detailed Analysis`
   - 多个 `### <小节标题>`（建议 3–6 个）
   - 小节正文可包含 `- ` 列表（会被转成 PPT 的 bullets）
6. `## Areas of Consensus`（`- ` 列表）
7. `## Areas of Debate`（`- ` 列表）
8. `## Sources`
   - `[\d] 标题. https://...`（脚本会抓取编号、标题、URL）
9. `## Gaps and Further Research`（`- ` 列表）

不满足上述结构时：先把你的 Markdown “整理/重排”成这个结构再生成，成功率最高、版式最稳定。

