"""Publish audited isolated-column results, keeping transfer shift distinct."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--layout',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'build/capture-column-matrix-v2-20260925')
    a=p.parse_args();runs=a.run.resolve();layout=a.layout.resolve()
    load=lambda path:json.loads(path.read_text())
    result=load(runs/'report.json');baseline=load(a.baseline/'report.json')
    audit=load(runs/'audit.json');physical=load(layout/'verification.json')
    build=load(layout/'build.json')
    assert all(result[key] for key in ['complete','tracking_pass','timestep_pass','placement_pass','reference_duration_pass'])
    assert audit['all_48_fixtures_match_except_declared_model_temperature_input_step']
    assert physical['magic_drc_errors']==physical['klayout_main_drc_errors']==0
    assert physical['direct_and_resistor_collapsed_lvs']
    assert hashlib.sha256((layout/'direct.spice').read_bytes()).hexdigest()==hashlib.sha256((ROOT/'build/capture-column-v2-20260925/direct.spice').read_bytes()).hexdigest()
    solver_differences={}
    baseline_runs=load(a.baseline/'transients.json')
    for name in ['ideal','physical']:
        klu=load(ROOT/f'build/capture-isolation-20260925/{name}-100/result.json')
        sparse=next(r for r in baseline_runs if (r['model'],r['temperature_C'],r['input_V'],r['step_ns'])==(name,27,1.6,100))
        assert klu['complete'] and sparse['complete']
        solver_differences[name]=max(abs(klu['samples'][slot]['hold']-sparse['samples'][slot]['hold']) for slot in ['first','last'])
    assert max(solver_differences.values())<1e-10
    summary=dict(scope='Isolated seven-transistor/eight-MIM column; typical process at 27/125 C with nominal wire RC; ideal imposed COL/VDD sources and schematic reference/control/ADC fixtures.',
        physical=physical,qualification=result,fixture_audit=audit,
        baseline_maxima=baseline['maxima'],solver_control_differences_V=solver_differences,selected_run=str(runs.relative_to(ROOT)),selected_layout=str(layout.relative_to(ROOT)),
        all_tracking_and_numerical_checks_pass=True,
        schematic_comparison_under_500uV=result['schematic_shift_under_500uV'],
        source_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [runs/'report.json',runs/'audit.json',layout/'verification.json']})
    (ROOT/'simulations/capture-column-qualification.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(3,1,figsize=(10,9),layout='constrained')
    rows=[]
    for temp,color in [(27,'#147d92'),(125,'#b64d44')]:
        values=[r for r in result['comparisons'] if r['temperature_C']==temp]
        old=[r for r in baseline['comparisons'] if r['temperature_C']==temp]
        x=np.arange(len(values));labels=[f"{r['input_V']:g} V\n{r['slot']}" for r in values]
        axes[0].plot(x,[r['rc_minus_ideal_V']*1e6 for r in old],':',color=color,alpha=.65,label=f'{temp} °C original')
        axes[0].plot(x,[r['rc_minus_ideal_V']*1e6 for r in values],'.-',color=color,label=f'{temp} °C revised')
        axes[1].plot(x,[r['rc_tracking_error_V']*1e6 for r in values],'.-',color=color,label=f'{temp} °C')
        axes[2].plot(x,[r['max_timestep_difference_V']*1e6 for r in values],'.-',color=color,label=f'{temp} °C timestep')
        axes[2].plot(x,[abs(r['placement_difference_V'])*1e6 for r in values],'x--',color=color,label=f'{temp} °C placement')
        maxima={key:max(abs(r[key]) for r in values)*1e6 for key in ['rc_minus_ideal_V','rc_tracking_error_V','max_timestep_difference_V','placement_difference_V']}
        rows.append(f"| {temp} °C | {maxima['rc_tracking_error_V']:.3f} | {maxima['rc_minus_ideal_V']:.3f} | {maxima['max_timestep_difference_V']:.3f} | {maxima['placement_difference_V']:.4f} |")
    for ax,title in zip(axes,['Layout output minus ideal-40 pF schematic','Output minus layout-specific DC reference','Numerical and capacitance-placement differences']):
        ax.set(title=title,ylabel='Difference (µV)',xticks=np.arange(6),xticklabels=labels)
        ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=2)
    for ax in axes[:2]:
        for v in [-500,500]:ax.axhline(v,color='#777',ls='--',lw=.8)
    axes[2].set_yscale('log');axes[2].axhline(10,color='#777',ls='--',lw=.8)
    image=ROOT/'docs/assets/capture-column-qualification.png';fig.savefig(image,dpi=160);plt.close(fig)
    m=result['maxima'];table='\n'.join(rows)
    md=f'''# Physical capture column qualified — 2026-09-25

**The isolated physical column passes the nominal/hot tracking, timestep and
capacitance-placement checks.** All 48 single-model transients finish through
2.7 ms. Worst tracking error is {m['rc_tracking_error_V']*1e6:.3f} µV against
500 µV; 100→50 ns difference is {m['max_timestep_difference_V']*1e6:.3f} µV
against 10 µV. This is a conditional single-column result, not full-array qualification.

| Temperature | Tracking error (µV) | Layout–schematic shift (µV) | Timestep difference (µV) | Placement difference (µV) |
|---|---:|---:|---:|---:|
{table}

![Column transfer, tracking and numerical checks](assets/capture-column-qualification.png)

## What resolved the transient blocker

The schematic column and the physical-capacitor schematic both finish in about
one second when tested alone. KLU completes the resistance-only control but is
very slow with the capacitance-only and full-RC controls. **SPARSE completes the
unchanged full-RC column**, with the original error tolerances. The accepted
workflow runs each model independently, with identical external input, supply,
control sources, reference fixture and ADC load. It does not combine four models
on a shared reference as the earlier failed fixture did.

This establishes solver/fixture sensitivity, not a proven KLU defect or a hardware
failure. The accepted runs retain every extracted resistor and the previously
documented COL-shunt capacitance approximation.
Schematic KLU/SPARSE controls agree within 0.1 nV at the checked nominal point.
Earlier incomplete and failed attempts are preserved separately.

## Physical routing and transfer fidelity

The revised column uses 2 µm supply rails, 1.2 µm current-carrying supply branches,
distributed contact/via landings, and {build['output_width_um']:g} µm buffer/output rails. All seven MOS
devices and eight 64 × 38.880 µm MIM plates are unchanged: the direct-device
netlist is byte-identical to the original column. Magic and KLayout main DRC
report zero errors; both direct and resistor-collapsed LVS match uniquely.
The original cell's largest layout–schematic shift was
{baseline['maxima']['rc_minus_ideal_V']*1e6:.3f} µV; the selected revision's is
{m['rc_minus_ideal_V']*1e6:.3f} µV.

Tracking error and transfer shift are separate measurements. Tracking compares
the transient to an independently solved DC reference **for the same physical
column**, with the capture/mux/acquisition paths closed at the imposed input.
Transfer shift compares its transient output with the ideal-40 pF schematic under
the same external stimulus and bias fixture. The additional 500 µV schematic
comparison screen passes: **{result['schematic_shift_under_500uV']}**.

The supply-only revision's largest shift was 611.384 µV. A 2 µm output-rail
candidate reduced the high-input shift but raised the low-input shift to
580.851 µV. The selected intermediate width balances those measured deviations.
All three routing candidates pass tracking/refinement, but only the selected
revision passes this additional comparison band over the tested input levels.
Its margin to that band is limited; broader process/wire/load corners remain open.

Development routing revisions with DRC failures or an LVS-detected buffer-node
short were excluded. Passing DRC alone did not qualify those candidates.

## Checks and limits

- Typical process; device temperatures 27/125 °C; input levels 1.2/1.6/2.0 V.
- One simultaneous capture, followed by first and last readout slots. Capture at
  1.4 ms, 20 µs slots, 10 µs acquisition, 100 pF board and 20 pF sample loads.
- 500 kΩ BIAS / 12.4 kΩ PREF schematic reference fixture; 100 Ω behavioral
  control drivers. Actual driver and shared reference layout remain open.
- Four independently simulated models per condition: ideal schematic,
  physical-capacitor schematic, extracted RC with near/far COL shunt placement.
- Every transient is finite, time-monotonic and complete; sampled controls pass.
  The audit verifies the actual maximum timesteps and recomputes every sample.
- Thirty-six DC solves use 200/400 µs transient-fallback limits. They converge
  directly, so their equality is **not** a doubled transient-settling test.
- The raw extraction's negative COL-shunt corrections remain archived. Diagnostic
  models retain all {physical['resistors']} resistors, conserve total COL shunt
  capacitance and place its positive sum at either end. Worst sampled sensitivity:
  {m['placement_difference_V']*1e6:.4f} µV. This checks these terminal conditions;
  it is not a general proof that distributed capacitance can always be lumped.
- MIM capacitance/leakage controls from the earlier stage still apply because the
  direct-device netlist is unchanged. The conditional 2 fF option remains
  unselected for manufacturing; its voltage-dependence expressions are inactive.

Both temperatures use nominal wire RC. There is no physical pixel attached to
COL in this fixture, no 64-column shared bus or peripheral supply grid, no
repeated/multirow capture, no noise/mismatch or full startup qualification.
Main DRC excludes antenna/density/CUP; no optical aperture is placed in this cell.
No release GDS, carrier, commit or push changed.

## Next and reproduction

Implement the 64-column bank with physical common supply/return, capture clocks,
bias/reference routes and output bus, then couple it to the already extracted
row. Recheck routing/loading, capture acquisition and all 64 outputs before
multirow operation and real drivers. Frame rate remains undecided.

Selected physical evidence: `{layout.relative_to(ROOT)}`.
Selected electrical evidence: `{runs.relative_to(ROOT)}`.
The earlier matrix remains in `build/capture-column-matrix-v2-20260925`.

```sh
bash scripts/run-tools.sh python3 scripts/qualify-capture-column.py \\
  --extraction {layout.relative_to(ROOT)} --out build/capture-column-new-matrix
bash scripts/run-tools.sh python3 scripts/audit-capture-column-matrix.py \\
  --run build/capture-column-new-matrix
```

Use a fresh output directory. All input models, runner snapshots, successful and
excluded experiments are retained in `checkpoints/capture-column-qualification/`.
Machine-readable results: `simulations/capture-column-qualification.json`.
'''
    (ROOT/'docs/capture-column-qualification.md').write_text(md)
    encoded=base64.b64encode(image.read_bytes()).decode()
    section=f'''<section id="capture-column-qualification"><h2>Physical capture column: qualified isolated operation</h2><p>All 48 transients complete at 27/125 °C. Worst tracking error <b>{m['rc_tracking_error_V']*1e6:.3f} µV</b> / 500 µV; timestep difference <b>{m['max_timestep_difference_V']*1e6:.3f} µV</b> / 10 µV. Revised layout–schematic shift: {m['rc_minus_ideal_V']*1e6:.3f} µV. DRC and both LVS checks pass.</p><p>Independent SPARSE runs resolve the earlier solver/fixture blockage without relaxed tolerances. One column with imposed inputs, typical process and nominal wire RC; shared 64-column routing, actual drivers, multirow operation, noise, startup and manufacturing gates remain open.</p><img alt="Column transfer, tracking and numerical comparisons" src="data:image/png;base64,{encoded}"><p>Next: implement the shared physical bank and repeat full-row readout. <a href="capture-column-qualification.md">Scope and reproduction</a>.</p></section>'''
    (ROOT/'docs/capture-column-qualification-section.html').write_text(section+'\n')
    print(json.dumps(dict(maxima=m,all_tracking_and_numerical_checks_pass=True,schematic_comparison_under_500uV=result['schematic_shift_under_500uV']),indent=2))


if __name__=='__main__':main()
