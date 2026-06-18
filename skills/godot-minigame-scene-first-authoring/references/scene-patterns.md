# Scene Patterns

## Core Rule

When a minigame object needs human eyeballing, scene authoring wins.

Use GDScript for:

- match state
- score and fail rules
- prompts, HUD, and audio cues
- AI targeting and timing
- additive animation deltas

Use `.tscn` authoring for:

- character holding a prop
- rest pose
- socket position
- visible court/pitch geometry
- prop placement
- manually tuned marker anchors

## Soccer Lessons

- If a goal, ball stand, or kickoff staging point is visually sensitive, put it in the scene and give it a stable anchor name.
- Do not bury service geometry inside a giant all-code venue builder if a human will want to move it later.
- Keep match logic in script, but let the pitch scene own the authored look.

## Tennis Lessons

- A held racket is not just another runtime child; it is a visually authored attachment problem.
- If the user wants to move the racket in the editor, do not also fight them with code-side rest transforms.
- Preserve authored rest transforms and only add swing deltas at runtime.
- If editor preview and runtime use different asset-load paths, assume scale drift until proven otherwise.
- Do not fix a giant racket by scaling the humanoid up.
- Do not save temporary compensation transforms onto the wrong node and then reapply compensation again in runtime.

## Recommended Node Ownership

Use this split by default:

```text
Venue scene
  owns court/pitch geometry, static markers, authored actor spawn points

Actor scene
  owns model, hand socket, authored held-item subtree

Gameplay script
  owns rules, state machine, AI, visibility toggles, runtime-only impulses/deltas

Visual helper script
  owns additive animation or optional normalization only when explicitly enabled
```

## Debugging Order

When editor looks right but runtime is wrong:

1. Confirm the authored scene file actually contains the intended nodes and transforms.
2. Check whether runtime code rewrites rest transforms, scale, or visibility.
3. Check whether editor preview and runtime use different asset loaders.
4. Measure actual runtime scale before changing more transforms.
5. Fix the ownership boundary, not the symptom.

## Acceptance Checklist

- Scene can be opened and tuned by hand.
- Runtime loads the same authored scene through `PackedScene`.
- Static held-item pose is not hardcoded in gameplay logic.
- A targeted contract test proves the prop still exists in runtime.
- An e2e test proves the minigame still plays after the authoring change.
