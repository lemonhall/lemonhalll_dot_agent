---
name: md-to-modern-pptx
description: Convert Markdown (.md) into a polished, modern .pptx slide deck using a theme palette (theme-factory) plus deterministic PPTX generation (PptxGenJS) and QA (markitdown). Use when the user asks to “把 Markdown 变成精美 PPT/PPTX/幻灯片/Deck”, “根据这份研究报告生成演示稿”, or when a Deep-Research style markdown (Executive Summary / Key Findings / Detailed Analysis / Sources) should become a presentation with consistent visual design, footers, and verification steps.
---

# Md → Modern PPTX

## 快速开始（推荐）

目标：用 **theme-factory 选主题** + 用 **PptxGenJS 稳定生成 PPTX**，再用 **markitdown 做内容 QA**（可选再做视觉 QA）。

### 1) 选主题（theme-factory）

- 主题预览：打开 `~/.agents/skills/theme-factory/theme-showcase.pdf`
- 主题 slug（对应 `~/.agents/skills/theme-factory/themes/*.md`）：
  - `ocean-depths`
  - `sunset-boulevard`
  - `forest-canopy`
  - `modern-minimalist`
  - `golden-hour`（本次示例用的）
  - `arctic-frost`
  - `desert-rose`
  - `tech-innovation`
  - `botanical-garden`
  - `midnight-galaxy`

### 2) 安装依赖（一次即可）

在要生成 PPTX 的项目目录运行：

```powershell
npm i pptxgenjs
python -m pip install "markitdown[pptx]"
```

### 3) 生成 PPTX

用本 skill 自带脚本（面向“Deep Research 风格 Markdown”）：

```powershell
node .\skills\md-to-modern-pptx\scripts\md-deepresearch-to-pptx.js --in .\YOUR.md --out .\YOUR.pptx --theme golden-hour
```

如果你的 Markdown 不符合 Deep Research 结构：先把它整理成下述结构（见 `references/deepresearch-md-contract.md`），再生成。

## Gemini 配图（可选，但能显著变“高级”）

你说的思路是可行的：用 `gemini-3-pro-image-preview` 这类“文生图”模型为**部分页面**生成插画，再在生成 PPTX 时把图片贴进去。

### 配图策略（默认推荐）

- **只给 Detailed Analysis 页配图**：每个小节 1 张（最多 5 张），性价比最高。
- Title/Executive Summary/Key Findings/Consensus/Debate/Sources：默认不配图（避免噪声、避免风格漂移）。

### 配图提示词统筹（Prompt Bank）

一张图的提示词由 4 部分组成（建议保持一致，避免每页风格乱跳）：

1) **语义**：本页小节标题 + 关键语境（1–2 句）  
2) **视觉风格**：modern editorial illustration / flat vector / subtle grain / clean shapes  
3) **主题约束**：沿用 deck 主题色倾向（例如 `golden-hour` 是 warm mustard + terracotta + beige）  
4) **硬约束**：`no text, no logos, no watermarks, no brand marks`

本 skill 的脚本会按上述原则自动生成 plan（你也可以手改）。

### 1) 准备 `.env`（敏感信息别提交）

推荐两种放置方式（二选一）：

- **全局（推荐）**：`~/.agents/skills/md-to-modern-pptx/.env`（一次配置，所有项目可复用；脚本也会兼容某些“嵌套安装”路径）
- **项目级**：`<项目根目录>/.env`（只对当前项目生效；脚本也会自动读）

`.env` 内容参考 `skills/md-to-modern-pptx/.env.example`：

```dotenv
CHERRY_BASE_URL=https://your-gateway.example.com
CHERRY_API_KEY=your_key_here
CHERRY_MODEL=gemini-3-pro-image-preview
```

说明：
- 这里按“中转站/网关”的 **base_url + key** 方式设计；脚本会优先读 `CHERRY_*`，并兼容旧的 `GEMINI_*` 命名。
- 对 `gemini-3-pro-image-preview` 这类 Gemini 生图模型：脚本默认走 `POST /v1beta/models/<model>:generateContent`（`responseModalities=["IMAGE"]`）。
- 若你的网关不支持 Gemini 原生路径，则会回退到 OpenAI-like 的 `POST /v1/images/generations`（部分中转站使用 task_id 轮询）。

### 2) 生成配图计划（plan.json）

```powershell
python .\skills\md-to-modern-pptx\scripts\gemini_image_pack.py make-plan --in .\YOUR.md --theme golden-hour --out .\images.plan.json
```

这会默认给分析页（从第 5 页开始）生成最多 5 张图的提示词。

### 3) 调用 Gemini 生成图片

```powershell
python .\skills\md-to-modern-pptx\scripts\gemini_image_pack.py generate --plan .\images.plan.json --out-dir .\images
```

如果报错里出现类似：
- “无可用渠道（distributor）” / `model_not_found`
- “not supported model for image generation”

通常意味着：你的中转站账号/分组没有开通该模型的 **IMAGE 输出能力**，需要在中转站侧开通/切换分组/换可用模型。

输出命名默认是：`images/slide-05.png`, `images/slide-06.png` …（与 deck 页码对齐）。

### 4) 重新生成 PPTX，并自动贴图

```powershell
node .\skills\md-to-modern-pptx\scripts\md-deepresearch-to-pptx.js --in .\YOUR.md --out .\YOUR.pptx --theme golden-hour --images-dir .\images
```

（如果临时不想贴图：加 `--no-images`。）

## QA（必做）

### 内容 QA（markitdown）

```powershell
python -m markitdown .\YOUR.pptx
python -m markitdown .\YOUR.pptx | Select-String -Pattern "xxxx|lorem|ipsum|this.*(page|slide).*layout" -CaseSensitive:$false
```

重点看：
- 是否漏了段落/顺序错了
- 是否残留 Markdown 标记（`**`/反引号）
- 是否有占位符文本

### 视觉 QA（可选，但强烈推荐）

如果你本机有 LibreOffice（`soffice`）与 Poppler（`pdftoppm`），可以用 `pptx` skill 的 `thumbnail.py` 生成缩略图网格，快速发现溢出/遮挡/边距过小等问题：

```powershell
python "$HOME\.agents\skills\pptx\scripts\thumbnail.py" .\YOUR.pptx deck-thumbs --cols 4
```

## 常见坑（别踩）

- PptxGenJS 颜色不要带 `#`，也不要用 8 位 hex 夹带透明度（会损坏文件）
- 列表用 `bullet: true`，别直接写 “•”
- 不要复用同一个 options 对象（PptxGenJS 会原地 mutate）

更完整的 PPTX 工程化注意事项，直接看 `pptx` skill 的 `pptxgenjs.md`。
