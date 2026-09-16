# Extracted 20 µm 3×3 array

The comparison uses the existing, verified filled layout and its matching unfilled functional control. It does not modify either GDS. Results and source hashes are in [parasitic-results.json](../simulations/parasitic-results.json); the plot and comparison table are embedded in [the notebook](overview.html#parasitics).

## Reproduce

Restore the existing checkpoint using [Docker setup](docker-setup.md), then run:

```bash
bash scripts/run-tools.sh bash scripts/run-parasitics.sh
```

The pinned image supplies Magic 8.3.664, ngspice, Netgen and SciPy. No host virtual environment is needed. Generated extraction files, netlists, LVS logs, testbenches and waves are under `build/parasitics/`; these build artifacts are not part of the earlier checkpoint archive.

A compact snapshot of the reduced netlists, reduction audits and matching LVS reports is saved in [`simulations/extracted-20um`](../simulations/extracted-20um), with a SHA-256 manifest. Full raw extraction files can be regenerated with the command above.

The half-step / tighter-tolerance check changed sampled outputs by at most **0.0061 mV**. This supports the millivolt-scale comparison; microvolt frame-change figures should still be treated as numerical diagnostics.

## Method

1. Read the 20 µm variant GDS and physically flatten the array in Magic. Use the nominal `ngspice()` GF180MCU D extraction style with coupling and resistance enabled. Resistance threshold is 1 Ω, minimum resistor 0.1 Ω, minimum delay zero; command inputs use milliohms. Export every extracted capacitance (`cthresh 0`).
2. Keep all transistor, diode, resistor and port nodes. Eliminate only purely capacitive nodes using the Schur complement of the capacitance matrix. This preserves the linear terminal charge/voltage relation for initially charge-neutral floating fill. It does not ground the fill. Sparse linear-solve residuals, symmetry, eigenvalues, random-vector charge/energy agreement and truncation error are checked. Capacitors below 0.000001 fF may be omitted; maximum matrix row error must remain below 0.001 fF.
3. Verify the extracted devices independently against the schematic in Netgen, with parasitic resistors shorted and capacitors omitted. Preserve transistor diffusion area/perimeter and diode area/perimeter. Infer pixel identity from circuit connections, not extractor instance ordering.
4. Compare schematic, extracted devices alone, C-only unfilled/filled, and RC unfilled/filled using identical three-frame scan stimuli and solver settings. Check correct brightness ordering and agreement of the devices-only control with the schematic.

The diode's area and perimeter capacitance remains in its GF180 device model. No assumed lumped sense capacitor is added to the extracted array. The extracted interconnect capacitance is additional. The unfilled array is a control for fill loading, not a density-clean manufacturing alternative.

## Observed comparison

At 80 pA, the schematic gives 201.431 mV dark-subtracted signal, compared with 190.176 mV for unfilled RC and 175.635 mV for filled RC. The filled RC value is 12.8% below the schematic. Shorting the filled model’s resistors changes this signal by just 0.014 mV, so capacitance dominates this particular scan. These figures do not establish the settling of a larger array or an external ADC interface.

## Limits

This is nominal PDK-based engineering extraction, not a field-solver comparison or fabrication signoff. Floating-fill reduction assumes zero initial net charge and linear capacitance. The model omits optical responsivity calibration, noise, process/temperature variation, pad/ESD and package parasitics, PCB loading and actual amplifier/ADC input circuitry. Tiny deterministic frame changes should not be interpreted as a sensor noise floor.

Next implement column bias, multiplexing and an output buffer, then sweep realistic external loads and sampling delays. Row circuits drive reset/selection; columns carry the analog outputs. An off-chip ADC remains a suitable architectural target, pending settling and drive verification.

## Tool references

- [Magic extraction workflow](https://www.opencircuitdesign.com/magic/howto.html)
- [Integrated resistance extraction settings](https://www.opencircuitdesign.com/~tim/programs/magic/commandref/extresist.html)
- [SPICE export settings](https://www.opencircuitdesign.com/magic/commandref/ext2spice.html)
