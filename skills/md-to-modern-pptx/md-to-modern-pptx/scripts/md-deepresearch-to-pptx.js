#!/usr/bin/env node
/*
  Deep Research Markdown -> Modern PPTX

  Usage:
    node scripts/md-deepresearch-to-pptx.js --in input.md --out output.pptx --theme golden-hour

  Notes:
  - Expects a "Deep Research" markdown structure (see references/deepresearch-md-contract.md).
  - Reads theme from theme-factory: ~/.agents/skills/theme-factory/themes/<theme>.md
  - Uses pptxgenjs from the surrounding project node_modules.
*/

const fs = require("fs");
const path = require("path");

let pptxgen;
try {
  // eslint-disable-next-line import/no-extraneous-dependencies, global-require
  pptxgen = require("pptxgenjs");
} catch {
  console.error(
    "缺少依赖：pptxgenjs。\n请在当前目录执行：npm i pptxgenjs\n然后重试。",
  );
  process.exit(1);
}

const SLIDE_W = 10;
const SLIDE_H = 5.625;
const MARGIN = 0.65;

function argValue(argv, name) {
  const idx = argv.indexOf(name);
  if (idx < 0) return null;
  return argv[idx + 1] || null;
}

function argFlag(argv, name) {
  return argv.includes(name);
}

function hex6NoHash(hex) {
  return String(hex).replace("#", "").toUpperCase();
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function hexToRgb(hex) {
  const h = hex6NoHash(hex);
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

function rgbToHex({ r, g, b }) {
  const to2 = (n) =>
    clamp(Math.round(n), 0, 255).toString(16).padStart(2, "0");
  return `${to2(r)}${to2(g)}${to2(b)}`.toUpperCase();
}

function mix(hexA, hexB, t) {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return rgbToHex({
    r: a.r + (b.r - a.r) * t,
    g: a.g + (b.g - a.g) * t,
    b: a.b + (b.b - a.b) * t,
  });
}

function stripMd(text) {
  return String(text).replaceAll("**", "").replaceAll("`", "").trim();
}

function normalizeParagraphs(raw) {
  return raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith("生成日期："))
    .join("\n");
}

function splitIntroAndBullets(text) {
  const lines = String(text)
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const firstBullet = lines.findIndex((l) => l.startsWith("- "));
  if (firstBullet < 0) return { intro: lines.join("\n"), bullets: [] };

  const intro = lines.slice(0, firstBullet).join("\n").trim();
  const bullets = lines
    .slice(firstBullet)
    .filter((l) => l.startsWith("- "))
    .map((l) => l.slice(2).trim());
  return { intro, bullets };
}

function sectionBetween(md, startHeading, endHeadingOrNull) {
  const startIdx = md.indexOf(startHeading);
  if (startIdx < 0) return "";
  const after = md.slice(startIdx + startHeading.length);
  if (!endHeadingOrNull) return after.trim();
  const endIdx = after.indexOf(endHeadingOrNull);
  if (endIdx < 0) return after.trim();
  return after.slice(0, endIdx).trim();
}

function parseBullets(raw) {
  const out = [];
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) out.push(trimmed.slice(2).trim());
  }
  return out;
}

function splitBoldPrefix(bullet) {
  const m = bullet.match(/^\*\*([^*]+)\*\*[：:]\s*(.+)$/);
  if (!m) return { title: null, body: bullet };
  return { title: stripMd(m[1]), body: stripMd(m[2]) };
}

function parseDetailedAnalysis(raw) {
  const blocks = raw
    .split(/\r?\n###\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const out = [];
  for (const block of blocks) {
    const lines = block.split(/\r?\n/);
    const titleLine = stripMd(lines[0].trim());
    const body = stripMd(normalizeParagraphs(lines.slice(1).join("\n")));
    out.push({ title: titleLine, body });
  }
  return out;
}

function parseSources(raw) {
  const sources = [];
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    const m = trimmed.match(
      /^\[(\d+)\]\s+(.+?)\.\s+(https?:\/\/\S+)\s*$/,
    );
    if (m) sources.push({ id: m[1], title: stripMd(m[2]), url: stripMd(m[3]) });
  }
  return sources;
}

function parseTheme(themeMarkdownPath) {
  if (!fs.existsSync(themeMarkdownPath)) return null;
  const raw = fs.readFileSync(themeMarkdownPath, "utf8");

  const colors = [];
  for (const line of raw.split(/\r?\n/)) {
    const m = line.match(/-\s+\*\*([^*]+)\*\*:\s+`(#[0-9a-fA-F]{6})`/);
    if (m) colors.push({ name: m[1].trim(), hex: hex6NoHash(m[2]) });
  }

  const headerFont =
    (raw.match(/-\s+\*\*Headers\*\*:\s+(.+)\s*$/m) || [])[1]?.trim() || null;
  const bodyFont =
    (raw.match(/-\s+\*\*Body Text\*\*:\s+(.+)\s*$/m) || [])[1]?.trim() || null;

  return {
    name: (raw.match(/^#\s+(.+)\s*$/m) || [])[1]?.trim() || "Theme",
    colors,
    fonts: { headerFont, bodyFont },
  };
}

function pickWindowsFontPair(themeFonts) {
  // theme-factory fonts are cross-platform names (often not installed on Win).
  // Use sensible Windows defaults.
  const headerFallback = "Segoe UI Semibold";
  const bodyFallback = "Segoe UI";
  void themeFonts;
  return { header: headerFallback, body: bodyFallback };
}

function pickPalette(theme) {
  const fallback = {
    themeName: "Fallback",
    accent1: "F4A900",
    accent2: "C1666B",
    bg: mix("D4B896", "FFFFFF", 0.68),
    card: mix("FFFFFF", "D4B896", 0.12),
    text: "4A403A",
    dark: mix("4A403A", "000000", 0.30),
    bgText: mix("FFFFFF", "D4B896", 0.08),
  };
  if (!theme || theme.colors.length < 2) return fallback;

  const getByName = (re) =>
    theme.colors.find((c) => re.test(c.name.toLowerCase()))?.hex || null;

  const accent1 =
    getByName(/electric|mustard|teal|blue|gold|accent|primary/) ||
    theme.colors[0].hex;
  const accent2 =
    getByName(/cyan|terracotta|seafoam|rose|secondary|highlight/) ||
    theme.colors[1].hex;
  const bgBase =
    getByName(/white|cream|beige|light|background/) ||
    mix(theme.colors[0].hex, "FFFFFF", 0.85);
  const textBase =
    getByName(/dark|charcoal|chocolate|navy|text/) ||
    mix(theme.colors[0].hex, "000000", 0.65);

  const bg = mix(bgBase, "FFFFFF", 0.25);
  const card = mix("FFFFFF", bgBase, 0.10);
  const text = textBase;
  const dark = mix(textBase, "000000", 0.28);
  const bgText = mix("FFFFFF", bgBase, 0.06);

  return {
    themeName: theme.name,
    accent1,
    accent2,
    bg,
    card,
    text,
    dark,
    bgText,
  };
}

function makeShadow() {
  return {
    type: "outer",
    color: "000000",
    blur: 8,
    offset: 3,
    angle: 135,
    opacity: 0.14,
  };
}

function addBeanMotif(slide, pres, colors) {
  const dots = [
    { x: SLIDE_W - 1.55, y: 0.45, c: colors.accent2 },
    { x: SLIDE_W - 1.15, y: 0.40, c: colors.accent1 },
    { x: SLIDE_W - 0.78, y: 0.50, c: colors.accent2 },
    { x: SLIDE_W - 1.30, y: 0.68, c: colors.accent1 },
    { x: SLIDE_W - 0.92, y: 0.72, c: colors.accent2 },
  ];
  for (const d of dots) {
    slide.addShape(pres.shapes.OVAL, {
      x: d.x,
      y: d.y,
      w: 0.22,
      h: 0.14,
      fill: { color: d.c },
      line: { color: d.c },
      rotate: 18,
    });
  }
}

function addChrome(slide, pres, colors, opts) {
  const isDark = Boolean(opts?.dark);
  const bg = isDark ? colors.dark : colors.bg;

  slide.background = { color: bg };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0,
    y: 0,
    w: 0.18,
    h: SLIDE_H,
    fill: { color: isDark ? colors.accent1 : colors.accent2 },
    line: { color: isDark ? colors.accent1 : colors.accent2 },
  });

  addBeanMotif(slide, pres, colors);

  if (!opts?.hideFooter) {
    slide.addText(opts?.footerLeft || "", {
      x: 0.35,
      y: SLIDE_H - 0.42,
      w: 6.5,
      h: 0.3,
      fontFace: opts?.fontBody,
      fontSize: 10,
      color: isDark ? mix(colors.bg, "FFFFFF", 0.35) : mix(colors.text, "FFFFFF", 0.25),
      margin: 0,
    });

    slide.addText(String(opts?.pageNumber ?? ""), {
      x: SLIDE_W - 0.95,
      y: SLIDE_H - 0.45,
      w: 0.6,
      h: 0.3,
      fontFace: opts?.fontBody,
      fontSize: 10,
      align: "right",
      color: isDark ? mix(colors.bg, "FFFFFF", 0.30) : mix(colors.text, "FFFFFF", 0.25),
      margin: 0,
    });
  }
}

function addTitle(slide, colors, fonts, title, subtitle) {
  slide.addText(title, {
    x: 0.55,
    y: 1.5,
    w: SLIDE_W - 1.2,
    h: 1.4,
    fontFace: fonts.header,
    fontSize: 46,
    color: colors.bgText,
    bold: true,
    margin: 0,
  });

  slide.addShape("rect", {
    x: 0.55,
    y: 3.25,
    w: 6.7,
    h: 0.55,
    fill: { color: colors.accent2, transparency: 12 },
    line: { color: colors.accent2, transparency: 100 },
  });

  slide.addText(subtitle, {
    x: 0.75,
    y: 3.33,
    w: 6.3,
    h: 0.4,
    fontFace: fonts.body,
    fontSize: 16,
    color: colors.bgText,
    margin: 0,
  });
}

function addH1(slide, colors, fonts, h1, h2) {
  slide.addText(h1, {
    x: 0.55,
    y: 0.62,
    w: SLIDE_W - 1.2,
    h: 0.6,
    fontFace: fonts.header,
    fontSize: 34,
    color: colors.text,
    bold: true,
    margin: 0,
  });

  if (h2) {
    slide.addText(h2, {
      x: 0.55,
      y: 1.2,
      w: SLIDE_W - 1.2,
      h: 0.4,
      fontFace: fonts.body,
      fontSize: 14,
      color: mix(colors.text, "FFFFFF", 0.35),
      margin: 0,
    });
  }
}

function addCard(slide, pres, colors, rect, opts) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rect.x,
    y: rect.y,
    w: rect.w,
    h: rect.h,
    fill: { color: opts?.fill ?? colors.card },
    line: { color: opts?.line ?? mix(colors.text, "FFFFFF", 0.80), width: 0.7 },
    shadow: opts?.shadow ? makeShadow() : undefined,
  });
}

function addBullets(slide, fonts, colors, bullets, rect) {
  const runs = [];
  for (let i = 0; i < bullets.length; i++) {
    runs.push({
      text: bullets[i],
      options: { bullet: true, breakLine: i !== bullets.length - 1 },
    });
  }
  slide.addText(runs, {
    x: rect.x,
    y: rect.y,
    w: rect.w,
    h: rect.h,
    fontFace: fonts.body,
    fontSize: 16,
    color: colors.text,
    margin: 0,
    paraSpaceAfter: 6,
  });
}

function findSlideImage(imagesDir, slideNumber) {
  if (!imagesDir) return null;
  const candidates = [
    path.join(imagesDir, `slide-${String(slideNumber).padStart(2, "0")}.png`),
    path.join(imagesDir, `slide-${String(slideNumber).padStart(2, "0")}.jpg`),
    path.join(imagesDir, `slide-${String(slideNumber).padStart(2, "0")}.jpeg`),
    path.join(imagesDir, `slide-${String(slideNumber).padStart(2, "0")}.webp`),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return null;
}

function addRightPanel(slide, pres, palette, fonts, opts) {
  const x = 6.85;
  const y = 1.8;
  const w = 2.5;
  const h = 3.25;

  addCard(
    slide,
    pres,
    palette,
    { x, y, w, h },
    { shadow: true, fill: mix(palette.card, palette.accent2, 0.05) },
  );

  if (opts?.imagePath) {
    slide.addText("Illustration", {
      x: x + 0.2,
      y: y + 0.22,
      w: w - 0.4,
      h: 0.3,
      fontFace: fonts.header,
      fontSize: 12,
      bold: true,
      color: palette.text,
      margin: 0,
    });

    slide.addImage({
      path: opts.imagePath,
      x: x + 0.18,
      y: y + 0.58,
      w: w - 0.36,
      h: h - 0.95,
      sizing: { type: "cover", w: w - 0.36, h: h - 0.95 },
    });

    if (opts?.caption) {
      slide.addText(opts.caption, {
        x: x + 0.2,
        y: y + h - 0.34,
        w: w - 0.4,
        h: 0.28,
        fontFace: fonts.body,
        fontSize: 10,
        color: mix(palette.text, "FFFFFF", 0.30),
        margin: 0,
      });
    }
    return;
  }

  slide.addText(opts?.title || "要点", {
    x: x + 0.2,
    y: y + 0.22,
    w: w - 0.4,
    h: 0.4,
    fontFace: fonts.header,
    fontSize: 16,
    bold: true,
    color: palette.text,
    margin: 0,
  });

  const mini = (opts?.bullets || []).slice(0, 3);
  let yy = y + 0.75;
  for (let k = 0; k < mini.length; k++) {
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2,
      y: yy + 0.05,
      w: 0.16,
      h: 0.16,
      fill: { color: k % 2 === 0 ? palette.accent1 : palette.accent2 },
      line: { color: k % 2 === 0 ? palette.accent1 : palette.accent2 },
    });
    slide.addText(stripMd(mini[k]), {
      x: x + 0.42,
      y: yy,
      w: w - 0.62,
      h: 0.3,
      fontFace: fonts.body,
      fontSize: 13,
      color: mix(palette.text, "FFFFFF", 0.15),
      margin: 0,
    });
    yy += 0.48;
  }
}

async function buildDeck(mdPath, outPath, themeSlug, opts = {}) {
  const md = fs.readFileSync(mdPath, "utf8");
  const title =
    (md.match(/^#\s+(.+)$/m) || [])[1]?.trim() || "Deep Research";
  const date =
    (md.match(/^生成日期：\s*([0-9-]+)\s*$/m) || [])[1]?.trim() || "";

  const themePath = path.join(
    process.env.USERPROFILE || "",
    ".agents",
    "skills",
    "theme-factory",
    "themes",
    `${themeSlug}.md`,
  );
  const theme = parseTheme(themePath);
  const fonts = pickWindowsFontPair(theme?.fonts);
  const palette = pickPalette(theme);

  const executiveSummary = stripMd(
    normalizeParagraphs(
      sectionBetween(md, "## Executive Summary", "## Key Findings"),
    ),
  );
  const keyFindingsRaw = sectionBetween(
    md,
    "## Key Findings",
    "## Detailed Analysis",
  );
  const keyFindings = parseBullets(keyFindingsRaw).map(splitBoldPrefix);
  const detailedRaw = sectionBetween(
    md,
    "## Detailed Analysis",
    "## Areas of Consensus",
  );
  const analyses = parseDetailedAnalysis(detailedRaw);
  const consensusRaw = sectionBetween(
    md,
    "## Areas of Consensus",
    "## Areas of Debate",
  );
  const debateRaw = sectionBetween(md, "## Areas of Debate", "## Sources");
  const consensus = parseBullets(consensusRaw).map(stripMd);
  const debate = parseBullets(debateRaw).map(stripMd);
  const sourcesRaw = sectionBetween(
    md,
    "## Sources",
    "## Gaps and Further Research",
  );
  const sources = parseSources(sourcesRaw);
  const gapsRaw = sectionBetween(md, "## Gaps and Further Research", null);
  const gaps = parseBullets(gapsRaw).map(stripMd);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Codex (md-to-modern-pptx)";
  pres.title = title;
  pres.subject = "Deep Research deck";
  pres.theme = { headFontFace: fonts.header, bodyFontFace: fonts.body, lang: "zh-CN" };

  let page = 1;
  const footerLeft = `${stripMd(title)}${date ? ` • ${date}` : ""}`.trim();
  const imagesDir = opts?.imagesDir || null;

  // Slide 1: Title
  {
    const slide = pres.addSlide();
    addChrome(slide, pres, palette, { dark: true, hideFooter: true, fontBody: fonts.body });
    addTitle(
      slide,
      palette,
      fonts,
      stripMd(title).replace(/（Deep Research）/g, ""),
      `生成日期：${date || "—"}  ·  主题：Markdown → Modern PPTX`,
    );
  }

  // Slide 2: Executive Summary (2-col)
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, "Executive Summary", "一句话：把核心结论放在第一页内容页。");

    addCard(slide, pres, palette, { x: MARGIN, y: 1.75, w: 6.3, h: 3.2 }, { shadow: true });
    slide.addText(executiveSummary || "（未提供 Executive Summary）", {
      x: MARGIN + 0.35,
      y: 1.95,
      w: 5.6,
      h: 2.8,
      fontFace: fonts.body,
      fontSize: 16,
      color: palette.text,
      margin: 0,
      lineSpacingMultiple: 1.1,
    });

    addCard(
      slide,
      pres,
      palette,
      { x: 7.2, y: 1.75, w: 2.15, h: 3.2 },
      { shadow: true, fill: mix(palette.card, palette.accent1, 0.06) },
    );
    slide.addText("Theme", {
      x: 7.42,
      y: 1.95,
      w: 1.75,
      h: 0.35,
      fontFace: fonts.header,
      fontSize: 16,
      color: palette.text,
      bold: true,
      margin: 0,
    });

    const tags = [
      { t: theme?.name || themeSlug, c: palette.accent1 },
      { t: "一致配色", c: palette.accent2 },
      { t: "可复用脚本", c: palette.accent1 },
      { t: "可验证输出", c: palette.accent2 },
    ];
    let y = 2.38;
    for (const tag of tags) {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.42,
        y,
        w: 1.75,
        h: 0.42,
        fill: { color: mix(tag.c, "FFFFFF", 0.45) },
        line: { color: mix(tag.c, "FFFFFF", 0.10), width: 1 },
      });
      slide.addText(tag.t, {
        x: 7.42,
        y: y + 0.08,
        w: 1.75,
        h: 0.3,
        fontFace: fonts.body,
        fontSize: 12,
        align: "center",
        color: palette.text,
        margin: 0,
      });
      y += 0.55;
    }
  }

  // Slide 3: Key Findings (up to 4 cards)
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, "Key Findings", "把最重要的 3–5 点拆成卡片。");

    const grid = [
      { x: MARGIN, y: 1.75 },
      { x: 5.35, y: 1.75 },
      { x: MARGIN, y: 3.55 },
      { x: 5.35, y: 3.55 },
    ];

    const items = keyFindings.length > 0 ? keyFindings : [{ title: "（缺失）", body: "在 Key Findings 下用 - 列表写结论点。" }];
    for (let i = 0; i < Math.min(4, items.length); i++) {
      const item = items[i];
      const pos = grid[i];
      addCard(slide, pres, palette, { x: pos.x, y: pos.y, w: 4.0, h: 1.55 }, { shadow: true });

      slide.addShape(pres.shapes.OVAL, {
        x: pos.x + 0.25,
        y: pos.y + 0.28,
        w: 0.55,
        h: 0.55,
        fill: { color: i % 2 === 0 ? palette.accent1 : palette.accent2 },
        line: { color: i % 2 === 0 ? palette.accent1 : palette.accent2 },
      });
      slide.addText(String(i + 1), {
        x: pos.x + 0.25,
        y: pos.y + 0.34,
        w: 0.55,
        h: 0.45,
        fontFace: fonts.header,
        fontSize: 18,
        color: palette.bgText,
        align: "center",
        margin: 0,
      });

      slide.addText(item.title || `发现 ${i + 1}`, {
        x: pos.x + 0.92,
        y: pos.y + 0.25,
        w: 2.95,
        h: 0.4,
        fontFace: fonts.header,
        fontSize: 17,
        bold: true,
        color: palette.text,
        margin: 0,
      });
      slide.addText(item.body || "", {
        x: pos.x + 0.92,
        y: pos.y + 0.68,
        w: 2.95,
        h: 0.95,
        fontFace: fonts.body,
        fontSize: 13,
        color: mix(palette.text, "FFFFFF", 0.20),
        margin: 0,
      });
    }
  }

  // Slide 4: Section divider
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body, dark: true });

    slide.addText("Detailed Analysis", {
      x: 0.55,
      y: 2.05,
      w: SLIDE_W - 1.2,
      h: 0.8,
      fontFace: fonts.header,
      fontSize: 42,
      bold: true,
      color: palette.bgText,
      margin: 0,
    });
    slide.addText("每个小节 1 页：左侧正文，右侧要点。", {
      x: 0.55,
      y: 2.95,
      w: 8.5,
      h: 0.5,
      fontFace: fonts.body,
      fontSize: 16,
      color: mix(palette.bgText, "000000", 0.05),
      margin: 0,
    });
  }

  // Slides: analysis points (up to 5)
  for (let i = 0; i < Math.min(5, analyses.length); i++) {
    const a = analyses[i];
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, a.title || `分析 ${i + 1}`, "");

    addCard(slide, pres, palette, { x: MARGIN, y: 1.8, w: 6.0, h: 3.25 }, { shadow: true });
    const { intro, bullets } = splitIntroAndBullets(a.body || "");
    slide.addText(intro || "（本小节无正文）", {
      x: MARGIN + 0.35,
      y: 2.02,
      w: 5.3,
      h: bullets.length === 0 ? 2.85 : 1.1,
      fontFace: fonts.body,
      fontSize: 15,
      color: palette.text,
      margin: 0,
      lineSpacingMultiple: 1.12,
    });
    if (bullets.length > 0) {
      addBullets(slide, fonts, palette, bullets.map(stripMd).slice(0, 6), {
        x: MARGIN + 0.45,
        y: 3.06,
        w: 5.1,
        h: 2.0,
      });
    }

    const imagePath = imagesDir ? findSlideImage(imagesDir, page) : null;
    addRightPanel(slide, pres, palette, fonts, {
      title: "要点",
      bullets: bullets.length > 0 ? bullets.slice(0, 3) : [stripMd(a.title)],
      imagePath,
      caption: imagePath ? "AI-generated (Gemini)" : null,
    });
  }

  // Consensus
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, "Areas of Consensus", "");

    addCard(slide, pres, palette, { x: MARGIN, y: 1.75, w: SLIDE_W - 1.35, h: 3.4 }, { shadow: true });
    addBullets(slide, fonts, palette, (consensus.length ? consensus : ["（缺失）"]).slice(0, 8), {
      x: MARGIN + 0.45,
      y: 2.05,
      w: SLIDE_W - 2.2,
      h: 2.85,
    });
  }

  // Debate
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, "Areas of Debate", "");

    addCard(slide, pres, palette, { x: MARGIN, y: 1.75, w: SLIDE_W - 1.35, h: 3.4 }, { shadow: true });
    addBullets(slide, fonts, palette, (debate.length ? debate : ["（缺失）"]).slice(0, 8), {
      x: MARGIN + 0.45,
      y: 2.05,
      w: SLIDE_W - 2.2,
      h: 2.85,
    });
  }

  // Sources
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body });
    addH1(slide, palette, fonts, "Sources", "（按引用编号）");

    const y0 = 1.7;
    const rowH = 0.62;
    addCard(slide, pres, palette, { x: MARGIN, y: 1.55, w: SLIDE_W - 1.35, h: 3.65 }, { shadow: true });

    const list = sources.length ? sources : [{ id: "1", title: "（缺失）", url: "" }];
    for (let i = 0; i < Math.min(6, list.length); i++) {
      const s = list[i];
      const y = y0 + i * rowH;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: MARGIN + 0.35,
        y: y + 0.04,
        w: 0.42,
        h: 0.42,
        fill: { color: i % 2 === 0 ? palette.accent1 : palette.accent2 },
        line: { color: i % 2 === 0 ? palette.accent1 : palette.accent2 },
      });
      slide.addText(String(s.id), {
        x: MARGIN + 0.35,
        y: y + 0.12,
        w: 0.42,
        h: 0.3,
        fontFace: fonts.header,
        fontSize: 12,
        color: palette.bgText,
        align: "center",
        margin: 0,
      });
      slide.addText(stripMd(s.title), {
        x: MARGIN + 0.85,
        y: y,
        w: 7.9,
        h: 0.28,
        fontFace: fonts.body,
        fontSize: 12,
        color: palette.text,
        margin: 0,
      });
      slide.addText(stripMd(s.url), {
        x: MARGIN + 0.85,
        y: y + 0.27,
        w: 7.9,
        h: 0.25,
        fontFace: fonts.body,
        fontSize: 10,
        color: mix(palette.text, "FFFFFF", 0.35),
        margin: 0,
      });
    }
  }

  // Gaps (dark)
  {
    const slide = pres.addSlide();
    page += 1;
    addChrome(slide, pres, palette, { pageNumber: page, footerLeft, fontBody: fonts.body, dark: true });
    slide.addText("Gaps & Next Steps", {
      x: 0.55,
      y: 0.8,
      w: SLIDE_W - 1.2,
      h: 0.7,
      fontFace: fonts.header,
      fontSize: 38,
      bold: true,
      color: palette.bgText,
      margin: 0,
    });

    addCard(
      slide,
      pres,
      palette,
      { x: MARGIN, y: 1.7, w: SLIDE_W - 1.35, h: 3.35 },
      {
        shadow: true,
        fill: mix(palette.dark, "FFFFFF", 0.06),
        line: mix(palette.bgText, "000000", 0.55),
      },
    );
    slide.addText("把研究推进到更“硬”的材料：", {
      x: MARGIN + 0.45,
      y: 1.95,
      w: SLIDE_W - 2.2,
      h: 0.35,
      fontFace: fonts.header,
      fontSize: 16,
      bold: true,
      color: palette.bgText,
      margin: 0,
    });

    const steps =
      gaps.length > 0
        ? gaps
        : ["补齐一手档案/政策材料。", "把口味/广告/供应链时间线做成可核对的年表。"];
    const runs = [];
    for (let i = 0; i < steps.length; i++) {
      runs.push({
        text: stripMd(steps[i]),
        options: { bullet: { type: "number" }, breakLine: i !== steps.length - 1 },
      });
    }
    slide.addText(runs, {
      x: MARGIN + 0.45,
      y: 2.35,
      w: SLIDE_W - 2.2,
      h: 2.3,
      fontFace: fonts.body,
      fontSize: 16,
      color: mix(palette.bgText, "000000", 0.02),
      margin: 0,
      paraSpaceAfter: 10,
    });

    slide.addText(`（主题：${palette.themeName} / 来自 theme-factory）`, {
      x: 0.55,
      y: SLIDE_H - 0.55,
      w: SLIDE_W - 1.2,
      h: 0.3,
      fontFace: fonts.body,
      fontSize: 10,
      color: mix(palette.bgText, "000000", 0.12),
      margin: 0,
    });
  }

  await pres.writeFile({ fileName: outPath });
}

async function main() {
  const argv = process.argv.slice(2);
  const inPath = argValue(argv, "--in");
  const outPath = argValue(argv, "--out");
  const themeSlug = argValue(argv, "--theme") || "golden-hour";
  const imagesDirArg = argValue(argv, "--images-dir");
  const imagesDir = imagesDirArg ? path.resolve(process.cwd(), imagesDirArg) : null;
  const noImages = argFlag(argv, "--no-images");

  if (!inPath || !outPath) {
    console.error(
      "用法：node md-deepresearch-to-pptx.js --in input.md --out output.pptx [--theme golden-hour] [--images-dir images/] [--no-images]",
    );
    process.exit(2);
  }

  const absIn = path.resolve(process.cwd(), inPath);
  const absOut = path.resolve(process.cwd(), outPath);

  if (!fs.existsSync(absIn)) {
    console.error(`找不到输入文件：${absIn}`);
    process.exit(1);
  }

  await buildDeck(absIn, absOut, themeSlug, { imagesDir: noImages ? null : imagesDir });
  console.log(`已生成：${absOut}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
