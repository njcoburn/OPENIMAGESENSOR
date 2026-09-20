# ADC choice and slow bench readout

## ADS1115: useful for characterization, too slow for the existing timing

The ADS1115 provides programmable conversion rates up to 860 samples/s. One conversion then takes approximately 1.16 ms. This does not fit the sensor's current 18 µs column slots. Its input range setting does not permit input pins to exceed their supply limits. Start with single-ended AIN0, address 0x48 and ±4.096 V full-scale selection on the 3.3 V board, after confirming the signal stays inside the valid input limits. See the [TI ADS1115 datasheet](https://www.ti.com/lit/ds/symlink/ads1115.pdf).

The following are arithmetic throughput ceilings, **not demonstrated camera frame rates**:

| Array | One conversion/pixel at 860 SPS | Reset + signal conversions/pixel |
|---|---:|---:|
| 3 × 3 | 95.6 frames/s | 47.8 frames/s |
| 64 × 64 | 0.210 frames/s | 0.105 frames/s |

Real operation adds integration, settling, I²C transactions and controller overhead. More importantly, the 3T sensing node continues integrating during conversion. A reading reflects the converter's time-dependent response to that changing voltage; it is not an instantaneous sample. Reset/signal subtraction also requires its own validated timing and noise interpretation.

## Proposed slow characterization sequence

1. Power up with output drivers disabled and defined chip-side pulls. Establish all controller levels before enabling outputs; validate supply/reset startup on the bench.
2. Reset the selected row, release reset and allow a controlled integration interval.
3. Select one row and one column. Wait for verified analog settling, then start a single-shot ADC conversion.
4. Hold the selection constant until conversion-ready, with a timeout in firmware. Record the reset, selection and conversion timestamps with the raw ADC code.
5. Reduce illumination or exposure as needed to avoid saturation during the complete measurement window. Repeat with the same schedule for dark and illuminated measurements.
6. Confirm this sequence in simulation/measurement before interpreting full images. For comparison between pixels, use controlled repeated exposures or account for their different acquisition times.

The board's OPA2320 stage and RC network are candidates for isolating the sensor from the ADC load. Stability and settling have not yet been simulated or measured for this PCB. The amplifier selection uses TI's [OPA320/OPA2320 datasheet](https://www.ti.com/lit/ds/symlink/opa320.pdf); timing-buffer behavior must also be checked against the [SN74LVC244A datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf).

For a future 64 × 64 camera at 30 fps, at least 122,880 pixel conversions/s are required before overhead (245,760 for two conversions per pixel). Choose a faster ADC and validate its acquisition load before scaling. The analog expansion header lets us evaluate that converter while retaining the removable carrier.
