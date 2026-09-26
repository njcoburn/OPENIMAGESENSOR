# Camera load and operating-corner checkpoint

Concatenate `evidence.tar.gz.part-*` in filename order and restore to an empty scratch directory. The manifest records every member, part and combined archive hash; all were read back and verified. Includes exact stock/frozen models, capacitor recalculations, decks, full waveforms, matched DC references and failed or timed-out attempts.

Read `docs/camera-operating-corners.md` for measured results, selected coverage and limitations. Startup, full distributed R+C and fabrication qualification remain open.
