# Proposed unused-pad termination — 24 September 2026

**Simulation proposal; not incorporated into the released bond map or carrier.** The existing [connection table](../hardware/carrier/die-connections.csv) leaves P10, P11, P12 and P15 unbonded. The full-camera cold cases could not establish a stock DC operating point with those nodes floating. Isolated controls reproduced the singular-matrix warning at the protected unused pad.

The follow-up testbench gives each of these pads its own explicit 100 kΩ path to sensor ground:

| Die pad | Extracted node | Existing connection | Proposed test condition |
|---|---|---|---|
| P10 | NC_P10 | Unbonded | 100 kΩ to GND |
| P11 | NC_P11 | Unbonded | 100 kΩ to GND |
| P12 | NC_P12 | Unbonded | 100 kΩ to GND |
| P15 | NC_P15 | Unbonded | 100 kΩ to GND |

The full stock nonlinear-capacitor model then finds its cold DC point without the singular warning or transient-assisted OP fallback. The resistor paths remain present throughout capacitor recalculation, imaging and matched DC references. This changes a physical boundary condition; it is not proof that the original floating circuit is qualified or defective.

## Physical implementation needed before adopting the result

A carrier implementation needs four reviewed bond connections and four local resistors/routes to the sensor return. Confirm available bond landings, routing space, optical clearance and the pad/bond map. Update the native carrier schematic/PCB, BOM and connection table, and rerun the affected board/connection checks. The existing carrier files are still the original unbonded-pad version.

An on-chip termination would instead change the die circuit/layout and require new extraction, DRC/LVS and associated electrical checks. Neither implementation is silently selected by the simulations.

Cold normal-operation repeatability and timestep checks are recorded in [the follow-up report](readout-followup.md). Nonlinear startup/protection and full distributed R+C remain separate open gates. Final manufacturing/pad review must include the selected unused-pad treatment.
