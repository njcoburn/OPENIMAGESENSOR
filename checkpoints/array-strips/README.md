# Extracted 64-pixel strips checkpoint

Concatenate `evidence.tar.gz.part-*` in filename order and restore into an empty scratch directory. Every archive member, split part and combined archive was read back and verified.

Includes GDS, direct and RC-collapsed LVS, extraction, raw and adjusted RC models, audit, complete traces, matched DC references, exact runner snapshots and excluded fixture-development attempts. Read docs/array-strips.md and build/array-strips-20260924/attempts.json before interpreting results. This is unfilled-strip evidence, not full 64×64 or fabrication qualification.

The archive retains the creator script as executed. Its initial random-access verification was stopped after compression; `scripts/verify-array-strips-checkpoint.py` verified the completed archive in one streaming pass, with its hash recorded in the manifest. The current creator script now uses the same streaming approach for future checkpoints.
