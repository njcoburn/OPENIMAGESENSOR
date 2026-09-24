# Streamed nominal-frame evidence

See [the report](../../docs/streamed-frame.md) and `manifest.json` for the actual completion status and scope. This checkpoint is not a fabrication or full-chip qualification release.

The archive preserves the exact streamed frame inputs and raw output, three preliminary static-reference method probes, reports and scripts. The manifest records every file hash plus the hashes of the two earlier dependency archives. Derived `.npz` caches are omitted; analysis reads the original raw traces.

Restore dependencies first, then this archive, **only into an empty scratch directory**. Check the archive and per-file SHA-256 values before selecting artifacts to restore to a checkout. All archive paths are repository-relative; never blindly extract over current work.

The preliminary captured-state DC references add explicit sense-node voltage sources only for the static calculation. They are not proposed physical devices. Source-node voltages/currents, input hashes, control states and failures are included for review. The nominal screen report does not substitute for timestep/tolerance refinement, repeated frames, startup, PVT, distributed wiring resistance, optical characterization or board/ADC-specific validation.
