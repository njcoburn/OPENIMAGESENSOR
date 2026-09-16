# Extracted buffer in the three-block electrical model

The verified three-PMOS buffer layout is extracted and connected to the separately extracted array and qualified readout. The candidate retains the 40 µA buffer reference, all-row 20 µs startup reset, 100 pF board load, 20 pF sampler and 5 µs acquisition window.

## Extraction and checks

Magic physically flattens the buffer before extracting resistance and coupling capacitance. The settings retain resistors above the configured extraction thresholds (1 Ω threshold, 0.1 Ω minimum resistor) and export all capacitances before reduction.

The raw buffer has **19 resistors and 150,473 capacitors**. Eliminating **21,085 capacitive-only floating nodes** leaves **276 effective capacitors**. The linear reduction assumes zero net initial charge on floating fill. It preserves the terminal capacitance relation; solve residuals, symmetry, eigenvalues, charge/energy agreement and bounded truncation error are checked. It does not ground the fill.

The buffer needs no negative-shunt redistribution correction. This is distinct from the existing readout model, which still retains its documented BIAS-shunt approximation. The buffer's PMOS diffusion geometry stays in its device models.

Netgen checks extracted device connectivity against the independent buffer circuit with parasitic resistors shorted and capacitors removed. A nominal device-only transient is an additional control. A nominal C-only transient shorts the wiring resistors while retaining extracted capacitance. The full RC model runs the prior 24-case process/temperature matrix; cold and worst-case runs receive a finer-timestep check.

Cold and worst-case checks at 0.05 µs / 1e-5 relative tolerance preserve the passing results; maximum sampled-voltage change is **0.00516 mV**. Simulation decks, logs and result summaries are archived in `checkpoints/buffer-pex-evidence.tar.gz`, with SHA-256 hashes in the adjacent manifest.

## Interpretation

All **24/24 full-RC cases** pass the **0.5 mV** sampling screen, as do the two nominal controls. The worst hold error is **0.1965 mV**, at typical MOS / fast diode / 125 °C. Maximum sampled-output change from the schematic buffer is **0.8090 mV** (sf / −40 °C). At nominal conditions, the device-only control changes output by 0.00001 mV and the C-only control by 0.00149 mV, indicating that resistance accounts for most of the buffer-induced voltage shift.

Sampling error uses the same corner's loaded DC transfer curve. The separate output-shift metric compares identical sample times against the prior schematic-buffer run. Wiring resistance can change DC voltage offsets even if dynamic sampling error stays small. Small tracking error is not proof that the original voltage calibration remains valid.

The three blocks connect through ideal wires. There is no extracted routing or coupling between blocks and no shared physical supply/ground network. Device corners and temperature vary, but extracted wire R/C, references, load values and assumed photocurrent remain fixed. No actual ADC, ESD/pad circuit, reference generator, noise, mismatch or optical characterization is implied.

## Reproduce

```bash
bash scripts/run-tools.sh bash scripts/run-buffer-pex.sh
```

Input: `checkpoints/output-buffer/output_buffer.gds`, checked against its saved verification hash. The script preserves that GDS. Compact models, raw extraction archive, reduction checks and LVS log are saved in `checkpoints/output-buffer/pex/`. Full waves, DC curves and generated testbenches are under `build/buffer-pex/sim/`.

Results: [buffer-pex.json](../simulations/buffer-pex.json) and [the notebook](overview.html#buffer-pex).

Next: physically integrate the blocks with supply/ground and signal routing, then extract that combined layout. Pad/ESD and external interface design remain separate work.
