---
name: github-daily-brief
description: Use when the user asks for a daily GitHub brief (today’s trending repos and/or repositories created today), especially when they want a scannable Chinese summary plus Markdown/HTML output files.
---

# GitHub Daily Brief

生成「GitHub 今日简报」：抓取 **Trending（Today）** 与 **今日新建仓库（created:YYYY-MM-DD）**，为每个项目写约 80–120 字中文简介（含主观建议/判断），并输出 `.md`、`.html`、`.pdf` 三份文件（可选额外生成终端友好的彩色链接列表）。

- `github-brief-YYYY-MM-DD.md`
- `github-brief-YYYY-MM-DD.html`
- `github-brief-YYYY-MM-DD.pdf`（必须：用 `md-to-pdf` 技能由 Markdown 生成）

## When to Use

- 用户说“今天 GitHub 有什么新项目 / 热门项目 / 简报”
- 需要固定排版、可复制粘贴、每天重复产出
- 需要同时提供 `.md` 与 `.html` 简报

## Core Principle（别写脚本）

- 这是**信息汇总类**技能：先用 `agent-browser` 抓到结构化信息（repo、语言、stars、简介），再由 LLM 按模板**生成中文总结**并落盘。
- 不依赖自定义 `ps1`/`py` 之类的生成脚本（翻译/总结/见解必须由 LLM 产出）。

## Inputs（默认）

- 日期：默认使用用户本地日期（中国/西安，UTC+8）。也允许用户显式指定 `YYYY-MM-DD`。
- Trending 条数：默认 10。
- 今日新建仓库条数：默认 5（口径：`created:YYYY-MM-DD`，按 Stars 排序，第一页为准）。
- 输出目录：默认当前工作目录。

## Output Format (Chat)

在对话里输出时，保持这种结构（用户偏好）：

- 一句总述（包含日期）
- `GitHub Trending（Date range: Today）前 N`
  - `owner / repo（Lang）+X today / Y★`
    - 80–120 字中文简介（1 段）
- `今天新建仓库（created:YYYY-MM-DD，按 Stars 排序）前 M`
  - 同上

## Templates（落盘文件格式）

- Markdown 模板：`templates/brief.md.tmpl`
- HTML 模板：`templates/brief.html.tmpl`

生成文件名：
- `github-brief-YYYY-MM-DD.md`
- `github-brief-YYYY-MM-DD.html`
- `github-brief-YYYY-MM-DD.pdf`

## Data Collection（用 agent-browser 抓数据）

### Trending（Today）
- 打开：`https://github.com/trending?since=daily`
- 采集字段（每条）：`owner/repo`、`url`、`language`、`stars_total`、`stars_today`、`about/description`

### Created Today（按 Stars）
- 打开（示例）：`https://github.com/search?q=created%3A2026-02-11&sort=stars&order=desc&type=repositories`
- 采集字段（每条）：`owner/repo`、`url`、`language`、`stars_total`、`about/description`

## Writing Rules（中文总结硬约束）

- 每个项目输出一段**中文**总结，目标 **80–120 字**（≈100 字左右）。
- 结构建议（1 段内完成，不要分行）：
  - 这是什么（把英文 About 翻译/改写成中文，必要时做合理推断但别瞎编）
  - 适合谁/用在哪（1 个具体场景）
  - 我的看法/建议（上手关注点、风险、为何值得关注，至少 1 句）
- 如果 About 明显是占位（如 “Contribute to …”），要显式说“描述缺失”，并用页面信息（topics/语言/Stars/仓库名）做**保守推断**。

## Optional: Terminal-friendly Links（PowerShell 可 Ctrl+点击）

- 在 Windows Terminal/VS Code 终端里，**直接显示完整 URL** 通常就能 `Ctrl+点击` 打开。
- 如果用户坚持“项目名本身是蓝色可点击”，可以额外输出一段使用 **OSC 8** 的 PowerShell 打印脚本（按需生成，不作为技能固定脚本文件落盘）。

## HTML Quality（用 web-design-guidelines 自检）

- 生成 HTML 后，按 `web-design-guidelines` 技能要求抓取最新规则并对输出文件做一次审查（标题层级、对比度、焦点样式、点击区域、移动端可读性）。

## MUST: PDF 输出（用 md-to-pdf）

- 在 `.md` 与 `.html` 落盘后，**必须**调用 `md-to-pdf` 技能把 `github-brief-YYYY-MM-DD.md` 转成 `github-brief-YYYY-MM-DD.pdf`。
- 生成完成后检查输出文件存在且可打开；若失败，优先排查：路径是否含空格、Node 版本、以及代理/网络是否影响到 PDF 渲染依赖（如有）。

- 数据抓取依赖全局 `agent-browser`。
- 如果某仓库没有明确 About（出现 “Contribute to ...” 这类占位文案），简介要标注“描述缺失”，并尽量从 topics / README（如有）补全一句用途推断，避免瞎编。
- 默认输出必须是**中文**，并包含**简短的主观判断/建议**（例如：适用场景、上手关注点、潜在风险），目标是每条约 80–120 字（≈100 字左右）。
- HTML 简报需要可读、可访问（标题层级、对比度、键盘焦点样式、hover/focus 状态、可点击目标大小）。生成后可用 `web-design-guidelines` 对输出 HTML 做一次自检并修正。
