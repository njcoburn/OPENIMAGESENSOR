# Three-frame checkpoint

Concatenate `evidence.tar.gz.part-*` in filename order. Member, part and combined archive hashes are recorded in the manifest and were verified. Exact transient and conditional DC-reference decks, waveforms and logs are included.

The initial timed-out raw trace may be represented by its archived exact header plus a verified prefix of the completed trace Binary section; the manifest records reconstruction length and the original complete-file SHA-256, which was verified from archive members. No trace samples are discarded.

Read `docs/three-frames.md` for measured outcomes and model limitations. This is normal-operation evidence, not startup, RC, corner or fabrication qualification.
