# GF180 3×3 checkpoint

This archive preserves the verified baseline and 5/10/20 µm junction-size study.
See [Docker and restore instructions](../docs/docker-setup.md).

On a clean checkout: `python3 scripts/restore-checkpoint.py`.
The restore checks `manifest.json` and refuses overwrites. Source files outside
`build/` remain the primary editable design. The archive is a saved result, not
a replacement for rerunning verification after changes.
