# Godot Citys Scene Landmark Patterns

## Core Files

Always inspect these first in `godot_citys`:

- `city_game/world/inspection/CityWorldInspectionResolver.gd`
- `city_game/world/features/CitySceneLandmarkRegistry.gd`
- `city_game/world/features/CitySceneLandmarkRuntime.gd`
- `city_game/serviceability/landmarks/generated/landmark_override_registry.json`
- target landmark directory
  - scene file
  - `landmark_manifest.json`
- map consumer when needed
  - `city_game/world/map/CityMapPinRegistry.gd`
  - `city_game/ui/CityMapScreen.gd`
- tests closest to the change
  - ground-probe contract
  - manifest contract
  - visual envelope
  - mount/full-map flows

## Known Working Consumer

### Fountain Pattern

Use when the user wants a discrete landmark with near-chunk mounting and optional full-map pin.

- Manifest:
  - `city_game/serviceability/landmarks/generated/landmark_v21_fountain_chunk_129_142/landmark_manifest.json`
- Scene:
  - `city_game/serviceability/landmarks/generated/landmark_v21_fountain_chunk_129_142/fountain_landmark.tscn`
- Registry:
  - `city_game/serviceability/landmarks/generated/landmark_override_registry.json`
- Tests:
  - `tests/world/test_city_fountain_landmark_manifest_contract.gd`
  - `tests/world/test_city_fountain_landmark_visual_envelope.gd`
  - `tests/world/test_city_world_feature_full_map_pin_contract.gd`
  - `tests/e2e/test_city_scene_landmark_mount_flow.gd`
  - `tests/e2e/test_city_fountain_landmark_full_map_flow.gd`

What it teaches:

- `feature_kind = scene_landmark`
- absolute manifest `world_position` must include correct terrain `y`
- visual-envelope validation matters as much as mount validation
- full-map icon remains manifest-driven and minimap-excluded
- when manual visibility fails, a temporary giant beacon is a valid debugging tactic

## Ground-Probe Placement Checklist

Before you place or debug a landmark, verify all of these:

1. `ground_probe` payload includes `world_position` and explicit `surface_y_m`
2. copied HUD or clipboard text includes `y=`
3. manifest `world_position` matches the intended absolute placement
4. `anchor_chunk_id` / `anchor_chunk_key` match the same world position
5. landmark scene local transforms do not sink the mesh under ground

## Minimum Landmark Contract

Keep these stable unless there is a strong reason to rename them:

- registry entry
  - `landmark_id`
  - `feature_kind`
  - `manifest_path`
  - `scene_path`
- manifest
  - `landmark_id`
  - `display_name`
  - `feature_kind`
  - `anchor_chunk_id`
  - `anchor_chunk_key`
  - `world_position`
  - `scene_path`
  - `manifest_path`
  - optional `full_map_pin`
  - optional `far_visibility`
- runtime pin contract when enabled
  - `pin_type = landmark`
  - `icon_id`
  - `title`
  - `subtitle`
  - `priority`
  - `visibility_scope = full_map`

## Landmark vs Terrain Region Decision

Use `scene_landmark` when:

- the feature is spatially discrete
- a single authored scene can represent it
- near-chunk mount / retire behavior is acceptable

Do not use `scene_landmark` when:

- the feature spans large terrain areas
- the feature needs heightmap carving, water surfaces, or nav topology changes
- the user is really asking for a mountain, lake, canyon, or large landform

For those cases, stop and reframe the task as a future `terrain_region_feature` route.

## Test Matrix

Pick the smallest relevant set, but do not skip the contracts touched by the change.

### Ground-probe or HUD payload change

- `tests/world/test_city_ground_probe_inspection_contract.gd`
- `tests/world/test_city_player_laser_designator.gd`

### New or moved landmark scene

- target manifest contract test
- target visual envelope test
- target mount flow
- `& $godot --headless --rendering-driver dummy --path $project --quit`

### New or changed full-map icon

- target manifest contract test
- `tests/world/test_city_world_feature_full_map_pin_contract.gd`
- `tests/e2e/test_city_fountain_landmark_full_map_flow.gd`

## PowerShell Verification Template

```powershell
$project='E:\development\godot_citys'
$godot='E:\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe'
$tests=@(
  'res://tests/world/test_city_ground_probe_inspection_contract.gd',
  'res://tests/world/test_city_player_laser_designator.gd',
  'res://tests/world/test_city_fountain_landmark_manifest_contract.gd',
  'res://tests/world/test_city_fountain_landmark_visual_envelope.gd',
  'res://tests/e2e/test_city_scene_landmark_mount_flow.gd',
  'res://tests/e2e/test_city_fountain_landmark_full_map_flow.gd'
)
foreach($test in $tests){
  & $godot --headless --rendering-driver dummy --path $project --script $test
  if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
}
```
