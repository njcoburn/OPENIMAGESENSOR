# Heavy-load readout interface proposal — 24 September 2026

**A tested simulation candidate, not an adopted hardware revision.** The existing board/bond files and nominal regression remain the baseline. The proposal below is intended to support the 470 pF board / 100 pF reset sampling-capacitor stress load. The actual ADC and board capacitance must determine whether this higher-drive mode is necessary.

| Item | Existing regression / carrier value | Proposed heavy-load mode |
|---|---|---|
| Carrier R2, PREF-to-ground resistance | 49.9 kΩ | 12.4 kΩ |
| Unused P10/P11/P12/P15 pads | Unbonded | Each connected to GND through 100 kΩ |
| Column slot | 18 µs | 50 µs |
| Acquisition duration | 5 µs | 30 µs |
| First row-select edge | 2.170 ms | 2.060 ms |
| First acquisition window | 2.180–2.185 ms | 2.075–2.105 ms |
| Selected row width | 60 µs | 160 µs |
| Reset/illumination history | Existing sequence | Preserved |

Rows still repeat every 1 ms and frames every 3 ms in this nine-pixel fixture. Later readout rows/frames add the corresponding 1 ms / 3 ms offsets. Column selection begins 10 µs before acquisition and remains on beyond sampling; the three-column readout finishes before the next row-reset event. The change shifts exposure/sample times and increases inter-column exposure skew, so old output samples are not a transfer reference for the new timing.

## Measured motivation and tradeoff

The heavy-load fast fixture missed its 0.5 mV tracking screen by about 349 mV. Slower timing alone reduces the error to 0.759 mV. With slower timing, 24.9 kΩ and 16.5 kΩ PREF candidates reach 0.578 mV and 0.503 mV; both remain failures. The 12.4 kΩ combined proposal reaches 0.461 mV in its finer-step first-frame check. Three-frame and refinement outcomes are recorded in the [follow-up report](readout-followup.md); do not infer broader corner coverage from the nominal heavy-load result.

Initial DC supply current rises from approximately 80.4 µA to 248.3 µA, or from about 0.265 mW to 0.819 mW at the 3.3 V source. These figures exclude the external controller/ADC and are not full-frame peak/average measurements. Increased bias changes the analog transfer curve; matching DC references are recomputed rather than reusing a room-temperature calibration.

## Work needed before hardware adoption

Review the actual ADC input circuit, board capacitance and required frame rate first. If this mode is selected, update carrier R2 (currently 49.9 kΩ) and the BOM, implement the [unused-pad connections](unused-pad-termination-proposal.md), and implement the complete controller schedule rather than changing acquisition width in isolation. Rerun the relevant board/bond checks and the combined interface across the required load/PVT range. The generic switched-capacitor fixture does not implement an ADS1115 conversion.

Startup/protection, full distributed wire R+C and final manufacturing/optical-package checks remain open. This is separate from designing a larger array's addressing, physical interconnect and exposure/readout architecture; see [tapeout readiness](tapeout-readiness.md).
