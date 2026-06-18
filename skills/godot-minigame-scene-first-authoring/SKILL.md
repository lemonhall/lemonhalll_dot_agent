---
name: godot-minigame-scene-first-authoring
description: Use when working in `godot_citys` on sports or reaction minigames that need manually authored character/prop placement, sockets, held items, court/pitch scenes, or other visually sensitive setup. Trigger when Godot editor placement should own static transforms and imported asset scale, while GDScript should stay focused on rules, state, scoring, prompts, AI, and runtime-only deltas.
---

# Godot Minigame Scene First Authoring

## Overview

Prefer `.tscn`-authored setup for any minigame work where a human would want to visually place a player, racket, ball, goal, marker, or socket in the editor. Keep static pose, rest transform, attachment offset, and author-time visual composition in scenes. Keep GDScript for rules and runtime state only.

Read [references/scene-patterns.md](references/scene-patterns.md) when you need the soccer/tennis pitfall list, concrete node hierarchies, or the editor-vs-runtime transform failure patterns.

## Workflow

1. Classify the request before touching code.
   - Use this skill when the task involves visible placement or alignment: player holding a racket, AI holding a prop, start ring location, court/pitch dressing, ball stand, goal mouth, receive marker anchor, or any other thing a human would naturally want to drag in the editor.
   - Do not use this skill for pure scoring logic, rally state machines, HUD text changes, or AI targeting rules with no scene-authoring component.
2. Split ownership clearly.
   - Scene owns: imported meshes, static offsets, sockets/anchors, rest pose, held-item placement, court geometry, decorative props, manually tuned marker anchors.
   - Script owns: rules, scoring, prompts, AI, animation state, visibility toggles, swing tokens, sound triggers, runtime-only marker updates.
   - If a transform is meant to be edited by hand later, do not also hardcode it in GDScript.
3. Build the hierarchy explicitly.
   - Prefer `PackedScene` consumers over rebuilding the same hierarchy with `Node3D.new()` every run.
   - Give authored anchors stable names such as `TennisRacketSocket`, `BallSpawnAnchor`, `ServeAnchor`, `GoalkeeperStandAnchor`.
   - Let gameplay scripts load the authored scene, then talk to named nodes or small visual scripts.
4. Keep one scale system.
   - Do not scale the character up to cancel an oversized prop.
   - Do not use one loader in the editor and another loader at runtime unless you have proven they preserve the same units.
   - If a visual subtree is authored in-scene, runtime must preserve that authored rest transform by default.
5. Add runtime deltas on top of authored rest state.
   - Use authored nodes for idle placement.
   - Apply swing/serve/hit reactions as additive deltas from the authored rest transform, not as a full replacement of the mount transform.
   - If a visual script must normalize imported geometry, make that behavior explicit and opt-in.
6. Verify in the same order every time.
   - editor scene looks correct
   - runtime still shows the authored prop
   - targeted world contract passes
   - one e2e gameplay flow still passes

## Required Patterns

- Use a dedicated actor scene when a minigame player or NPC holds a prop.
- Use a dedicated socket node when hand placement matters.
- Keep the venue script loading a `PackedScene` for authored actors instead of constructing the full visual tree inline.
- Preserve authored transforms unless the user explicitly asks for code-driven normalization.
- When a visual script supports both authored mode and normalized mode, make the mode explicit in config.

Example hierarchy:

```text
TennisOpponent.tscn
  TennisOpponent
    Visual
    .../RightHand
      TennisRacketSocket
        TennisRacketVisual
          MountRoot
            Visual
```

## Common Mistakes

- Building the whole held-item hierarchy in code because it feels faster, then discovering no one can tune the pose visually.
- Saving a compensation transform on the wrong node and then compensating it again at runtime.
- Letting a tool-time preview path and runtime load path use different units.
- Scaling a humanoid mesh to match a bad prop import instead of fixing the prop path.
- Mixing static authored pose with hardcoded `mount_position` / `rest_rotation_deg` in script.
- Calling `configure_rig()` in a way that silently overwrites scene-authored rest transforms.
- Judging success from the editor only and forgetting that runtime may hide or re-normalize the authored prop.

## Verification

Minimum closeout for scene-first minigame work:

1. Open the authored scene in Godot and confirm the pose visually.
2. Run a focused world contract that proves the prop still exists in runtime.
3. Run one gameplay e2e that proves the minigame still works after the scene wiring change.
4. Only after that, tune optional visuals or sound.
