---
name: godot-city-scene-landmark-authoring
description: Use when working in `godot_citys` and the user wants to place a non-building authored world landmark such as a fountain, tower, statue, monument, or debug beacon into the streamed city through the `v21` scene-landmark chain. Trigger for `ground_probe`, `landmark_manifest.json`, `landmark_override_registry.json`, near chunk mount, and optional full-map pin work, especially when absolute `y` height, lazy loading, visual envelope, or landmark-specific pitfalls matter.
---

# Godot City Scene Landmark Authoring

## Overview

Turn one authored landmark scene into a formal `scene_landmark` consumer without abusing building overrides or breaking streaming, map-pin, and inspection contracts.

Read [references/godot-citys-scene-landmark-patterns.md](references/godot-citys-scene-landmark-patterns.md) when you need the repo-specific file checklist, known-good fountain pattern, or test names.

## Workflow

1. Classify the request before editing anything.
   - Use this skill only for discrete authored landmarks that can be mounted as a scene: fountain, tower, statue, monument, sculpture, debug beacon.
   - Do not use this skill for mountain, lake, terrain carve, or water body work. Those are future `terrain_region_feature` sibling routes, not `scene_landmark`.
2. Identify the landmark quartet.
   - target scene file under `city_game/serviceability/landmarks/generated/<landmark-id>/`
   - sibling `landmark_manifest.json`
   - `city_game/serviceability/landmarks/generated/landmark_override_registry.json`
   - downstream consumer touched by the request, usually `CityWorldInspectionResolver.gd`, `CityMapPinRegistry.gd`, or `CityMapScreen.gd`
3. Start from a real ground probe, not a guessed height.
   - Prefer laser `ground_probe` output copied from the game.
   - Require or derive `chunk_id`, `chunk_key`, and absolute `world_position`, including `y`.
   - Treat missing `y` as an incomplete placement input.
4. Read one nearest exemplar before implementing.
   - Use the fountain consumer when the request is a standard `scene_landmark`.
   - If the user cannot find the landmark in-game, inspect both manifest `world_position` and the landmark scene's local transforms.
5. Lock the scope.
   - Decide whether the request includes only scene/manifest/registry work, or also full-map icon wiring, debug beacon staging, or inspection/HUD contract changes.
   - Decide whether the landmark should be full-map only, or world-only with no pin.
6. Write failing tests first.
   - Add or update ground-probe contract tests when inspection payload or HUD/clipboard changes.
   - Add or update manifest/runtime/full-map tests when the landmark coordinates, icon wiring, or mount path changes.
   - Add or update a visual envelope test when the landmark can exist but still be effectively invisible.
7. Implement in this order.
   - fix or extend `ground_probe` contract if placement data is missing
   - author or clean the landmark `.tscn`
   - set manifest `world_position` to the absolute sampled ground height
   - sync registry `scene_path` / `manifest_path`
   - wire optional `full_map_pin` and any `icon_id -> glyph` mapping
   - only then tune visuals, debug beacon scale, or proxy staging
8. Verify with fresh Godot runs.
   - run the smallest world tests first
   - then run landmark mount/full-map e2e
   - run a headless import check if the request changes scene text only and nothing else
9. Close out properly.
   - update `docs/prd/` and `docs/plan/vN-*` when the request is versioned
   - commit, push, and send the required APN notification

## Required Wiring

Always keep these contracts aligned:

- `ground_probe` when used for authored placement
  - `chunk_id`
  - `chunk_key`
  - `world_position`
  - `surface_y_m`
  - `chunk_local_position`
- `landmark_override_registry.json`
  - `landmark_id`
  - `manifest_path`
  - `scene_path`
- target `landmark_manifest.json`
  - same `landmark_id`
  - `feature_kind = "scene_landmark"`
  - `anchor_chunk_id`
  - `anchor_chunk_key`
  - absolute `world_position` with the sampled `y`
  - `full_map_pin` only when the user wants a full-map icon
- target `.tscn`
  - stable root node for the landmark
  - local transforms that do not bury the mesh below manifest ground height
  - readable visual envelope when the landmark is meant to be found manually

Do not let registry and manifest drift to different scene paths or different landmark ids.

## Height Discipline

The most common failure is not "landmark failed to load". It is "landmark loaded underground".

Always enforce these rules:

1. Trust absolute `world_position.y`, not memory or guessed terrain height.
2. Keep `surface_y_m` and `world_position.y` consistent.
3. Remember that scene-local transforms can still sink the mesh even when manifest `y` is correct.
4. If manual visibility is failing, temporarily stage a giant debug beacon before blaming registry/runtime.
5. When the player sends a copied ground-probe payload, preserve the `y=` field end to end.

## Full-Map Pin Wiring

When the landmark should appear on the full map:

1. add `full_map_pin` to the manifest
2. keep pin world position driven from the manifest, not inferred from scene extents
3. update `icon_id -> glyph` mapping only if the icon is new
4. preserve `visibility_scope = full_map`
5. keep the landmark out of minimap unless the user explicitly asks for a different scope

## Performance Rules

- Keep authored landmark scenes lazy-mounted through the chunk runtime.
- Do not preview-instantiate landmark scenes during registry sync just to validate them.
- Do not add per-frame full-registry scans.
- Do not solve long-range visibility by keeping the full near-scene resident forever.
- For tall landmarks, use `far_visibility` only as a cheap future proxy contract, not as permission to keep the expensive scene alive.

## Common Pitfalls

- Copying only `x/z` from a ground probe and forgetting the sampled `y`.
- Treating scene-local coordinates as absolute world coordinates.
- Fixing manifest `y` but forgetting a negative local mesh offset inside the `.tscn`.
- Assuming "map marker is correct" means the landmark scene is visible; map pins can be right while the mesh is underground.
- Adding a full-map pin but forgetting the UI glyph mapping for a new `icon_id`.
- Leaking landmark pins into the minimap.
- Treating mountains or lakes as `scene_landmark` work instead of a future terrain/water feature route.
- Claiming the landmark is mounted without a visual envelope test when the node can exist but still be unreadable.
- Leaving a temporary debug beacon in place without telling the user it is intentional.
- Ignoring Godot ext_resource UID warnings when they start spamming every mount; text-path fallback may work, but the warning still needs conscious triage.

## Verification

Default verification order:

1. ground-probe contract test when inspection payload changes
2. target landmark manifest contract test
3. target landmark visual envelope test
4. target landmark mount e2e
5. full-map pin flow when `full_map_pin` or icon wiring changed
6. `Godot --headless --quit` import check

If the request changes only visuals inside one existing landmark scene and the user explicitly forbids tests, still run at least the import check unless they forbid that too.
