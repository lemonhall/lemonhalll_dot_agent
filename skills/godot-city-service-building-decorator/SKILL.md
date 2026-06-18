---
name: godot-city-service-building-decorator
description: Use when working in `godot_citys` and the user gives a generated custom building scene path, building name, or building_id and wants it remodeled into a real service building. Trigger for storefront/interior/signage/door work, plus manifest/registry/full-map wiring, or staff/NPC/dialogue consumer hookup with scene-contract tests, docs/plan, and Godot verification.
---

# Godot City Service Building Decorator

## Overview

Turn one exported generated building under `city_game/serviceability/buildings/generated/` into a real service-building consumer without breaking the existing override, map-pin, NPC interaction, and verification chains.

Read [references/godot-citys-building-patterns.md](references/godot-citys-building-patterns.md) when concrete exemplar files, test names, or repo-specific commands are needed.

## Workflow

1. Identify the asset quartet before editing anything:
   - target scene file
   - sibling `building_manifest.json`
   - `city_game/serviceability/buildings/generated/building_override_registry.json`
   - any downstream consumer touched by the request, usually `CityMapScreen.gd` or service-building tests
2. Read the target files and one nearest exemplar consumer.
   - Use the cafe scene when the building needs staff, dialogue, or rich interior anchors.
   - Use the gun shop scene when the building is storefront-heavy and needs shell, interior, props, or a staffed counter consumer.
3. Lock the scope.
   - Decide whether the task includes only shell/interior work, or also manifest/registry/full-map wiring, NPCs, dialogue, or tests.
   - If the user frames it as a versioned slice, add `docs/plans/` and `docs/plan/vN-*` evidence first.
4. Write failing tests before implementation.
   - Add or update scene-contract tests when the building layout or metadata changes.
   - Add or update manifest/registry contract tests when `scene_path`, `full_map_pin`, or building identity wiring changes.
   - If another icon-bearing building is added, update service-building pin tests so they no longer assume a single icon consumer.
5. Implement in this order:
   - fix `scene_path` drift between registry and manifest
   - fix `full_map_pin` and any `icon_id -> glyph` mapping
   - rebuild the `.tscn` shell/interior/lighting/anchors
   - add NPC/dialogue wiring only if explicitly requested, following `Staff And Dialogue Wiring`
   - update scene contract and e2e flow for any new staffed consumer
6. Verify with fresh Godot runs.
   - Run the most specific world tests first.
   - Then run the related e2e flow and a headless import check.
7. Close out properly.
   - Update version docs/evidence when used.
   - Commit, push, and send the required APN notification.

## Required Wiring

Always keep these contracts aligned:

- `building_override_registry.json`
  - `building_id`
  - `manifest_path`
  - `scene_path`
- target `building_manifest.json`
  - same `building_id`
  - same `scene_path`
  - `source_building_contract.inspection_payload.world_position` intact
  - `full_map_pin` when the building should appear on the full map
- target `.tscn`
  - root metadata: `city_service_scene_root`, `city_building_id`, `city_service_scene_kind`
  - `GeneratedBuilding` as `StaticBody3D`
  - `city_service_scene_profile`
  - `city_inspection_payload`
  - when staff/dialogue is requested: `Staff` root, stable actor metadata, and a formal interactable NPC contract

Do not let registry point at a stale `building_scene.tscn` placeholder while manifest or tests point at a renamed scene.

## Staff And Dialogue Wiring

When the request includes a waiter, clerk, barista, gunsmith, receptionist, or any other staffed consumer, wire it through the existing `v17` NPC interaction chain instead of inventing building-local interaction logic.

1. Read the cafe scene first.
   - Treat `咖啡馆.tscn` as the primary exemplar for `Staff/*`, `CityIdleServicePedestrian.gd`, interaction contract fields, and the `5m -> E -> dialogue -> close` flow.
2. Add a stable `Staff` branch in the target scene.
   - Prefer `GeneratedBuilding/Staff/<RoleName>` as the actor path.
   - Instance the chosen pedestrian model under `Model`.
3. Use `res://city_game/world/serviceability/CityIdleServicePedestrian.gd` on the actor node.
   - Set `idle_animation_name`, `source_height_m`, `target_visual_height_m`, and `source_ground_offset_m` for the chosen `.glb`.
   - Do not assume every civilian model uses the cafe barista defaults.
4. Fill the formal interactable NPC contract on the actor node.
   - `actor_id`
   - `display_name`
   - `interaction_kind = "dialogue"`
   - `interaction_radius_m = 5.0` unless the user explicitly changes it
   - `dialogue_id`
   - `opening_line`
5. Mirror the stable service metadata.
   - `city_service_actor_id`
   - `city_service_actor_role`
   - `city_service_actor_model`
6. Place the actor against a stable service anchor, not a random floor point.
   - For storefront staff, prefer the `counter` anchor or a position just behind the counter.
   - Face the customer area instead of the back wall or shelf.
7. Update tests with the same rigor as the scene work.
   - Extend the target scene contract test so it asserts actor path, role metadata, interaction contract, model source, and idle animation.
   - Add or update an e2e flow that proves `5m -> prompt visible -> E opens dialogue -> opening_line appears -> E closes dialogue`.
8. When an e2e needs to stage near the building, derive the absolute world position from manifest chunk metadata if needed.
   - Prefer `building_manifest.json -> source_building_contract.center + generation_locator.chunk_key` over trusting a stale scene-local `world_position` field.

## Scene Checklist

Build service buildings with stable named sections so tests and future edits stay cheap:

- `Shell`
- `Interior`
- `Lighting`
- `ServiceAnchors`
- `Staff` when the building has an on-site service worker
- `TerrainMitigation` when the footprint needs extra ground masking

For storefronts, prefer an explicit front facade contract:

- left/right front columns
- front top lintel
- door jambs
- transom or upper glass
- left/right windows
- readable sign mesh

For interiors, prefer low-poly `BoxMesh` / `CollisionShape3D` composition over bespoke complexity. Keep the room legible with a small number of strong props: counter, racks, display cases, shelving, runner, lights.

For staffed buildings, keep the actor contract cheap to read and future-proof:

- one stable actor path under `Staff`
- one stable role name in metadata
- one stable opening line on the actor contract
- actor standing in a believable service position relative to `ServiceAnchors`

## Common Pitfalls

- Forgetting to update both manifest and registry `scene_path`.
- Keeping the service scene as a single closed box with no real doorway contract.
- Adding `full_map_pin.icon_id` but forgetting the UI glyph mapping.
- Updating the target building but leaving service-building pin tests assuming there is only one icon-bearing building.
- Dropping `city_inspection_payload`, which breaks the stable building identity and map-pin world position chain.
- Adding service-building pins to full map without preserving minimap exclusion.
- Adding a visual NPC but forgetting `actor_id / interaction_kind / dialogue_id / opening_line`, so the runtime never sees an interactable consumer.
- Copying cafe idle parameters onto a different `.glb` without checking animation names or source height first.
- Staging e2e near a staffed building with stale scene-local coordinates instead of resolving the absolute world position from manifest chunk metadata.
- Updating only the scene contract test and forgetting the interaction/dialogue e2e for the new staffed consumer.
- Editing the scene but skipping a headless import check; malformed `.tscn` text fails late.

## Verification

Default verification order:

1. target scene contract test
2. target manifest contract test when manifest/registry changed
3. affected service-building map pin tests when `full_map_pin` or icon wiring changed
4. affected e2e full-map or interaction flow
5. shared NPC/dialogue consumer regression e2e when reusing the `v17` interaction chain
6. `Godot --headless --quit` import check

If the request changes only visuals inside one existing scene and the user explicitly forbids tests, still run at least the import check unless they forbid that too.
