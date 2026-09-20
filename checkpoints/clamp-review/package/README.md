# GF180 extracted-clamp transient reproducer

Prepared 2026-09-19 02:01 PDT; **not sent**. See the accompanying review brief. The PDK is not redistributed; the decks include the installed GF180MCU D models at `/foss/pdks/gf180mcuD/libs.tech/ngspice`.

From this extracted package directory, with Docker available:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work --entrypoint /bin/bash hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a -lc 'python3 run.py klu-trap-50ns'
```

Use any directory name under `cases/` to replay a case. Archived logs/waves are preserved; replays write under `replay/`. A failure is expected for the reported failing case. The runner limits each case to 120 seconds; runtime varies by hardware. This is diagnostic evidence, not a claim that timeout proves non-convergence. The prior 100 ns completion and earlier runs used their documented 180-second watchdog.

Only the two `sparse-*` decks change solver selection from their matching `klu-*` 50 ns cases. The selected clamp contains 144 device records, 22,575 resistors and 127 explicit wiring capacitors. It omits other semiconductor groups and is not a full-chip equivalent. Local startup settings are in `init/.spiceinit`. PDK and original input hashes are recorded separately.
