"""Bounded matched-version experiment: stock corner, extracted stock, separate candidate.
No PDK edits. Same fixture and options, only binary differs within each pair.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,os,re,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/ngspice-version-comparison';P=Path('/foss/pdks/gf180mcuD');INIT=R/'checkpoints/clamp-review/package/init'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 source=P/'libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice';raw=source.read_text();cor=re.search(r'(?ms)^\.SUBCKT gf180mcu_fd_io__cor .*?^\.ENDS[^\n]*',raw).group()
 stock=raw[:raw.index('.SUBCKT')]+cor+'\nXcorner db dg vb gb gf180mcu_fd_io__cor\nVwire1 feed vb 0\nVwire2 feed db 0\nVwire3 gb 0 0\nVwire4 dg 0 0\n'
 original=(R/'build/charge-reduced/corner-full/practical-nominal/model.spice').read_text()
 candidate=(R/'build/corner-scaled-refinement/nominal/model.spice').read_text()
 # Assert the candidate changes only cap instance names and adds its helper subcircuit.
 reversed_candidate=candidate[:candidate.index('.subckt review_cap_nmos_06v0')].replace('review_cap_nmos_06v0','cap_nmos_06v0')
 assert reversed_candidate.strip()==original.strip()
 deck=(R/'build/corner-scaled-refinement/nominal/test.spice').read_text()
 assert 'reltol=1e-7 abstol=1e-14' in deck and 'tran 25n 153u 0 25n uic' in deck
 for name,model in [('stock-corner',stock),('extracted-stock',original),('extracted-candidate',candidate)]:
  d=B/'decks'/name;d.mkdir(parents=True,exist_ok=True);(d/'model.spice').write_text(model);(d/'test.spice').write_text(deck)
 control=B/'decks/capacitor-control';control.mkdir(parents=True,exist_ok=True)
 (control/'test.spice').write_bytes((R/'build/clamp-control-breakpoints/original-25ps/test.spice').read_bytes())
 (control/'model.spice').write_text('* Standalone control uses stock PDK include in test deck\n')
 provenance=dict(stock_library_sha256=sha(source),primitive_model_sha256=sha(P/'libs.tech/ngspice/sm141064.ngspice'),init_sha256=sha(INIT/'.spiceinit'),candidate_scope='Local helper normalization diagnostic, not a stock PDK fix',fixture='100 us 3.3 V ramp, 2 ohm source, two 1 mA loads at 151 us with 1 ns edges; 27 C typical; trap, KLU, 25 ns maxstep, reltol 1e-7, abstol 1e-14',stock_scope='Unextracted cor macro; ideal internal rail wiring, same external source and load fixture. Topology differs from extracted coupon; compare versions within each case, not exact stock-vs-extracted equivalence.')
 (B/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
def run(task):
 version,case=task;exe=(B/f'install-{version}/bin/ngspice') if version!='installed' else Path('/foss/tools/ngspice/bin/ngspice');d=B/'runs'/f'{case}-{version}';d.mkdir(parents=True,exist_ok=True)
 for f in ['test.spice','model.spice']:(d/f).write_bytes((B/'decks'/case/f).read_bytes())
 assert not (d/'result.json').exists(),f'Refuse to overwrite existing experiment {d}'
 start=time.monotonic();error=None;code=None;last=None;rows=0;stats=None
 try:
  with (d/'ngspice.log').open('w') as log:
   p=subprocess.run([str(exe),'-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=1200,env={**os.environ,'SPICE_USERINIT_DIR':str(INIT),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'});code=p.returncode
 except subprocess.TimeoutExpired:error='1200 s watchdog expired; no retry'
 log=(d/'ngspice.log').read_text();failures=re.findall(r'^.*(?:aborted|timestep too small|^Error|unknown device|fatal).*$',log,re.I|re.M)
 if failures:error='; '.join(failures)
 if (d/'tran.dat').exists():
  try:
   a=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2);rows=len(a);last=float(a[-1,0]);assert np.isfinite(a).all()
   if not error and code==0 and last>=152.99e-6:
    stats=dict(header=(d/'tran.dat').read_text().splitlines()[0],final_values=a[-1,1:].tolist(),min_values=np.min(a[:,1:],axis=0).tolist(),max_values=np.max(a[:,1:],axis=0).tolist())
   elif not error:error='Incomplete transient or nonzero return code'
  except Exception as e:error=repr(e)
 elif not error:error='No waveform'
 result=dict(version=version,case=case,completed=error is None,error=error,returncode=code,last_time_s=last,rows=rows,seconds=time.monotonic()-start,stats=stats,exe_sha256=sha(exe),deck_sha256=sha(d/'test.spice'),model_sha256=sha(d/'model.spice'))
 (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','control','stock','extracted','candidate']);args=ap.parse_args()
 if args.stage=='prepare':prepare();print('Prepared matched decks');raise SystemExit
 if args.stage in ['stock','extracted','candidate']:
  assert json.loads((B/'control-audit.json').read_text())['control_screen_pass'], 'Control response must pass before network runs'
 case={'control':'capacitor-control','stock':'stock-corner','extracted':'extracted-stock','candidate':'extracted-candidate'}[args.stage]
 versions=['46','47']
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[(v,case) for v in versions]))
 comparison=None
 if all(r['completed'] for r in results):
  a,b=[np.loadtxt(B/'runs'/f'{case}-{v}'/'tran.dat',skiprows=1) for v in versions];t=np.unique(np.r_[a[:,0],b[:,0]]);delta=np.array([abs(np.interp(t,a[:,0],a[:,i])-np.interp(t,b[:,0],b[:,i])) for i in range(1,a.shape[1])])
  comparison=dict(max_difference_by_column=np.max(delta,axis=1).tolist(),post150us_max_difference_by_column=np.max(delta[:,t>=150e-6],axis=1).tolist(),scope='Version comparison only; not timestep refinement or complete-chip qualification')
 report=dict(runs=results,comparison=comparison,accepted_full_chip=False)
 (B/f'{args.stage}-results.json').write_text(json.dumps(report,indent=2)+'\n')
