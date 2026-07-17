---
name: multilingual-tts-audio
description: 使用 Microsoft Edge 在线 TTS 将 UTF-8 文本可靠地生成本地多语言 MP3，并完成声音选择、代理、批量清单、幂等写入、媒体校验和网页接入。适用于语言课程、发音按钮、有声内容、无障碍语音、游戏对白，或需要替换不可靠的浏览器 speechSynthesis；当用户要求生成单语或十几种语言的语音、列出可用声音、制作本地音频资产时使用。
---

# Multilingual TTS Audio

使用捆绑脚本生成可离线播放的 MP3。不要把浏览器 `speechSynthesis` 当作唯一播放源；它依赖操作系统语音包，缺少目标语言时可能静默失败。

## 前置条件

- 使用 `uv` 临时提供 `edge-tts`，不污染项目虚拟环境。
- 联网失败时使用用户已配置的代理；在柠檬叔的机器上优先 `http://127.0.0.1:7897`。
- 非 ASCII 文本必须先写入 UTF-8 文件，再通过 `--text-file` 或清单传入。不要把中文、日文等文本直接放进 PowerShell 参数或 here-string。

## 工作流

1. 单条任务把文本保存为独立 UTF-8 文件；大批量任务可在 UTF-8 JSON 清单中使用内联 `text`。
2. 查询目标区域的实时声音列表，不凭记忆猜声音名。
3. 单条任务使用命令参数；多条、多语言任务使用 JSON 清单。
4. 运行合成脚本。相同文本与参数会命中指纹并跳过；内容变化时使用 `--overwrite` 明确覆盖。
5. 运行媒体契约测试或至少检查文件存在、大小大于 1 KB；有 `ffprobe` 时脚本自动验证并报告时长。
6. 网页按钮优先用 `new Audio(relativePath).play()` 或原生 `<audio>` 播放本地文件，并显示播放中/失败状态。
7. 写入中文或其他非 ASCII 文件后，按仓库规则检查 UTF-8、乱码和文本 diff。

## 快速命令

技能目录：

```powershell
$skill = "$HOME\.agents\skills\multilingual-tts-audio"
```

列出日语声音：

```powershell
uv run --with edge-tts python "$skill\scripts\synthesize.py" voices --language ja-JP --proxy http://127.0.0.1:7897
```

生成单条音频：

```powershell
uv run --with edge-tts python "$skill\scripts\synthesize.py" synthesize --text-file .\audio\source\hello.txt --output .\audio\hello.mp3 --language ja-JP --gender Female --rate=-12% --proxy http://127.0.0.1:7897
```

批量生成：

```powershell
uv run --with edge-tts python "$skill\scripts\synthesize.py" synthesize --manifest .\audio\tts-manifest.json --jobs 4 --proxy http://127.0.0.1:7897
```

超大清单应保留详细报告并允许临时失败项在批次末统一重试：

```powershell
uv run --with edge-tts python "$skill\scripts\synthesize.py" synthesize --manifest .\audio\tts-manifest.json --jobs 2 --retries 5 --continue-on-error --progress-every 100 --report .\audio\generation-report.json --proxy http://127.0.0.1:7897
```

清单字段和多语言示例见 [references/manifest.md](references/manifest.md)。使用批量模式前必须阅读该文件。

## 声音选择

- 使用 BCP 47 区域代码，如 `ja-JP`、`en-US`、`fr-FR`、`de-DE`、`es-ES`、`ko-KR`、`zh-CN`。
- 用户指定具体 `voice` 时原样使用；否则按 `language` 和可选 `gender` 查询实时列表并确定性选择。
- 同一课程保持相同声音、语速、音量和音高。
- 初学者跟读通常从 `rate=-10%` 到 `rate=-15%` 开始，不要把声音拉得过慢而破坏自然节奏。

## 安全与质量

- 不把令牌、私密文本或个人数据发送给在线 TTS，除非用户明确授权该具体内容。
- Edge TTS 是在线服务。用于商业分发前核对适用的服务条款与声音授权，不自行宣称拥有再分发权。
- 不覆盖已有且指纹不同的音频，除非用户要求更新或传入 `--overwrite`。
- 批量并发必须显式使用 `--jobs`，范围为 1 到 32；先用小清单验证，再逐步增加，遇到限流时降低并发。
- 超大清单使用 `--continue-on-error` 跑完整批次，配合 `--report` 保留逐项结果；命令仍会在存在失败项时返回非零退出码。
- 不把 `.part-*` 临时文件当作成果；只有校验通过后脚本才原子替换目标文件。
- 保留源文本或生成清单，使音频可以审计和重建。

## 完成标准

- 每个请求项都有非空 MP3 和 `.tts.json` 指纹元数据。
- 脚本退出码为 0；媒体大小与可选 `ffprobe` 校验通过。
- 消费方引用的是存在的相对路径，并有自动化契约测试覆盖缺失文件。
- 至少手动试听每种声音的一条代表样本；自动化只能证明媒体可解析，不能证明发音符合语境。
