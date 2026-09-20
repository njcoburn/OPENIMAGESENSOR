"""Publish scoped functional-camera results without changing qualification gates."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json,shutil,html,re
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('run');args=p.parse_args();D=R/'build/functional-camera'/args.run
r=json.loads((D/'result.json').read_text());stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
op=json.loads((R/'build/functional-camera/op-100ns/result.json').read_text())
text=f'''# Final filled 3×3: normal-operation simulation candidate

Updated {stamp}.

The stock-model DC operating point completes with every final-chip device and the condensed wiring capacitance retained. Initial voltage guesses (`.nodeset`, released during the DC solve) resolve floating unused-pad initialization. No external resistor or device was added to the chip model.

- Settled supply: {op['summary']['last_values'][0]:.6f} V.
- Supply current: {-op['summary']['last_values'][7]*1e6:.3f} µA.
- All 16 MOS-capacitor terminal pairs settle near 3.30 V.

For the transient candidate, 1,680 nonlinear MOS capacitors are replaced by their capacitance at that measured bias. The typical foundry equation is `C(V) = area × (0.001107 + 0.00107 tanh(6.25 V − 4.1875))`. Every other netlist record is preserved. This approximation must remain valid throughout the run; it is not suitable for a supply ramp.

## Latest run: {args.run}

Completed: **{r['completed']}**. Integration: {r.get('method','trap')}. Maximum timestep: {r['step_ns']:g} ns; ngspice also uses smaller adaptive steps. Typical process, 27 °C, constant 3.3 V source with 2 Ω series resistance. Three illumination levels: 0, 80 and 240 pA. External load: bond model, 100 Ω isolation, 100 pF board capacitance, 1 MΩ input and 20 pF sampled capacitor.

'''
if r['completed']:
 a=json.loads((D/'analysis.json').read_text());worst=max(c['max_relative_C_error'] for c in a['cap_checks']);minimum=min(c['min_V'] for c in a['cap_checks']);maximum=max(c['max_V'] for c in a['cap_checks'])
 text+=f'''| Diagnostic | Result |
|---|---:|
| Brightness ordering in every row | {a['brightness_order_ok']} |
| MOS-cap voltage range | {minimum:.6f}–{maximum:.6f} V |
| Maximum relative C(V) deviation | {worst:.3g} |
| C(V) deviation below 1 ppm | {a['cap_range_pass']} |
| Initial seven voltage outputs vs stock DC OP | {a['stock_op_max_voltage_difference_V']:.3g} V maximum difference |
| Maximum sample/hold minus simultaneous ADC input | {a['max_hold_minus_adc_mV']:.6f} mV |

The last quantity is only an acquisition diagnostic. It does not measure output settling against a DC transfer reference, ADC conversion accuracy, or final sampling margin.

![Final-chip functional candidate](assets/functional-camera.png)

| Frame | Row | Column | Light (pA) | Held output (V) |
|---:|---:|---:|---:|---:|
'''
 for s in a['samples']:text+=f"| {s['frame']+1} | {s['row']+1} | {s['col']+1} | {s['light_pA']} | {s['hold_V']:.6f} |\n"
 shutil.copyfile(D/'response.png',R/'docs/assets/functional-camera.png')
 shutil.copyfile(D/'analysis.json',R/'simulations/functional-camera.json')
else:text+=f"Run stopped: {r.get('stop_reason', r['error'])} No frame result accepted.\n"
text+='''
## Scope and next steps

This is a nominal **functional candidate**, not complete-chip electrical qualification. The earlier startup gate remains failed; no signoff threshold has been relaxed. The 100 ns preliminary frame was deliberately stopped after its measured runtime projected beyond the watchdog; its saved result is not a solver-convergence failure. The 5 µs trapezoidal run was stopped after persistent time stagnation at the second row turn-off (about 3.23002 ms). Gear integration is a controlled numerical comparison with unchanged device models and tolerances; it still needs timestep refinement.

1. First isolate the row-switching stagnation with a short, incrementally saved transient and matched circuit controls. Neither trap nor Gear has completed this frame, so no capacitor-range or imaging pass is claimed. Once a frame completes, refine the timestep and compare all nine held voltages; run three repeated frames and measure frame-to-frame stability.
2. Establish a matched DC transfer reference for settling error, then check load and process/voltage/temperature variations. Recompute and validate the MOS-cap approximation at each bias/corner.
3. Resolve the nonlinear protection/startup model separately; retain the stock pad geometry and devices.
4. Complete distributed wiring-resistance qualification and the board/ADC-specific conversion sequence. The fast sample fixture is not an ADS1115 model.

## Reproduction

```sh
python3 scripts/prepare-functional-pad-model.py
bash scripts/run-tools.sh python3 scripts/simulate-functional-camera.py op
python3 scripts/freeze-functional-pad-model.py
'''+f'bash scripts/run-tools.sh python3 scripts/simulate-functional-camera.py frame --step-ns {r["step_ns"]:g} --method {r.get("method","trap")}\n'+f'bash scripts/run-tools.sh python3 scripts/analyze-functional-camera.py {args.run}\n'+f'python3 scripts/report-functional-camera.py {args.run}\n'+'''```

Runs refuse to overwrite existing result files. Restore the final filled capacitance extraction first; see the preceding electrical checkpoints. The evidence archive includes decks, waveforms, logs, node aliases, stock OP and capacitor replacement provenance.
'''
(R/'docs/functional-camera.md').write_text(text)
summary='Nominal frame completed; refinement and full qualification remain open.' if r['completed'] else 'Nominal frame attempt did not complete; qualification remains open.'
section=f'<section id="functional-camera"><h2>Final filled 3×3: normal-operation candidate</h2><p>{stamp}. <strong>{summary}</strong></p><p>Stock-model DC bias passes. The transient candidate freezes only the 1,680 MOS capacitors at their measured settled bias, preserving all other devices and extracted lumped wiring capacitance. Startup, PVT, distributed wire resistance and ADC-specific qualification remain separate.</p>'
if r['completed']:
 section+=f'<p>Brightness ordering: {a["brightness_order_ok"]}. Capacitor-range check: {a["cap_range_pass"]}. Maximum C(V) deviation: {worst:.3g}. This is a {r["step_ns"]:g} ns maximum-step screen, awaiting refinement.</p><img src="assets/functional-camera.png" alt="Nominal final-chip output scan and capacitor voltages" style="max-width:100%">'
 section+='<table><thead><tr><th>Frame</th><th>Row / column</th><th>Light (pA)</th><th>Held output (V)</th></tr></thead><tbody>'
 for sample in a['samples']:section+=f'<tr><td>{sample["frame"]+1}</td><td>{sample["row"]+1} / {sample["col"]+1}</td><td>{sample["light_pA"]}</td><td>{sample["hold_V"]:.6f}</td></tr>'
 section+='</tbody></table><p>Next: timestep refinement and repeated frames, then matched transfer-reference settling and load/PVT checks. Full startup and distributed-resistance qualification remain open.</p>'
section+='<p><a href="functional-camera.md">Results, limits and reproduction</a> · <a href="#gf180-shuttle-references">Published GF180 project references</a></p></section>'
if not r['completed']:
 section=section.replace('</section>','<p><strong>Remaining issue:</strong> both integration methods stopped advancing at row-switching edges (trap: about 3.23002 ms; Gear: about 3.17001 ms). Runs were stopped manually and retained. No full-frame waveform or capacitance-range validation is available. Next: isolate the switching edge with incrementally saved waveforms and matched circuit controls.</p></section>')
(R/'docs/functional-camera-section.html').write_text(section)
overview=R/'docs/overview.html';s=overview.read_text()
if 'id="functional-camera"' in s:s=re.sub(r'<section id="functional-camera">.*?</section>',section,s,count=1,flags=re.S)
else:s=s.replace('</main>',section+'</main>',1)
overview.write_text(s)
nextfile=R/'NEXT_STEPS.md';s=nextfile.read_text();heading=s.split('\n',1)[0];s=s.replace(heading,heading+f'\n\n## Normal-operation candidate — {stamp}\n\n{summary} Stock-model DC bias passes with unused-pad initial guesses. See [results and exact next checks](docs/functional-camera.md). No hardware decision is needed for the next simulation checks.\n',1);nextfile.write_text(s)
print(summary)
