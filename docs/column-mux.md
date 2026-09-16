# Step 2 — column multiplexer and standalone readout layout

The 3:1 NMOS multiplexer connects the three columns in sequence to one output. Its switches use GF180 `nfet_03v3`, W/L 1/0.5 µm, with bulk grounded. The four bias mirror transistors retain W/L 2/2 µm and an ideal 0.5 µA reference. The gate drive is 3.3 V; suitability is limited to the tested column voltage range, not rail-to-rail signals.

Each selection lasts 16 µs, followed by a 2 µs gap. Sampling 10 µs after selection gives less than 0.004 mV output-to-selected-column difference across all nine samples. The notebook separately reports column disturbance against the no-mux waveform. This local tracking result is not an ADC resolution or total settling specification. Optical integration continues, and the three samples occur at different exposure times.

The load is 1 pF with 1 GΩ leakage. Actual ADC sampling capacitance, switching kickback, PCB and package loading remain for the output-buffer stage. Ideal timing sources provide the select sequence; decoder/control hardware has not been designed.

## Physical layout

`layout/readout.py` builds a separate seven-transistor block using GF180 Magic primitives and gdsfactory routing. From left to right: reference transistor, three sinks, three mux switches. BIAS is an external reference-current connection. No VDD terminal is needed inside this NMOS-only block; the external reference source supplies BIAS.

The independent reference circuit is `layout/column_readout.spice`. Magic extracts the routed block for Netgen comparison; both Magic and the full GF180 KLayout DRC deck check the final filled GDS. Density fill extends around the wiring as a standalone verification region; this is not an optimized camera-floorplan allocation. Integrating the block with the array will require rerouting, density recalculation and renewed checks.

The readout devices are schematic models in the current transient test, while the pixel array includes extracted RC. The newly laid-out readout wiring and fill have not yet been extracted for simulation. DRC/LVS of this separate block does not verify a combined camera or optical package.

## Reproduce

With the existing project checkpoint restored:

```bash
# Generate the bias reference testbench if missing:
bash scripts/run-tools.sh python3 scripts/column-bias.py
bash scripts/run-tools.sh python3 scripts/column-mux.py
bash scripts/run-tools.sh bash scripts/build-readout.sh
bash scripts/run-tools.sh klayout -b -r scripts/report-readout.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The layout build uses the verified pixel NFET primitive from the restored checkpoint. The report script fails unless both DRC counts are zero and LVS matches uniquely. It saves the exact final GDS and reports under `checkpoints/readout/` and records the GDS hash in `simulations/readout-verification.json`. Mux waveforms and generated testbench are under `build/column-mux/`; the summary is `simulations/column-mux.json`.

Next extract the readout block and repeat the combined electrical simulation, then add a shared output buffer and realistic external load models.

## Follow-up: extracted readout simulation

The separately extracted array and readout now run together. See the latest notebook section `#readout-pex`, `simulations/readout-pex.json`, and the compact models in `checkpoints/readout/pex/`.

```bash
bash scripts/run-tools.sh bash scripts/run-readout-pex.sh
```

**Qualification:** Magic's RC capacitance redistribution produced one negative shunt, −3.52353 fF at `BIAS.n0`. The raw capacitance matrix failed the nonnegative-eigenvalue check. The comparison model preserves the signed sum of all BIAS-to-global-ground shunts at the BIAS port, retaining every extracted resistor and all coupling capacitances. This is an approximation to spatial capacitance distribution along BIAS, not a pristine distributed-RC extraction. A sensitivity variant puts that same total at the reference gate instead. The negative value is not simply clipped or omitted.

The adjusted capacitance network then undergoes floating-node reduction with solve-residual, charge/energy, symmetry, eigenvalue and truncation checks. LVS is performed on extracted devices with resistors shorted and capacitors omitted. A device-only simulation control and a smaller-step/tighter-tolerance RC run check the comparison numerically. Tiny changes comparable to the numerical-refinement difference should not be assigned physical significance.

Both blocks connect with ideal inter-block wires. There is no extracted common physical supply network or routing between blocks, no output buffer, pads/ESD, package or ADC input model. The existing individual GDS files are unchanged; prior DRC/LVS applies to those separate blocks only.
