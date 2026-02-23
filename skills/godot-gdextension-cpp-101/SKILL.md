---
name: godot-gdextension-cpp-101
description: Use when a Godot 4.x project needs a C++ GDExtension (godot-cpp) added or fixed, especially when dealing with SCons builds, MSVC/clang toolchains, extension_api.json + bindings generation, .gdextension library mapping, enabling the extension in Project Settings, or load/runtime errors like dynamic library not found, missing entry_symbol, or ABI/version mismatches.
---

# Godot 4.x：用 C++ GDExtension 引入 Native 模块（101）

目标：让“完全不懂”的 agent 也能在 Godot 4.x 项目里，把一个 C++ GDExtension **从 0 搭起来 → 能编译 → 能被 Godot 加载 → 能在 GDScript 里调用**，并在遇到常见报错时能按步骤排查。

## 你现在应该做哪条路径？

- **路径 A（推荐）**：项目里已经有脚本/模板（例如 `scripts/build_*gdextension*.ps1` 这种），先用脚本跑通闭环，再按本 skill 的 checklist 补齐缺项。
- **路径 B（通用）**：项目里啥都没有，就按下面的“最小骨架 → 绑定生成 → 编译 → 加载验证”一步步建。

## 最小交付（DoD）

以下三条同时满足，才算“引入成功”：

1) Godot 启动无 “dynamic library not found / symbol not found”。
2) GDScript 能 `var x := <NativeClass>.new()` 并调用 1 个方法返回正确值。
3) 在目标平台上（至少 Windows x86_64 或你实际要跑的平台）能 **可重复** 构建产物（不靠手工点点改路径）。

## Quick Checklist（先扫一遍再动手）

- 你用的是 **Godot 4.x**（不是 3.x；不要写 GDNative）。
- 你用的是 **godot-cpp**（与 Godot 版本匹配），且能从 `extension_api.json` 生成绑定。
- `.gdextension` 的 `entry_symbol`、`compatibility_minimum`、`libraries.<platform>` 指向的路径都真实存在（`res://...`）。
- 明确“交付策略”：发布给普通用户的插件通常需要一起交付预编译二进制；仅开发/CI 可选择不提交二进制。
- Windows 上编译必须在正确的工具链环境里（MSVC 的 `cl/link` 在 PATH 或通过 VsDevCmd 注入）。

## Bundled Scripts（可选，但强烈推荐）

本 skill 自带脚本可直接复用（生成骨架 / Windows 构建闭环）。正式说明与示例命令见文末 **Scripts** 章节。

## 与仓库规约对齐（别抓瞎）

在一个具体仓库里动手前，先找该仓库的 `AGENTS.md`（通常会写清楚）：

- **Godot console exe 的路径/约定**：很多仓库会用环境变量 `GODOT_WIN_EXE` 保存本机 Godot 路径（示例：`E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe`），并强调用 console 版跑 headless 测试更稳定。
- **Headless 测试怎么跑**：不少仓库会提供包装脚本（例如 `scripts/run_godot_tests.ps1`）统一处理 `--headless`、超时、`user://` 重定向等细节。

如果仓库里已经有“跑测试脚本/约定”，优先用它，不要让 agent 自己手拼一长串 Godot 参数。

## Repo Layout（推荐结构）

把 Native 工程放在插件内部，便于分发与 `res://` 引用：

```
addons/<plugin_name>/
  native/
    src/
      register_types.cpp
      register_types.h
      my_ext.cpp
      my_ext.h
    thirdparty/
      godot-cpp/   # submodule 或本机 junction/clone
    build/
      godot_api/
        extension_api.json   # Godot --dump-extension-api 生成
    SConstruct
    <ext>.gdextension
  bin/
    win64/
      <ext>.windows.template_debug.x86_64.dll
```

## Samples（建议作为插件交付的一等公民）

当你交付的是 `addons/<plugin>/` 级别的插件时，**samples 往往比 README 更能让用户“验收成功”**：打开场景 → 点运行 → 看到效果。

推荐把 samples 放在：`addons/<plugin>/samples/`（插件自包含，用户拷贝一个目录就能用）。

### 目录结构（推荐）

```
addons/<plugin>/
  samples/
    scenes/
      sample_smoke.tscn
      sample_interactive.tscn
    scripts/
      sample_smoke.gd
      sample_interactive.gd
    assets/   # 可选：字体/贴图/主题等（尽量小）
```

### 人类可验收的 samples：实战技巧

- **一个样例只证明一件事**：`sample_smoke` 只验证“能加载 + 能 new + 能调 1 个方法”；交互/渲染/PTY 放到 `sample_interactive`。
- **失败要可读**：如果扩展未启用/加载失败，场景里用 `Label` 明确提示（同时 `push_error` 打日志），不要静默黑屏。
- **兼容“未启用扩展”**：用 `ClassDB.class_exists("<NativeClass>")` 探测；通过 `ClassDB.instantiate` 创建实例，避免脚本在类不存在时直接报错。
- **零外部依赖**：样例尽量不依赖项目根目录的 autoload/输入映射/主题；需要资源就放在 `addons/<plugin>/samples/assets/`。
- **给出可验证预期**：在屏幕上显示 2~3 条“预期结果”（例如：已加载/输出字符串/退出码），用户不用读代码也能判断成功。
- **为导出做准备**：若插件也要支持导出运行，建议提供 `template_release` 对应的库映射，并准备一个“导出后也能跑”的样例场景。

### 最小 `sample_smoke` 脚本模式（可复用）

在样例脚本里用“软依赖”验证：

- `class_exists` 失败：提示用户去 `Project Settings` → `GDExtension` 启用 `.gdextension`
- `instantiate` 失败：提示是 ABI/版本/库映射问题
- 调用最小方法：尽早暴露绑定不匹配

## 工作流（通用版，按顺序执行）

### 1) 选工具链与构建方式

- **推荐**：SCons（因为 godot-cpp 原生就是 SCons 流程）。
- Windows：MSVC（Visual Studio Build Tools 2019/2022）。
- Linux/macOS：clang/gcc（按平台常规配置即可）。

如果你在 PowerShell 里要连续执行多条命令，用 `;`，不要用 `&&`。

### 2) 准备 godot-cpp（必须）

两种方式二选一：

- **submodule（推荐，最可复现）**
  - 把 `godot-cpp` 放进 `native/thirdparty/godot-cpp/`
  - 之后在 CI/新机器上也能一键拉起来
- **本机复用（省事，但可复现性差）**
  - 用 junction/symlink 指向你磁盘上已有的 `godot-cpp` checkout

关键验证点：`native/thirdparty/godot-cpp/SConstruct` 必须存在。

### 3) 生成 `extension_api.json`（必须）

从 Godot 自己导出 API 描述文件：

- 找到你的 Godot 可执行文件（推荐 console 版）
- 在 `native/build/godot_api/` 目录下运行：

```powershell
<godot_console.exe> --dump-extension-api
```

产物必须落在 `native/build/godot_api/extension_api.json`（或你约定的路径），否则后续绑定生成没法做。

### 4) 生成/刷新 godot-cpp 绑定（必须）

第一次构建或 Godot 升级后，需要生成（或重生成）绑定。

SCons 常用参数（概念上）：

- `generate_bindings=yes`：生成绑定（第一次很慢）
- `custom_api_file="<path/to/extension_api.json>"`：指定 API 文件

注意：**Godot 升级后**，即使项目能编译，也可能因为 API 变化导致运行期崩溃/符号缺失；这时要强制 regen 绑定。

### 5) 写 `SConstruct`（或复用项目脚本）

要点（不要求你背模板，但必须满足这些约束）：

- 编译你的 `src/*.cpp`
- 引入 `godot-cpp` 的 include 与链接
- 输出到一个稳定的 `bin/<platform>/` 路径
- Debug/Release（或 template_debug/template_release）分别输出不同文件名

如果项目已有脚本封装（例如用 PowerShell + VsDevCmd 调用 SCons），优先用脚本，避免 agent 手写一堆易错命令。

### 6) 写 `<ext>.gdextension`（必须）

这是 Godot 加载 native 库的“清单文件”。

最低必需字段：

- `entry_symbol`：你导出的 init 函数名（C++ 侧要匹配）
- `compatibility_minimum`：例如 `4.6.0`
- `[libraries]`：按平台/架构/target 填路径（`res://...`）

示例（Windows x86_64，兼容不同 key 风格时可以“多写几行”）：

```ini
[configuration]
entry_symbol = "myext_library_init"
compatibility_minimum = "4.6.0"

[libraries]
windows.x86_64 = "res://addons/<plugin_name>/bin/win64/myext.windows.template_debug.x86_64.dll"
windows.editor.x86_64 = "res://addons/<plugin_name>/bin/win64/myext.windows.template_debug.x86_64.dll"
windows.template_debug.x86_64 = "res://addons/<plugin_name>/bin/win64/myext.windows.template_debug.x86_64.dll"
windows.template_release.x86_64 = "res://addons/<plugin_name>/bin/win64/myext.windows.template_release.x86_64.dll"
```

### 6.5) 在项目中启用该扩展（必须）

不要默认“放了 `.gdextension` 文件就会自动加载”。以 Godot 编辑器为准：

- Godot 编辑器：`Project Settings` → `GDExtension` → 把你的 `res://.../<ext>.gdextension` 加入列表

如果你必须自动化（例如 CI / 无界面环境），把等价配置写进 `project.godot`（字段名以你当前 Godot 版本生成的实际内容为准；不要瞎猜键名）。

### 7) 在 GDScript 侧验证加载（必须）

最短闭环建议：

1) 启动一个最小场景/脚本。
2) **先做存在性探测**（避免扩展未启用时脚本加载失败）：
   - `if not ClassDB.class_exists("<NativeClass>"): push_error("GDExtension not enabled")`
3) 推荐实例化方式：
   - `var x := ClassDB.instantiate("<NativeClass>")`
   - 只有当你确认扩展一定启用时，再写 `var x := <NativeClass>.new()`
3) 调一个不会崩的函数（例如 `x.ping()` 返回字符串/整数）。

“能 new 出来”不代表 ABI 对了；至少再调用 1 个方法，才能更早发现绑定错位。

## Smoke Test（Headless，必须会跑）

目标：在**不打开窗口**的情况下验证两件事：

1) 扩展确实被启用并成功加载（`ClassDB.class_exists`）
2) 关键 API 可调用（至少调用 1 个方法）

最小 smoke 测试脚本（放到仓库里某个固定位置，例如 `tests/native_smoke/test_gdextension_smoke.gd`）：

```gdscript
extends SceneTree

func _init() -> void:
	var class_name := "MyExtension" # 改成你的 native 类名
	if not ClassDB.class_exists(class_name):
		push_error("GDExtension not enabled or failed to load: " + class_name)
		quit(2)
		return

	var obj = ClassDB.instantiate(class_name)
	if obj == null:
		push_error("Failed to instantiate: " + class_name)
		quit(3)
		return

	# 调一个最简单的方法，尽早发现绑定/ABI 问题
	if obj.has_method("ping"):
		var r = obj.call("ping")
		print("ping() => ", r)

	quit(0)
```

PowerShell 直接运行（不依赖仓库脚本时的兜底命令）：

```powershell
$godot = $env:GODOT_WIN_EXE  # 或者填绝对路径（建议 console 版）
& $godot --headless --path E:\path\to\project --script E:\path\to\project\tests\native_smoke\test_gdextension_smoke.gd
echo $LASTEXITCODE
```

如果仓库提供了测试运行器脚本（例如 `scripts/run_godot_tests.ps1`），用它来跑 smoke 测试通常更稳定（超时/环境隔离都已处理）。

## Windows（PowerShell + MSVC + SCons）推荐闭环（可复制）

这一段是“通用可复用”的最佳实践，其他项目也可以照抄结构与约束：

1) 探测 MSVC（确保 `cl/link` 可用）
2) 用 Godot dump `extension_api.json`
3) 用 SCons 编译（必要时 `generate_bindings=yes`）

如果项目里已有类似脚本（可当作模板参考）：

- `scripts/probe_msvc.ps1`：通过 VsDevCmd 探测工具链
- `scripts/setup_godot_cpp.ps1`：准备 `native/thirdparty/godot-cpp`
- `scripts/build_conpty_gdextension.ps1`：dump api + 生成绑定 + 编译（支持 `-RegenBindings`）

增量编译要点：
- SCons 默认就是增量；不要频繁清理 `build/`（会导致全量重编 + 更慢的绑定生成）。
- Godot 升级后需要重生成绑定（常见症状：能编译但运行崩 / 缺符号 / 行为异常）。

## 常见错误与排查（按优先级）

### “dynamic library not found”

按这个顺序查：

1) `.gdextension` 里的 `res://...` 路径是否真实存在（文件名/目录/大小写）。
2) key 是否匹配当前平台（例如 Windows 需要 `windows.*`）。
3) 你是不是只编了 debug，但运行在 release（或相反）。
4) DLL 依赖缺失（Windows：缺 MSVC runtime / 依赖 DLL 没在 PATH）。

### “symbol not found / entry symbol missing”

1) `.gdextension` 的 `entry_symbol` 与 C++ 导出函数名不一致。
2) C++ 编译时没导出符号（例如缺少 `extern "C"` 或导出宏）。
3) 链接到了旧 DLL（路径指向错误，或 Godot 缓存/复制了旧文件）。

### Godot 能启动，但 `new()` 崩溃 / 调用崩溃

1) `godot-cpp` 绑定与 Godot 版本不匹配（最常见）。
2) `extension_api.json` 是旧的（Godot 升级后未重新 dump）。
3) 只更新了 Godot 没 `-RegenBindings`（或等价操作）。

## 安全与仓库卫生（必须遵守）

### 选择：二进制（DLL/.so/.dylib）到底要不要进仓库？

不要“一刀切”。按交付目标选策略：

- **发布给普通用户安装/直接用的 Godot 插件（推荐）**：把目标平台的稳定二进制一起交付
  - 优先：直接提交到仓库的 `addons/<plugin>/bin/<platform>/...`（用户 clone/下载就能用）
  - 同时建议：放到 GitHub Releases（每个版本的附件），作为“版本化产物/镜像”，便于回滚与下载
  - 关键点：若插件需要在编辑器里用，通常要提供 `template_debug`；若还要导出后运行，还要提供 `template_release`
  - 仓库配置：确保 `.gitignore` 没把这些最终产物忽略；二进制体积较大时可考虑 Git LFS

- **仅开发者/CI 自己用的扩展**：可以不提交二进制，只提交可重复构建脚本（首次使用需要本地编译）。

无论选哪种，都必须做到：
- `.gdextension` 的路径始终有效（`res://...` 能找到文件）。
- 构建方式可重复（脚本化，能在新机器上跑通）。

### 其他仓库卫生

- 不要自动执行批量删除（清理 `build/` / `bin/`）——需要用户确认。
- 不要把本机绝对路径写死进仓库（例如 `E:\...`），改用脚本参数或环境变量。

## Red Flags（看到就停）

- “先把 C++ 写完再补 .gdextension/绑定/测试”
- “Godot 升级了但不想 regen bindings，应该也能跑”
- “只提交 DLL、不提交源码/构建脚本”
  - 结果：维护者无法复现构建；升级 Godot/工具链时只能靠猜
- “提交了 DLL，但 `.gdextension` 映射没对上（路径/target/架构）”
  - 结果：用户侧依然报 `dynamic library not found`
- “samples 放在仓库顶层或散落各处，发布插件时漏带”
  - 结果：用户没法一键验收，反馈成本变高
- “在 PowerShell 里随手用 `&&` 串命令”

## 附：ConPTY / Pipe 这类异步子系统的经验（可选，但很值）

当你的扩展封装的是异步子系统（比如 Windows ConPTY / conhost.exe）时：

- 不要假设“API 调用返回”就意味着资源已被异步进程 duplicate/接管完成。
- Handle/FD 生命周期要保守：需要时延迟关闭，把关闭集中到 `close()` 做。
- 先判断子进程是否存活，再判断管道是否有数据；否则会在错误方向上浪费很多时间。

## Scripts（本 Skill 自带，可直接复用）

位置：`scripts/`（在本 skill 目录内）。

### 1) `scripts/init_gdextension_skeleton.py`：生成最小骨架

用途：一次性创建最小可编译/可加载的 GDExtension 工程骨架（`native/` + `src/` + `SConstruct` + `.gdextension` + 一个 `ping()` 类）。

示例：

```powershell
$SkillDir = Join-Path $env:USERPROFILE ".agents\\skills\\godot-gdextension-cpp-101"
python (Join-Path $SkillDir "scripts\\init_gdextension_skeleton.py") `
  --project-root E:\development\YourGodotProject `
  --plugin-name your_plugin `
  --ext-name myext
```

安全：默认**不覆盖**已有文件；若要覆盖需显式传 `--force`。

### 2) `scripts/build_gdextension_windows.ps1`：Windows 构建闭环

用途：在 Windows 上完成：

1) 用 Godot 生成 `extension_api.json`（`--dump-extension-api`）
2) 必要时触发 godot-cpp 绑定生成（首次 / `-RegenBindings`）
3) 进入 MSVC 环境并运行 SCons 构建（`template_debug` / `template_release`）

示例（只编 debug）：

```powershell
$SkillDir = Join-Path $env:USERPROFILE ".agents\\skills\\godot-gdextension-cpp-101"
pwsh -NoProfile -File (Join-Path $SkillDir "scripts\\build_gdextension_windows.ps1") `
  -NativeDir E:\development\YourGodotProject\addons\your_plugin\native `
  -GodotExe "E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe"
```

示例（debug + release，且强制重生成绑定）：

```powershell
$SkillDir = Join-Path $env:USERPROFILE ".agents\\skills\\godot-gdextension-cpp-101"
pwsh -NoProfile -File (Join-Path $SkillDir "scripts\\build_gdextension_windows.ps1") `
  -NativeDir E:\development\YourGodotProject\addons\your_plugin\native `
  -GodotExe "E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe" `
  -All `
  -RegenBindings
```

前置条件：
- `scons` 可用（`python -m pip install --user -U scons`）
- MSVC Build Tools 已安装（脚本会尝试用 `vswhere` 找到 `VsDevCmd.bat`）
- `native/thirdparty/godot-cpp/SConstruct` 存在（submodule 或 junction 均可）

建议配套（让命令更短、更少出错）：

```powershell
# 建议提前设置一次，后续脚本/测试都能复用
$env:GODOT_WIN_EXE="E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe"
```

### 3) `scripts/run_godot_tests.ps1`：Headless 测试运行器模板（参考）

用途：提供一个通用的 Windows/PowerShell 版 headless 测试运行器模板，解决常见痛点：

- 自动加 `--headless` 与 `--rendering-driver dummy`
- 可跑单个测试（`-One`）或按目录跑 suite（`-Suite` / `-SuiteDir`）
- 通过 `APPDATA/LOCALAPPDATA/USERPROFILE` 重定向，把 Godot 的 `user://` 隔离到项目内 `./.godot-user/`，避免污染真实用户目录
- 支持超时（`-TimeoutSec` / `GODOT_TEST_TIMEOUT_SEC`）

用法（从 skill 里直接运行）：

```powershell
$SkillDir = Join-Path $env:USERPROFILE ".agents\\skills\\godot-gdextension-cpp-101"
pwsh -NoProfile -File (Join-Path $SkillDir "scripts\\run_godot_tests.ps1") `
  -ProjectRoot E:\development\YourGodotProject `
  -Suite all
```

建议：把它复制到你的仓库 `scripts/run_godot_tests.ps1` 后再按项目 suite 结构微调（这样团队/CI 用起来最顺手）。
