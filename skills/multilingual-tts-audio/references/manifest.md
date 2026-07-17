# 批量清单

批量模式读取 UTF-8 JSON。所有相对路径都以清单文件所在目录为基准，不以当前 PowerShell 目录为基准。

## 结构

```json
{
  "base_dir": ".",
  "defaults": {
    "gender": "Female",
    "rate": "-12%",
    "volume": "+0%",
    "pitch": "+0Hz"
  },
  "items": [
    {
      "text_file": "source/hello-ja.txt",
      "output": "generated/hello-ja.mp3",
      "language": "ja-JP"
    },
    {
      "text_file": "source/hello-en.txt",
      "output": "generated/hello-en.mp3",
      "language": "en-US"
    },
    {
      "text": "Bonjour tout le monde.",
      "output": "generated/hello-fr.mp3",
      "voice": "fr-FR-DeniseNeural"
    }
  ]
}
```

## 字段

- `defaults`：可选；为每个项目提供默认参数。
- `base_dir`：可选；所有相对输入和输出路径的共同基目录，值本身相对于清单目录，默认 `.`。
- `items`：必填且非空；结果顺序与清单顺序一致。
- `text_file` / `text`：二选一且必须恰好提供一个。`text_file` 指向 UTF-8 文本文件；`text` 是清单中的非空内联字符串，不做 trim 或 Unicode 归一化。
- `output`：必填；目标必须以 `.mp3` 结尾。
- `voice`：具体声音名；指定后优先于 `language` 与 `gender`。
- `language`：BCP 47 区域代码；未指定 `voice` 时必填。
- `gender`：可选，值为 `Female` 或 `Male`。
- `rate`：语速百分比，如 `-12%`、`+0%`、`+10%`。
- `volume`：音量百分比，如 `+0%`。
- `pitch`：音高，如 `+0Hz`、`-5Hz`。
- 顶层 `overwrite`：可选布尔值；为 `true` 时允许替换指纹不同的已有输出。命令行 `--overwrite` 具有同样效果。
- 命令行 `--jobs`：有限并发数，范围 1 到 32，默认 1。在线服务限流时降低该值并重跑，已完成且指纹相同的项目会跳过。
- 命令行 `--continue-on-error`：遇到单项失败时继续处理其余项目，批次结束后只要有失败项仍返回非零。
- 命令行 `--progress-every N`：每完成 N 项向标准错误输出一次进度，默认 100。
- 命令行 `--report PATH`：把逐项状态写入 UTF-8 JSON 报告，标准输出只保留汇总和报告路径。

## 常用区域代码

| 语言 | 区域代码 |
|---|---|
| 中文（中国大陆） | `zh-CN` |
| 中文（台湾） | `zh-TW` |
| 日语 | `ja-JP` |
| 韩语 | `ko-KR` |
| 英语（美国） | `en-US` |
| 英语（英国） | `en-GB` |
| 法语（法国） | `fr-FR` |
| 德语 | `de-DE` |
| 西班牙语（西班牙） | `es-ES` |
| 葡萄牙语（巴西） | `pt-BR` |
| 意大利语 | `it-IT` |
| 俄语 | `ru-RU` |
| 阿拉伯语（沙特） | `ar-SA` |
| 泰语 | `th-TH` |
| 越南语 | `vi-VN` |
| 印度尼西亚语 | `id-ID` |
| 印地语 | `hi-IN` |

区域代码只用于筛选当前在线声音。生成前运行 `voices --language <区域代码>`，以实时返回为准。

## 幂等行为

每个输出旁会生成 `<文件名>.mp3.tts.json`，记录源文件路径、声音参数和内容指纹。

- 输出、元数据和指纹都匹配：跳过，状态为 `skipped`。
- 输出不存在：生成，状态为 `generated`。
- 输出存在但指纹不同或元数据丢失：默认失败；明确传入 `--overwrite` 后更新。

此设计防止不知情地覆盖人工录音，也保证同一清单可以安全重复执行。
