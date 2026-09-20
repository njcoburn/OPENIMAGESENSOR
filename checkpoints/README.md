# GF180 3×3 checkpoint

## Filled-layout checkpoint — 2026-09-19 03:15 PDT

The latest separate archive is [filled-demonstrator/evidence.tar.gz](filled-demonstrator/evidence.tar.gz), with [hash manifest](filled-demonstrator/manifest.json). See [scope and reproduction](../docs/filled-demonstrator.md); it is not a fabrication release.

## Routed working assembly — 19 September 2026

[routed-demonstrator/manifest.json](routed-demonstrator/manifest.json) describes the separate routed-layout evidence archive. This includes its three source GDS inputs and placement metadata, generated layout, device reference, physical checks and screenshots. Read [the report](../docs/routed-demonstrator.md) for exclusions and outstanding work; it is not a fabrication release. Inspect or unpack the archive into a separate directory before copying any files over an existing workspace.

This archive preserves the verified baseline and 5/10/20 µm junction-size study.
See [Docker and restore instructions](../docs/docker-setup.md).

On a clean checkout: `python3 scripts/restore-checkpoint.py`.
The restore checks `manifest.json` and refuses overwrites. Source files outside
`build/` remain the primary editable design. The archive is a saved result, not
a replacement for rerunning verification after changes.

## Functional-camera diagnostic checkpoint — 19 September 2026

[Evidence](functional-camera/evidence.tar.gz) · [hash manifest](functional-camera/manifest.json) · [handoff and restore notes](../PICK_UP_HERE.md). Stock final-chip DC completes; no full-frame transient is accepted.
