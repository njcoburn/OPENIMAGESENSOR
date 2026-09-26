# Row power-feed checkpoint

202 files; every archive member was read back and checked against its size and SHA-256. Partial and deliberately stopped runs are included with explicit classifications. Read `docs/row-power.md` for accepted evidence and remaining gates.

Archive SHA-256: `7a045aac5386c74acba4f217ae4ccd22231e7eaebcda210eecc1364cd7698d8e`.

Concatenate the numbered parts in order, verify the archive checksum, and extract into an empty scratch directory. Do not overwrite existing evidence. Use the pinned tools/PDK container from the earlier array-recovery stage. SPICE include paths use its `/foss/designs` mount. The earlier 17.7 GB array-recovery archive remains unchanged; it is not duplicated here.
