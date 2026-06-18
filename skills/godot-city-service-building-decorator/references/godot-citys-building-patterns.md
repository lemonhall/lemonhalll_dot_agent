# Godot Citys Building Patterns

## Core Files

Always inspect these first in `godot_citys`:

- `city_game/serviceability/buildings/generated/building_override_registry.json`
- target building directory
  - scene file
  - `building_manifest.json`
- map icon consumer when needed
  - `city_game/ui/CityMapScreen.gd`
- tests closest to the change
  - scene contract
  - manifest contract
  - service-building pin runtime/full-map tests

## Known Working Consumers

### Cafe Pattern

Use when the user wants a staffed service building with dialogue, interaction anchors, and a richer interior.

- Scene:
  - `city_game/serviceability/buildings/generated/bld_v15-building-id-1_seed424242_chunk_137_136_003/咖啡馆.tscn`
- Manifest:
  - `city_game/serviceability/buildings/generated/bld_v15-building-id-1_seed424242_chunk_137_136_003/building_manifest.json`
- Tests:
  - `tests/world/test_city_cafe_scene_contract.gd`
  - `tests/e2e/test_city_cafe_barista_dialogue_flow.gd`
  - `tests/world/test_city_service_building_full_map_pin_contract.gd`

What it teaches:

- `city_service_scene_kind`
- `city_service_scene_profile`
- `Staff/<Actor>` structure
- `CityIdleServicePedestrian.gd` usage
- interaction/dialogue metadata
- `full_map_pin` for `cafe`

### Gun Shop Pattern

Use when the user wants a storefront-only service building with a proper facade, readable interior, and full-map icon, but no NPC workflow.

- Scene:
  - `city_game/serviceability/buildings/generated/bld_v15-building-id-1_seed424242_chunk_134_130_014/枪店_A.tscn`
- Manifest:
  - `city_game/serviceability/buildings/generated/bld_v15-building-id-1_seed424242_chunk_134_130_014/building_manifest.json`
- Tests:
  - `tests/world/test_city_gun_shop_scene_contract.gd`
  - `tests/world/test_city_gun_shop_manifest_contract.gd`
  - `tests/world/test_city_service_building_map_pin_runtime.gd`

What it teaches:

- storefront facade contract
- shell/interior/lighting/anchors without NPC overhead
- registry/manifest `scene_path` alignment
- `full_map_pin` for `gun_shop`
- multi-building service icon expectations

## Minimum Scene Contract

Keep these stable unless there is a strong reason to rename them:

- root metadata
  - `city_service_scene_root = true`
  - `city_building_id`
  - `city_building_display_name`
  - `city_service_scene_kind`
- `GeneratedBuilding`
  - type `StaticBody3D`
  - `city_generated_building = true`
  - `city_service_scene_profile`
  - `city_inspection_payload`
- child sections
  - `Shell`
  - `Interior`
  - `Lighting`
  - `ServiceAnchors`

For most storefronts, add named doorway/window nodes so tests can assert them directly:

- `CollisionDoorJambLeft`
- `CollisionDoorJambRight`
- `CollisionWindowLeft`
- `CollisionWindowRight`
- `DoorLeafLeft`
- `DoorLeafRight`
- sign mesh such as `CafeSign` or `ShopSign`

## Full-Map Icon Wiring

When the building should appear on the full map:

1. add `full_map_pin` to the target manifest
2. keep `inspection_payload.world_position`
3. update `CityMapScreen.gd` glyph mapping for the new `icon_id`
4. update tests that assume a fixed pin count or only one icon-bearing building
5. preserve `visibility_scope = full_map`; do not leak into minimap

## Test Matrix

Pick the smallest relevant set, but do not skip the contracts touched by the change.

### Scene-only or interior rebuild

- `tests/world/test_city_<building>_scene_contract.gd`
- `& $godot --headless --rendering-driver dummy --path $project --quit`

### Manifest / registry / scene path changes

- `tests/world/test_city_<building>_manifest_contract.gd`
- scene contract test
- headless import check

### New or changed full-map icon

- target manifest contract test
- `tests/world/test_city_service_building_map_pin_runtime.gd`
- `tests/world/test_city_service_building_full_map_pin_contract.gd`
- `tests/e2e/test_city_service_building_full_map_icon_flow.gd`
- `tests/world/test_city_map_pin_overlay.gd`
- `tests/world/test_city_minimap_idle_contract.gd`
- `tests/world/test_city_service_building_map_pin_startup_delay_contract.gd`

### NPC / dialogue addition

Start from cafe tests and add or adapt:

- `tests/world/test_city_cafe_scene_contract.gd`
- `tests/e2e/test_city_cafe_barista_dialogue_flow.gd`
- `tests/world/test_city_npc_interaction_prompt_contract.gd`
- `tests/world/test_city_dialogue_runtime_contract.gd`

## PowerShell Verification Template

```powershell
$project='E:\development\godot_citys'
$godot='E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe'

& $godot --headless --rendering-driver dummy --path $project --script 'res://tests/world/test_city_gun_shop_scene_contract.gd'
& $godot --headless --rendering-driver dummy --path $project --script 'res://tests/world/test_city_gun_shop_manifest_contract.gd'
& $godot --headless --rendering-driver dummy --path $project --script 'res://tests/world/test_city_service_building_map_pin_runtime.gd'
& $godot --headless --rendering-driver dummy --path $project --quit
```

Swap the target scene/manifest tests to match the active building.
