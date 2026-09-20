"""Build an unsent, portable startup reproducer; no further experiments."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil,json,hashlib,tarfile
R=Path(__file__).resolve().parents[1];B=R/'build/bounded-solver';C=R/'checkpoints/clamp-review';P=C/'package';P.mkdir(parents=True,exist_ok=True)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
s=json.loads((B/'summary.json').read_text());assert len(s['runs'])==2
cases={'capacitor-control':'build/moscap-branch/small-n1-r1000-False-False','klu-gear-100ns':'build/moscap-branch/clamp-localFalse-smoothFalse','klu-trap-100ns':'build/moscap-branch/integration-trapezoidal','klu-trap-50ns':'build/moscap-branch/trap-halfstep','klu-trap-50ns-strict':'build/moscap-branch/trap-halfstep-strict','sparse-trap-50ns':'build/bounded-solver/trap-halfstep','sparse-trap-50ns-strict':'build/bounded-solver/trap-halfstep-strict'}
origins={}
for name,origin in cases.items():
 d=P/'cases'/name;d.mkdir(parents=True,exist_ok=True)
 for filename in ['test.spice','ngspice.log','tran.dat']:
  src=R/origin/filename
  if src.exists():shutil.copy2(src,d/filename)
 origins[name]=origin
(P/'init').mkdir(exist_ok=True);shutil.copy2(R/'checkpoints/pad-closure/ngspice-init/.spiceinit',P/'init/.spiceinit')
for src,dest in [('build/bounded-solver/summary.json','bounded-result.json'),('build/moscap-branch/isolation.json','isolation.json'),('build/moscap-branch/pdk-provenance.json','pdk-provenance.json'),('scripts/run-tools.sh','repository-run-tools.sh')]:shutil.copy2(R/src,P/dest)
(P/'run.py').write_text('''"""Replay one case, preserving the archived evidence. Requires ngspice and GF180 PDK."""
from pathlib import Path
import argparse,subprocess,os,re,shutil,json
p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--timeout',type=int,default=120);a=p.parse_args()
r=Path(__file__).resolve().parent
assert a.case in [x.name for x in (r/'cases').iterdir() if x.is_dir()]
d=r/'replay'/a.case;d.mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'cases'/a.case/'test.spice',d/'test.spice');(d/'tran.dat').unlink(missing_ok=True)
result={'completed':False}
try:
 with (d/'ngspice.log').open('w') as log:
  proc=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout,env={**os.environ,'SPICE_USERINIT_DIR':str(r/'init')})
 text=(d/'ngspice.log').read_text()
 assert proc.returncode==0 and not re.search('aborted|timestep too small|^Error',text,re.I|re.M)
 lines=(d/'tran.dat').read_text().splitlines()[1:]
 assert len(lines)>1 and float(lines[-1].split()[0])>=152.99e-6
 result['completed']=True
except Exception as e:result['failure']=str(e)
(d/'result.json').write_text(json.dumps(result,indent=2)+'\\n');print(result)
raise SystemExit(0 if result['completed'] else 1)
''')
image='hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a'
(P/'README.md').write_text(f'''# GF180 extracted-clamp transient reproducer

Prepared {stamp}; **not sent**. See the accompanying review brief. The PDK is not redistributed; the decks include the installed GF180MCU D models at `/foss/pdks/gf180mcuD/libs.tech/ngspice`.

From this extracted package directory, with Docker available:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work --entrypoint /bin/bash {image} -lc 'python3 run.py klu-trap-50ns'
```

Use any directory name under `cases/` to replay a case. Archived logs/waves are preserved; replays write under `replay/`. A failure is expected for the reported failing case. The runner limits each case to 120 seconds; runtime varies by hardware. This is diagnostic evidence, not a claim that timeout proves non-convergence. The prior 100 ns completion and earlier runs used their documented 180-second watchdog.

Only the two `sparse-*` decks change solver selection from their matching `klu-*` 50 ns cases. The selected clamp contains 144 device records, 22,575 resistors and 127 explicit wiring capacitors. It omits other semiconductor groups and is not a full-chip equivalent. Local startup settings are in `init/.spiceinit`. PDK and original input hashes are recorded separately.
''')
brief=f'''# Draft expert review: GF180 extracted-clamp transient failure

Prepared **{stamp}**. **Local draft; not sent.**

## Request

Please review a reproducible ngspice startup failure in a reduced extracted GF180 supply-clamp group. We need a numerically justified solution that preserves the foundry device equations and terminal behavior. We are not claiming a confirmed simulator or PDK defect.

## Reproducer and observations

- [Portable evidence archive](../../checkpoints/clamp-review/reproducer.tar.gz), with decks, logs, saved waves, replay runner, initialization and model hashes.
- Pinned container: `{image}`. Recorded logs identify ngspice 46.
- 144 device records, 22,575 resistors, 127 explicit wiring capacitors; other semiconductor groups omitted. The smaller resistor reduction passes current comparisons with maximum relative error 9.15e-14.
- The reported `X354` is a 25 × 10 µm `cap_nmos_06v0`. Simple one/eight-capacitor fixtures all complete (24 cases).
- Direct Gear/100 ns aborts near 127.352 µs in another capacitor of the bank. Trapezoidal/100 ns completes to 153 µs, including the load pulse.
- Trapezoidal/50 ns aborts near 125.330 µs; stricter 50 ns aborts near 119.488 µs, both naming `e.x354.ec_moscap#branch`.
- Final SPARSE-only replacements of the two 50 ns decks each time out after 120 seconds. They are incomplete, not evidence that SPARSE can never converge.
- No accepted numerical fix. Local solver experimentation is stopped after this bounded batch.

## Questions for the reviewer

1. Does the behavioral-capacitor conversion or matrix conditioning explain failure near the settled state? How can we distinguish the cause with a controlled diagnostic?
2. Are the initialization, compatibility (`ngbehavior=hsa`, `wnflag=1`) and nonlinear-capacitor treatment appropriate for this installed PDK?
3. What targeted solver/model-equivalent reformulation should be tested, and how should terminal charge/current equivalence be demonstrated?
4. Is an independent extraction or simulation cross-check warranted before applying this to the full ring?

## Acceptance before adoption

Complete startup and load traces for both original capacitance placements, timestep and tolerance refinement, preserved terminal current/charge behavior, and full-corner regression. No capacitor substitution, artificial shunt, discarded parasitic, or relaxed tolerance is accepted solely because it makes a run finish.

Context: [isolation report](../moscap-branch.md), [extraction reference](../charge-reference.md), [completion plan](../../COMPLETION_PLAN.md).
'''
(R/'docs/reviews/clamp-startup-review.md').write_text(brief);(P/'review.md').write_text(brief.replace('[Portable evidence archive](../../checkpoints/clamp-review/reproducer.tar.gz)', '[Replay instructions](README.md)').split('Context:')[0]+'Context and parent-source locations are recorded in origins.json; see the repository documentation for the wider project.\n')
(P/'origins.json').write_text(json.dumps(origins,indent=2)+'\n')
files=sorted(p for p in P.rglob('*') if p.is_file());hashes={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(C/'reproducer.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(P)))
with tarfile.open(C/'reproducer.tar.gz') as tar:
 for item in tar:assert hashlib.sha256(tar.extractfile(item).read()).hexdigest()==hashes[item.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'reproducer.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
(R/'simulations/bounded-solver.json').write_text(json.dumps(s,indent=2)+'\n')
print('Verified portable review archive:',len(files),'files. Not sent.')
