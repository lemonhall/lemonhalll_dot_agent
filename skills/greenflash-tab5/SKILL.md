---
name: greenflash-tab5
description: Use when flashing M5Stack Tab5 (ESP32-P4) firmware from Windows PowerShell and the device is put into download mode ("绿闪了"), and you want an automated build+flash+boot+monitor log capture loop.
---

# greenflash-tab5（“绿闪了”一键刷机 + 自动抓日志）

## Overview
把“你说绿闪了 → 我 build/flash → 自动让板子跑起来 → 自动 monitor 抓日志并在崩溃时停下”固化成稳定流程，尽量减少手工 `idf.py monitor` 和手动按 Reset 抓日志。

## When to Use
- 用户说“绿闪了”（Tab5 已进入下载模式，绿灯快速闪烁），希望立刻刷固件并抓日志。
- 开发过程中频繁复现崩溃/重启，需要自动保存日志并按关键字/`rst:` 计数停止。
- 用户明确要求：Windows 11 + PowerShell；不要用 WSL2。

## Safety
- **默认不得执行** `erase_flash`。
- 刷机前只需用户确认“绿闪了”；如需擦除必须再次明确确认。
- 任何会修改用户全局 ESP-IDF 安装目录的操作必须先说明并征得同意。

## Core Workflow（推荐）
在仓库根目录执行（默认串口 `COM6`）：
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\greenflash.ps1 -Port COM6 -CaptureSec 600 -IsolationRstOnly:$false
```

输出：
- 日志自动保存到 `tools/logs/tab5-COM6-YYYYMMDD-HHMMSS.log`
- 命中崩溃关键字（`Guru Meditation`/`assert failed`/`task_wdt` 等）或 `rst:` 计数条件后自动停止

## 关键知识点：刷完后自动“软启动”（避免手动短按 Reset）
有些情况下刷完固件后设备仍停留在 DOWNLOAD 模式，monitor 会提示：
`Device is in DOWNLOAD mode. Short-press Reset once to boot the app.`

为减少手工操作，`tools/greenflash.ps1` 在写完 flash 后会 **best-effort** 追加执行：
```powershell
python -m esptool --chip esp32p4 -p COM6 -b 460800 --before no_reset --after hard_reset run
```

说明：
- `esptool run` 会请求芯片退出下载模式并直接运行 flash 中的 app。
- 若该命令在某些机器/驱动/板子上无效，则仍需要用户**短按一次 Reset**（脚本会提示）。

## 常见坑
- `--before no_reset` 写 flash 可能 `Write timeout`：脚本会自动回退重试 `--before default_reset`。
- 仅靠 toast 显示中文可能出现方块：优先以日志窗口/IRC 输出为准。

