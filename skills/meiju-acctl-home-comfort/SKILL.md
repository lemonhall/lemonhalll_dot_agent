---
name: meiju-acctl-home-comfort
description: Use when the user expresses being too cold/hot or asks to adjust Midea Meiju air conditioners, and you should respond empathetically and (with confirmation) control the AC via the `meiju-acctl` CLI using `--json` output and stable exit codes.
---

# meiju-acctl Home Comfort

## Overview

把“我有点冷 / 有点热”这类自然语言，转成**可确认、可回滚、可脚本化**的空调控制动作。默认先关心用户感受与安全，再执行命令。

核心原则：

1. **先确认再下发**：除非用户明确说“就这么做/马上执行”，否则先给建议并问是否执行。
2. **永远用 `--json` 执行**：stdout 纯 JSON，便于可靠解析。
3. **不泄漏敏感信息**：不要复述账号/密码；遇到未配置，提示用户运行 `meiju-acctl config set`。

## What to Say (Human-Friendly)

当用户说“有点冷”：

- 先共情 + 关怀：问是否在家、是否要开制热、目标温度是否合适
- 给默认建议：**制热 24°C**
- 给可选项：22–26°C、是否只开卧室/客厅

当用户说“有点热”：

- 先共情 + 关怀
- 给默认建议：**制冷 26°C**
- 给可选项：24–28°C、是否只开卧室/客厅

示例话术（冷）：

> 听起来你有点冷。要不要我帮你把**卧室空调打开制热 24°C**？如果你想更暖一点也可以改成 25–26°C。回复“好/不用/改成 25 度/开客厅”我就执行。

示例话术（热）：

> 有点热的话挺难受的。要不要我把**卧室空调打开制冷 26°C**？你偏凉一点可以 25°C，偏省电一点 27°C。你希望开卧室还是客厅？

## Command Mapping

### Preconditions

1. 先检查用户配置（不泄漏明文）：
   - `meiju-acctl --json config show`
   - 如果 `configured=false`：提示用户执行 `meiju-acctl config set`（交互输入不回显密码）

2. 若用户没说房间/设备：
   - 优先问一句“卧室还是客厅？”
   - 若仍不确定：列设备让用户选：
     - `meiju-acctl --json devices list`

### Execution (only after confirmation)

冷（制热 24°C，优先卧室）：

- `meiju-acctl --json ac set --bedroom --mode heat --temp 24`

热（制冷 26°C，优先卧室）：

- `meiju-acctl --json ac set --bedroom --mode cool --temp 26`

开/关机：

- `meiju-acctl --json ac power --bedroom on`
- `meiju-acctl --json ac power --bedroom off`

如果用户提供 device_id：

- `meiju-acctl --json ac set --id 123456 --mode heat --temp 24`

### Parsing & Reliability

每次执行命令都要检查：

1. 退出码：
   - `0` 成功
   - `10` 配置缺失（提示 `meiju-acctl config set`）
   - `11/12/13/14/15` 按错误提示处理
2. JSON 字段：
   - 成功：`{"ok": true, "data": ...}`
   - 失败：`{"ok": false, "error": {"code": "...", "message": "...", "hint": "..."}}`

## Safety Rules

- 不要在用户不知情的情况下频繁调温/频繁开关机。
- 用户说“别动/不用/就这样”→ 立即停止执行，改为给建议。
- 如果用户说身体不适（发烧/心慌/呼吸不适）→ 先关怀并建议休息/就医，不要强行执行设备控制。

## Quick Recipes

- “有点冷” → 建议 `heat 24°C` → 确认 → `ac set`
- “有点热” → 建议 `cool 26°C` → 确认 → `ac set`
- “开一下卧室空调制热 25 度” → 用户已明确 → 直接执行 `ac set --bedroom --mode heat --temp 25`
- “把客厅关了” → 执行 `ac power --living-room off`

## Install Note (local)

本 skill 文件在仓库内：`skills/meiju-acctl-home-comfort/SKILL.md`。

要让 Codex 自动发现并使用它，把整个目录复制到：

- `C:\\Users\\lemon\\.agents\\skills\\meiju-acctl-home-comfort\\`

