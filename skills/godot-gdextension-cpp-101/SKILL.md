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

这个 skill 自带了两个可复用脚本（在本 skill 目录下）：

- 生成最小骨架（创建 `native/` + `src/` + `SConstruct` + `.gdextension` + 一个可 `ping()` 的类）：
  - `python scripts/init_gdextension_skeleton.py --project-root <godot-project> --plugin-name <plugin> --ext-name <ext>`
- Windows 构建闭环（dump `extension_api.json` + 可选生成绑定 + scons 编译）：
  - `pwsh -NoProfile -File scripts/build_gdextension_windows.ps1 -NativeDir <path-to-native> -GodotExe <path-to-godot-console.exe>`

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
- “在 PowerShell 里随手用 `&&` 串命令”

## 附：ConPTY / Pipe 这类异步子系统的经验（可选，但很值）

当你的扩展封装的是异步子系统（比如 Windows ConPTY / conhost.exe）时：

- 不要假设“API 调用返回”就意味着资源已被异步进程 duplicate/接管完成。
- Handle/FD 生命周期要保守：需要时延迟关闭，把关闭集中到 `close()` 做。
- 先判断子进程是否存活，再判断管道是否有数据；否则会在错误方向上浪费很多时间。
