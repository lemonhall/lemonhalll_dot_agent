import argparse
import re
from pathlib import Path


def pascal_case(name: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", name.strip())
    parts = [p for p in parts if p]
    if not parts:
        return "MyExtension"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def write_text(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file (pass --force): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Initialize a minimal Godot 4.x C++ GDExtension skeleton (SCons + godot-cpp)."
    )
    ap.add_argument("--project-root", required=True, help="Godot project root (contains project.godot).")
    ap.add_argument("--plugin-name", required=True, help="addons/<plugin-name>/ (e.g. jediterm).")
    ap.add_argument("--ext-name", required=True, help="Extension short name (used in filenames/symbols).")
    ap.add_argument("--godot-min", default="4.6.0", help="compatibility_minimum in .gdextension (default: 4.6.0).")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files if present.")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    if not (project_root / "project.godot").exists():
        raise SystemExit(f"project.godot not found under: {project_root}")

    plugin_name = args.plugin_name.strip().strip("/\\")
    ext_name = args.ext_name.strip()
    if not re.fullmatch(r"[A-Za-z0-9_\\-]+", ext_name):
        raise SystemExit("--ext-name should be simple (letters/digits/_/-).")

    class_name = pascal_case(ext_name)
    entry_symbol = f"{ext_name}_library_init"

    addons_dir = project_root / "addons" / plugin_name
    native_dir = addons_dir / "native"
    src_dir = native_dir / "src"
    bin_win64_dir = addons_dir / "bin" / "win64"

    # Files
    sconstruct_path = native_dir / "SConstruct"
    gdextension_path = native_dir / f"{ext_name}.gdextension"
    ext_h_path = src_dir / f"{ext_name}.h"
    ext_cpp_path = src_dir / f"{ext_name}.cpp"
    reg_h_path = src_dir / "register_types.h"
    reg_cpp_path = src_dir / "register_types.cpp"

    write_text(
        sconstruct_path,
        f"""#!/usr/bin/env python

import os

env = SConscript("thirdparty/godot-cpp/SConstruct")
env["ENV"] = os.environ

VariantDir("build", "src", duplicate=0)
env["OBJPREFIX"] = os.path.join("build", "")

sources = Glob("src/*.cpp")

library = env.SharedLibrary(
\t"../bin/win64/{ext_name}{{}}{{}}".format(env["suffix"], env["SHLIBSUFFIX"]),
\tsource=sources,
)

Default(library)
""",
        force=args.force,
    )

    write_text(
        gdextension_path,
        f"""[configuration]

entry_symbol = "{entry_symbol}"
compatibility_minimum = "{args.godot_min}"

[libraries]

# Keep multiple keys to be resilient across Godot 4.x key variants.
windows.x86_64 = "res://addons/{plugin_name}/bin/win64/{ext_name}.windows.template_debug.x86_64.dll"
windows.editor.x86_64 = "res://addons/{plugin_name}/bin/win64/{ext_name}.windows.template_debug.x86_64.dll"
windows.template_debug.x86_64 = "res://addons/{plugin_name}/bin/win64/{ext_name}.windows.template_debug.x86_64.dll"
windows.template_release.x86_64 = "res://addons/{plugin_name}/bin/win64/{ext_name}.windows.template_release.x86_64.dll"
""",
        force=args.force,
    )

    write_text(
        ext_h_path,
        f"""#pragma once

#include <godot_cpp/classes/ref_counted.hpp>

namespace godot {{

class {class_name} : public RefCounted {{
\tGDCLASS({class_name}, RefCounted)

protected:
\tstatic void _bind_methods();

public:
\t{class_name}() = default;
\t~{class_name}() = default;

\tString ping() const;
}};

}} // namespace godot
""",
        force=args.force,
    )

    write_text(
        ext_cpp_path,
        f"""#include "{ext_name}.h"

#include <godot_cpp/core/class_db.hpp>

namespace godot {{

void {class_name}::_bind_methods() {{
\tClassDB::bind_method(D_METHOD("ping"), &{class_name}::ping);
}}

String {class_name}::ping() const {{
\treturn "pong";
}}

}} // namespace godot
""",
        force=args.force,
    )

    write_text(
        reg_h_path,
        """#pragma once

#include <godot_cpp/core/class_db.hpp>

void initialize_extension(godot::ModuleInitializationLevel p_level);
void uninitialize_extension(godot::ModuleInitializationLevel p_level);
""",
        force=args.force,
    )

    write_text(
        reg_cpp_path,
        f"""#include "register_types.h"

#include <gdextension_interface.h>
#include <godot_cpp/godot.hpp>

#include "{ext_name}.h"

using namespace godot;

void initialize_extension(ModuleInitializationLevel p_level) {{
\tif (p_level != MODULE_INITIALIZATION_LEVEL_SCENE) {{
\t\treturn;
\t}}
\tClassDB::register_class<{class_name}>();
}}

void uninitialize_extension(ModuleInitializationLevel p_level) {{
\tif (p_level != MODULE_INITIALIZATION_LEVEL_SCENE) {{
\t\treturn;
\t}}
}}

extern "C" {{

GDExtensionBool GDE_EXPORT {entry_symbol}(GDExtensionInterfaceGetProcAddress p_get_proc_address,
\t\tconst GDExtensionClassLibraryPtr p_library, GDExtensionInitialization *r_initialization) {{
\tGDExtensionBinding::InitObject init_obj(p_get_proc_address, p_library, r_initialization);
\tinit_obj.register_initializer(initialize_extension);
\tinit_obj.register_terminator(uninitialize_extension);
\tinit_obj.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_SCENE);
\treturn init_obj.init();
}}

}} // extern "C"
""",
        force=args.force,
    )

    (native_dir / "thirdparty").mkdir(parents=True, exist_ok=True)
    bin_win64_dir.mkdir(parents=True, exist_ok=True)

    print("[OK] GDExtension skeleton created:")
    print(f"  native: {native_dir}")
    print(f"  gdextension: {gdextension_path}")
    print("")
    print("Next steps:")
    print(f"  1) Put godot-cpp at: {native_dir / 'thirdparty' / 'godot-cpp'}")
    print("  2) Dump extension_api.json via your Godot console exe (--dump-extension-api).")
    print("  3) Build with SCons (Windows: ensure MSVC env).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
