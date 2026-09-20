# Public issue draft: ngspice 47 behavioral capacitor with explicit subcircuit multiplier generates invalid G-source gain

Draft prepared 2026-09-19. **Not posted.** This parser issue is separate from the image-sensor project's extracted startup convergence issue.

## Summary

Using official ngspice 46 and 47 source releases built with matching options in the same container, the circuit below succeeds in 46 but fails before simulation in 47. It contains no foundry PDK. Omitting `m=8` succeeds in both. Explicit `m=1`, `m=8` and `m=70` all fail in 47.

## Reproducer

Use this `.spiceinit` (the compatibility settings used in our original GF180 environment):

```text
set ngbehavior=hsa
set wnflag=1
```

```spice
Behavioral capacitor multiplier parser reproducer -- no PDK
Vdrive drive 0 1
Rdrive drive n 1k
.subckt nonlinear_cap p n
Ctest p n C='1p*(1+0.1*tanh(v(p,n)))'
.ends nonlinear_cap
Xcap n 0 nonlinear_cap m=8
.control
op
print v(n) i(Vdrive)
quit
.endc
.end
```

Run `ngspice -b test.spice` with the init directory selected via `SPICE_USERINIT_DIR`.

## Expected / observed

Expected: the multiplier scales the capacitor and the DC analysis completes. Version 46 completes. Version 47 prints `unknown parameter (e9)` on the generated G-source line and exits with status 1.

In the release-47 `src/frontend/inpcom.c`, the capacitance-formulation expansion uses a `tprintf` format ending in `%se9`. `eval_mvalue()` can return a formatted number with an exponent (or a brace-expression string), so appending another exponent suffix does not represent numeric multiplication by 1e9. This is a source-reading diagnosis; no source patch is included or claimed validated.

## Environment / evidence

- Source: official SourceForge release tarballs for 46 and 47.
- Both built with GCC in the pinned IIC-OSIC container, `CFLAGS=-O2`, `--enable-klu --with-x=no --with-readline=no --disable-debug`.
- ngspice-47 source tarball SHA-256: `894e649651f1838a14095e5a5439e7d3aa63e87ede14d283173fda4fcdef675f`.
- [Version comparison and source/binary hashes](../../checkpoints/ngspice-version-comparison/evidence.tar.gz), including all eight minimal parser runs under `multiplier-reproducer/`.
- Reproducer runner: [scripts/reproduce-ngspice47-cap-multiplier.py](../../scripts/reproduce-ngspice47-cap-multiplier.py).

Could maintainers confirm the intended multiplier scaling in this new expansion? A parser correction should be checked against both numeric and parameterized multipliers and terminal current/charge behavior.

The separate extracted startup failure still occurs without explicit multipliers. Resolving this parser issue alone would not establish a fix for that failure.
