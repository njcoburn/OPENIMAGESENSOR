"""Audit and report physical bank routing revisions; no transient accuracy claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('routing',ROOT/'scripts/diagnose-bank-routing.py')
routing=importlib.util.module_from_spec(spec);spec.loader.exec_module(routing)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(bank,dc):
    meta=json.loads((bank/'verification.json').read_text())
    assert meta['columns']==64 and meta['direct_and_resistor_collapsed_lvs']
    assert meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0
    for name,digest in meta['hashes'].items():assert sha(bank/name)==digest
    report=json.loads((dc/'report.json').read_text())
    assert report['all_completed'] and len(report['results'])==16
    for name,digest in report['model_sha256'].items():assert sha(dc/(name+'.spice'))==digest
    assert report['model_sha256']['rc-port']==meta['hashes']['rc-port.spice']
    expected=(bank/'reference.spice').read_text().replace('.subckt reference ','.subckt bank ').replace('.ends reference','.ends bank')
    assert (dc/'reference.spice').read_text()==expected
    lookup={}
    for r in report['results']:
        d=dc/f"{r['model']}-{r['temperature_C']}-{r['input_V']:g}"
        assert r['completed'] and not r['timed_out'] and r['returncode']==0 and not r['errors']
        assert sha(d/'test.spice')==r['deck_sha256']
        assert routing.read_op(d/'op.raw')==r['values']
        assert 'Transient op started' not in (d/'ngspice.log').read_text()
        key=(r['model'],r['temperature_C'],r['input_V'])
        assert key not in lookup
        lookup[key]=r
    assert set(lookup)=={(m,t,v) for m in ['reference','rc-port'] for t in [27,125] for v in [0,1.2,1.6,2]}
    rows=[]
    for t in [27,125]:
        for v in [0,1.2,1.6,2]:
            physical=lookup['rc-port',t,v]['values'];ideal=lookup['reference',t,v]['values']
            shifts=[physical[f'v(cbuf{c})']-ideal[f'v(cbuf{c})'] for c in range(64)]
            saved=next(r for r in report['comparisons'] if r['temperature_C']==t and r['input_V']==v)
            assert shifts==saved['buffer_shifts_V']
            assert max(map(abs,shifts))==saved['max_buffer_shift_V']
            def value(n):
                if n=='GND':return 0.0
                key='v('+ (n if n in ['VDD','BIAS','PREF'] or re.fullmatch(r'(COL|STORE|CBUF|SEL|SELB)\d+',n) else 'xbank.'+n).lower()+')'
                return physical[key]
            drops=[physical['v(vdd)']-value(role['follower']['body']) for role in meta['roles'].values()]
            rises=[value(role['follower']['drain']) for role in meta['roles'].values()]
            rows.append(dict(temperature_C=t,input_V=v,max_buffer_shift_V=max(map(abs,shifts)),
                             buffer_shift_span_V=max(shifts)-min(shifts),buffer_shifts_V=shifts,
                             max_local_vdd_drop_V=max(drops),max_local_ground_rise_V=max(rises)))
    return dict(bank=str(bank.relative_to(ROOT)),dc=str(dc.relative_to(ROOT)),physical=meta,
                rows=rows,all_16_raw_records_verified=True,
                hashes={'verification.json':sha(bank/'verification.json'),'dc-report.json':sha(dc/'report.json')})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank',type=Path,required=True);p.add_argument('--dc',type=Path,required=True)
    p.add_argument('--intermediate-bank',type=Path,required=True);p.add_argument('--intermediate-dc',type=Path,required=True)
    p.add_argument('--controls',type=Path,required=True);p.add_argument('--reset',type=Path)
    a=p.parse_args()
    banks=[ROOT/'build/capture-bank-c64-v2-20260925',a.intermediate_bank.resolve(),a.bank.resolve()]
    dcs=[ROOT/'build/capture-bank-dc-matrix-20260925',a.intermediate_dc.resolve(),a.dc.resolve()]
    designs=[audit(b,d) for b,d in zip(banks,dcs)]
    # Physical revisions retain the exact independently specified device contract.
    assert len({(b/'reference.spice').read_text() for b in banks})==1
    for dc in dcs[1:]:
        for t in [27,125]:
            for v in [0,1.2,1.6,2]:
                for model in ['reference','rc-port']:
                    def fixture(d):
                        text=(d/f'{model}-{t}-{v:g}'/'test.spice').read_text()
                        return ['.include BANK_MODEL' if l.startswith('.include ') and l.endswith('/'+model+'.spice') else l
                                for l in text.splitlines() if not l.startswith('.save ')]
                    assert fixture(dc)==fixture(dcs[0])
                original=routing.read_op(dcs[0]/f'reference-{t}-{v:g}'/'op.raw')
                assert routing.read_op(dc/f'reference-{t}-{v:g}'/'op.raw')==original
    controls=json.loads((a.controls/'report.json').read_text())
    expected_controls={'full','vdd','ground','supplies','bias','pref','references',
                       'supplies-references','all-wire-nets'}|{
                           'supplies-references-'+n for n in ['col','store','cbuf','buf']}
    assert len(controls['controls'])==13
    assert {r['name'] for r in controls['controls']}==expected_controls
    source=(a.controls/'original-model.spice').read_text()
    assert source==(banks[0]/'rc-port.spice').read_text()
    local=[]
    ideal=routing.read_op(dcs[0]/'reference-27-1.2/op.raw')
    for r in controls['controls']:
        d=a.controls/r['name']
        assert r['completed'] and not r['timed_out'] and not r['transient_assisted_initialization']
        assert sha(d/'model.spice')==r['model_sha256'] and sha(d/'test.spice')==r['deck_sha256']
        assert routing.read_op(d/'op.raw')==r['values']
        model,_,check=routing.collapse(source,r['selected_nets'])
        assert model==(d/'model.spice').read_text()
        assert all(r[k]==v for k,v in check.items())
        original=(a.controls/'original-deck.spice').read_text()
        deck=(d/'test.spice').read_text()
        assert [l for l in original.splitlines() if not l.startswith(('.include ','.save '))]==[l for l in deck.splitlines() if not l.startswith(('.include ','.save '))]
        original_includes=[l for l in original.splitlines() if l.startswith('.include ') and not l.endswith('/rc-port.spice')]
        assert original_includes==[l for l in deck.splitlines() if l.startswith('.include ') and l!='.include model.spice']
        shifts=[r['values'][f'v(cbuf{c})']-ideal[f'v(cbuf{c})'] for c in range(64)]
        assert shifts==r['buffer_shifts_V']
        if r['name']=='all-wire-nets':assert max(map(abs,shifts))<1e-12
        if r['name']=='full':assert r['values']==routing.read_op(dcs[0]/'rc-port-27-1.2/op.raw')
        local.append(dict(name=r['name'],max_abs_buffer_shift_V=max(map(abs,shifts)),
                          selected_nets=r['selected_nets'],device_parameters_preserved=True))
    reset=None
    if a.reset:
        reset=json.loads((a.reset/'result.json').read_text())
        assert 'timed_out' in reset
        for name,digest in reset['source_sha256'].items():assert sha(a.reset/name)==digest
        assert sha(a.reset/'bank.spice')==designs[-1]['physical']['hashes'][reset['model']+'.spice']
        original=(a.reset/'original-fixture.spice').read_text()
        deck=(a.reset/'test.spice').read_text()
        for line in original.split('.save ',1)[0].splitlines():
            f=line.split()
            if not f or f[0] in ['.include','.temp'] or line in reset['removed_fixture_elements']:continue
            assert line.replace('method=trap','method='+reset['method']) in deck.splitlines()
        assert len(reset['removed_fixture_elements'])==514
    summary=dict(designs=designs,local_controls=local,reset=reset,
                 unchanged_device_contract=True,unchanged_dc_fixture=True,
                 reference_results_bit_exact=True,full_readout_accuracy_qualified=False)
    (ROOT/'simulations/bank-reinforcement.json').write_text(json.dumps(summary,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,t in zip(axes,[27,125]):
        for design,label in zip(designs,['Original','Supply/reference revision','Plus local buffer revision']):
            r=next(r for r in design['rows'] if r['temperature_C']==t and r['input_V']==1.2)
            ax.plot(range(64),[v*1e3 for v in r['buffer_shifts_V']],label=label)
        ax.axhline(0,color='#777',lw=.7);ax.grid(alpha=.2)
        ax.set(xlabel='Column',ylabel='Physical − ideal buffer (mV)',title=f'{t} °C, uniform 1.2 V inputs')
    axes[0].legend(fontsize=8)
    fig.suptitle('Physical bank routing revisions — static controls, not readout qualification')
    fig.savefig(ROOT/'docs/assets/bank-reinforcement.png',dpi=160);plt.close(fig)
    table=['| °C | COL (V) | Original shift (mV) | Supply/reference shift (mV) | Selected shift (mV) | Selected span (mV) |',
           '|---|---|---|---|---|---|']
    for old,mid,new in zip(*(d['rows'] for d in designs)):
        table.append(f"| {new['temperature_C']} | {new['input_V']:g} | {old['max_buffer_shift_V']*1e3:.6f} | {mid['max_buffer_shift_V']*1e3:.6f} | {new['max_buffer_shift_V']*1e3:.6f} | {new['buffer_shift_span_V']*1e3:.6f} |")
    physical=designs[-1]['physical']
    worst=[max(r['max_buffer_shift_V'] for r in d['rows'] if r['input_V']>0)*1e3 for d in designs]
    reset_text='No revised coupled transient was run.'
    if reset:
        reset_text=(f"The selected bank's {reset['temperature_C']:g} °C / {reset['step_ns']:g} ns "
            f"coupled reset control requested {reset['stop_ms']:g} ms and used {reset['seconds']:.1f} s. "
            f"Completed: **{reset['completed']}**; timed out: **{reset['timed_out']}**; "
            f"complete readout samples: **{len(reset.get('samples',[]))}**. "
            +(f"Last retained time: **{reset['last_time_s']*1e3:.9f} ms**. " if 'last_time_s' in reset else 'No complete transient records. ')
            +'This bounded control does not establish capture or output accuracy.')
    md=f'''# Physical bank routing reinforcement — 2026-09-25

**The revised 64-column bank passes both main DRC checks and both LVS paths.**
Across the eight nominal/hot DC conditions, all 16 selected-bank runs complete.
Within the 1.2–2.0 V screen, the largest physical–ideal static buffer shift changes
from **{worst[0]:.6f} mV** to **{worst[2]:.6f} mV**. Full readout qualification remains open.

![Measured physical routing comparison](assets/bank-reinforcement.png)

## Physical changes and checks

The supply/reference revision uses nine parallel 8 µm M5 straps per supply,
M4/M5 column supply uprights with distributed 3×3 vias, reinforced reference
source connections, and BIAS/PREF external feeds beside the reference devices.
This increases routing height by 80 µm. The final revision also adds a 2 µm M4
CBUF rail and parallel 1.2 µm M2 branches at each mirror drain/follower source,
with distributed vias. Existing signal/control wires and devices remain present.

Two-column controls and both 64-column revisions pass Magic/KLayout main DRC
and direct/resistor-collapsed LVS. An earlier two-column attempt failed M1/M2
spacing around the reference transistor; its geometry and reports are retained.
The selected bank retains {physical['mos']} MOS devices, {physical['mim_devices']}
MIM plates and {physical['distinct_connected_ports']} distinct connected ports.
Extraction contains {physical['resistors']} resistors and
{physical['parasitic_capacitors']} parasitic capacitors. Device parameters and
schematic contracts match the original bank exactly. Main DRC still excludes
antenna, density and CUP; manufacturing qualification is open.

## Static electrical comparison

Each cell below is the largest absolute physical–ideal CBUF difference among
all 64 columns. Span is the range of those signed differences. Independent raw
readback verifies all 48 baseline/intermediate/selected DC records. Fixtures,
solver tolerances, loads and transistor models are unchanged; all ideal-wire
reference results reproduce exactly. Zero input is a separate reset diagnostic.

{chr(10).join(table)}

The external supply remains 3.3 V through 2 Ω; bias resistors remain
500 kΩ/12.4 kΩ. These imposed-column DC results are not matched camera output
errors, noise measurements, calibration evidence or full-row qualification.
Local VDD/ground measurements for every condition are in the JSON report.
The buffer revision improves the overall worst case, but the intermediate
supply/reference-only layout has smaller absolute shifts at 1.6 and 2.0 V.
Removing one offset can expose another of opposite sign; the changes are not
uniform improvements at every input. Residual spread and systematic shifts
still require investigation before any accuracy claim.

## Common-offset diagnosis

Thirteen baseline wire-contraction controls complete. After supply/reference
contraction, additionally contracting CBUF reduces the largest offset from
2.199456 mV to 0.015255 mV. Contracting COL instead leaves 2.214677 mV;
STORE/BUF contractions have negligible effect. Contracting all wire networks
matches the ideal reference within 0.9 fV. Device parameters are preserved.
This identifies the local buffer current path as the main remaining common
DC-offset contributor in the tested 27 °C / 1.2 V control. It is not a universal
correction or a transient accuracy result. The physical CBUF revision is tested
separately above.

## Coupled runtime and remaining gates

{reset_text}

Raw negative substrate-shunt corrections remain archived. The derived port/far
placements conserve net totals and all resistors; their sensitivity requires new
qualification. The row/bank joins remain ideal terminal connections. Continue
with residual supply/reference spread and coupled solver behavior, followed by
independent capture/output targets, all 64 matched samples, nominal/hot timestep
and placement comparisons. Physical joining routes, multirow capture, real
drivers, wire/process corners, startup, noise and manufacturing gates remain open.

## Reproduce

Selected layout: `{designs[-1]['bank']}`.
Intermediate layout: `{designs[1]['bank']}`. Use fresh output directories:

```sh
bash scripts/run-tools.sh python3 scripts/build-capture-bank.py \\
  --columns 64 --reinforced-routing --reinforced-buffer --out build/bank-new
bash scripts/run-tools.sh bash -lc 'cd build/bank-new && klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=bank.gds -rd report=main-drc.lyrdb -rd topcell=capture_bank -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > klayout.log 2>&1'
bash scripts/run-tools.sh python3 scripts/verify-capture-bank.py --run build/bank-new
bash scripts/run-tools.sh python3 scripts/screen-capture-bank-dc.py \\
  --bank build/bank-new --out build/bank-new-dc --levels 0 1.2 1.6 2 --timeout 60
```

Omit `--reinforced-buffer` for the intermediate control; omit both reinforcement
flags to retain the original routing configuration. Machine-readable results:
`simulations/bank-reinforcement.json`. Evidence: `checkpoints/bank-reinforcement/`.
Earlier checkpoints are unchanged. No release GDS, carrier, commit or push changed.
'''
    (ROOT/'docs/bank-reinforcement.md').write_text(md)
    import base64
    encoded=base64.b64encode((ROOT/'docs/assets/bank-reinforcement.png').read_bytes()).decode()
    (ROOT/'docs/bank-reinforcement-section.html').write_text(f'<section id="bank-reinforcement"><h2>Physical bank routing reinforcement</h2><p>Both main DRC checks and both LVS paths pass. Largest static buffer shift within 1.2–2.0 V: {worst[0]:.3f} → {worst[2]:.3f} mV. Full readout remains unqualified.</p><img alt="Static bank routing comparison" src="data:image/png;base64,{encoded}" style="max-width:100%"><p><a href="bank-reinforcement.md">Measurements, scope and reproduction</a></p></section>\n')
    print(json.dumps(dict(static_max_shift_mV=worst,dc_records_verified=48,local_controls=len(local),reset_completed=reset['completed'] if reset else None)))


if __name__=='__main__':main()
