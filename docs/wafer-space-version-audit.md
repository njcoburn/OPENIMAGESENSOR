# wafer.space environment audit

Checked 2026-09-19 11:09 PDT. Read-only comparison of installed tools and separately downloaded reference files. No working PDK, simulator, layout or acceptance gate was changed.

## Conclusion

The installed **gf180mcuD** process and **gf180mcu_fd_io** pad library are supported wafer.space choices. The installed PDK build is older than the currently published template/precheck pins. However, the actual relevant model and pad files match the newer template. This audit finds no evidence that a different pad-corner design is required, or that updating the PDK alone fixes our transient convergence failure.

| Item | Installed | Published reference / comparison |
|---|---|---|
| Process | gf180mcuD, 5 metal layers | Same template and precheck default |
| PDK build | b344c97eacc2aaf8e14ae7e43e2e9dc0871de2c0; open_pdks 1.0.599 | Template f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7; metadata 1.0.605 |
| Precheck PDK pin | Not our installed revision | d658698bd8bcf4e05fc7b5991a701247ba0d744c |
| ngspice | 46, KLU build | Reviewed wafer.space template provides RTL/gate-level simulation targets; this audit establishes no prescribed analog-ngspice version |
| Magic executable | 8.3.664 | Template PDK metadata says built with 8.3.674; build provenance, not proof of required runtime |
| sm141064.ngspice | Stock installed model | Byte-for-byte identical to template PDK |
| design.ngspice | Stock installed parameters | Byte-for-byte identical |
| Foundry I/O SPICE | gf180mcu_fd_io.spice | Byte-for-byte identical |
| Foundry I/O GDS | gf180mcu_fd_io.gds | Identical after zeroing only GDS library/structure timestamps (963 records) |
| Magic gf180mcuD.tech | Installed technology | Only difference is the version-label line; extraction rules unchanged in this file |

Template and precheck currently pin different PDK revisions. They must be recorded separately; there is no single revision established by these two pages. Detailed file comparison was against the **template** revision, not the precheck payload. The full PDK and all verification decks were not compared.

## What the failure means

Our failing test is an extracted physical corner coupon with a custom resistor/capacitance representation and a **local experimental MOS-capacitor helper normalization**. It is not an untouched wafer.space reference simulation. Both tighter runs fail in that helper at a 151 µs load transition. This is evidence that our numerical qualification has not passed, not evidence that a foundry pad macro cannot be manufactured or works incorrectly in silicon. Stock-model failures from earlier work also remain relevant; this audit does not establish the cause of either failure.

The foundry I/O library upstream revision is identical in both metadata files: `40cdef6d74ec5c9b7d596c147df94c98366afc5b`. The optional OCD library is absent from the installed libs.ref directory; its presence in nodeinfo metadata does not mean it is installed. The template supports both libraries, so its absence does not invalidate a foundry-I/O design.

## Next action

1. Keep the present reproducible checkpoint and pad geometry. Do not redesign the corner based on a solver failure.
2. Use an isolated tool environment for a controlled simulator-version comparison with the **stock** model first. Test an unextracted stock corner/supply macro and then the extracted coupon with the same physical stimulus. Keep the experimental helper model as a separately labeled diagnostic.
3. Record exact solver, model, startup configuration and extraction hashes; compare completed traces and refinement, not merely a successful exit code. Updating identical model files is not a substantive new hypothesis.
4. Run the official wafer.space precheck under its pinned environment after choosing the submission slot. Existing custom DRC/LVS passes do not replace it; the precheck also checks slot geometry and, for CoB, prescribed pad openings/identification cells. Our custom 1.210 mm ring is not a final slot wrapper.

## Official sources and evidence

- [wafer.space technology](https://wafer.space/technology.html): GF180MCU and designer sign-off responsibilities.
- [Project template](https://github.com/wafer-space/gf180mcu-project-template): foundry/OCD pad options and standalone analog pad-ring target.
- [Template Makefile](https://github.com/wafer-space/gf180mcu-project-template/blob/main/Makefile): process/library defaults and PDK pin.
- [Precheck Makefile](https://github.com/wafer-space/gf180mcu-precheck/blob/main/Makefile): separate PDK pin.
- [Precheck requirements](https://github.com/wafer-space/gf180mcu-precheck): geometry, DRC, density, antenna and optional CoB checks.
- [Template PDK release](https://github.com/fossi-foundation/ciel-releases/releases/tag/gf180mcu-f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7): downloaded common and foundry-I/O archives, sizes and GitHub SHA-256 digests verified.
- [Saved manifests, source snapshots, hashes and comparison scripts](../checkpoints/wafer-space-version-audit/manifest.json). Large reference archives remain in build/wafer-space-version-audit; the working Docker image was not changed.
