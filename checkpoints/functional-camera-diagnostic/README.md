# Switching diagnostic evidence

This archive preserves streamed waveforms, exact decks/models, solver logs, watchdog/setup failures, analysis and the scripts used for the bounded row-switching investigation. See [the report](../../docs/functional-camera-diagnostic.md) and `manifest.json` for scope, dependencies and SHA-256 hashes. It is not a full-frame or fabrication qualification checkpoint.

Restore only to an empty scratch directory:

```sh
mkdir -p /tmp/ois-switching-diagnostic
sha256sum checkpoints/functional-camera-diagnostic/evidence.tar.gz
tar -xzf checkpoints/functional-camera-diagnostic/evidence.tar.gz -C /tmp/ois-switching-diagnostic
```

Compare the archive hash with `manifest.json`, then verify its per-file hashes before selecting any artifacts to restore. Archive paths are repository-relative; do not extract over a working checkout. The earlier functional-camera archive supplies the stock OP, frozen-model metadata and node mapping needed by the report script. The raw-file parser deliberately ignores stale point counts and drops an incomplete last record after a watchdog stop.

The archive retains the original raw files. Derived local `waveforms.npz` caches are omitted to avoid duplicating the same data; the report reads the raw files directly.
