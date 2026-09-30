"""Gate one authorized placement batch on completed, passing bright audits.

Runs as a detached host process so Docker can launch without exposing its socket
inside a simulation container. Stops on failures; never retries or overwrites runs.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):return {}


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream, 'sha256').hexdigest()


def gate_ready(status):
    assert not status.get('failures'), 'Predecessor simulation/audit failure'
    assert not status.get('render_failures'), 'Predecessor rendering failure'
    assert not status.get('watcher_expired'), 'Predecessor watcher expired'
    if not status.get('all_pairs_audited'):return False
    assert status.get('all_selected_screens_pass'), 'Predecessor accuracy/refinement failed'
    assert status.get('audited') == {'bright27': True, 'bright125': True}
    return True


def verify_reports(root, paths):
    evidence, reports = {}, []
    for relative in paths:
        report = read(root / relative)
        assert report['pattern'] == 'bright' and report['selected_screen_pass']
        assert set(report['checks']) == {'capture_readout', 'output_tracking', 'refinement', 'event_refinement'}
        assert all(report['checks'].values()) and not report['contrast_order_applicable']
        assert not report['full_bank_accuracy_qualified'] and not report['full_chip_qualified']
        assert [(r['samples'], r['references']) for r in report['runs']] == [(128, 192), (128, 0)]
        assert max(report['max_total_error_uV'], report['max_tracking_error_uV']) < 500
        assert max(report['max_refinement_uV'], report['event_refinement_worst']['difference_uV']) < 10
        for name, digest in report['evidence_hashes'].items():
            assert name not in evidence or evidence[name] == digest, name
            evidence[name] = digest
        reports.append(report)
    assert {r['temperature_C'] for r in reports} == {27, 125} and len(reports) == 2
    for name, digest in evidence.items():assert sha(root / name) == digest, name
    return reports, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); config = read(args.config)
    args.out.mkdir(parents=True, exist_ok=True)
    lock = (args.out / 'controller.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status_path = args.out / 'status.json'
    assert not status_path.exists(), 'Do not restart an existing continuation'
    started = time.monotonic()
    state = dict(pid=os.getpid(), phase='waiting for bright audits', audited={}, failures={},
                 render_failures={}, all_pairs_audited=False, all_selected_screens_pass=False,
                 watcher_expired=False, placement_launched=False)
    last_handoff_phase = None

    def publish():
        nonlocal last_handoff_phase
        state.update(updated_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started)
        temporary = status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2) + '\n'); temporary.replace(status_path)
        if state['phase'] != last_handoff_phase:
            path = ROOT / 'PICK_UP_HERE.md'
            block = ('<!-- OVERNIGHT_STATUS_BEGIN -->\n'
                     f'**Automatic continuation status:** {state["phase"]}. '
                     f'Updated {state["updated_at_utc"]}. '
                     f'Placement launched: {state["placement_launched"]}. '
                     f'All placement audits passing: {state["all_selected_screens_pass"]}.\n'
                     '<!-- OVERNIGHT_STATUS_END -->')
            text = path.read_text()
            pattern = r'<!-- OVERNIGHT_STATUS_BEGIN -->.*?<!-- OVERNIGHT_STATUS_END -->'
            if re.search(pattern, text, re.S):
                path.write_text(re.sub(pattern, lambda _: block, text, flags=re.S))
            last_handoff_phase = state['phase']

    def execute(command, name, timeout=1800):
        with (args.out / (name + '.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)

    def frozen_inputs():
        for name, digest in config['evidence_hashes'].items():assert sha(ROOT / name) == digest, name

    try:
        publish(); frozen_inputs()
        while True:
            gate_path = ROOT / config['gate_status']; gate = read(gate_path)
            if gate_ready(gate):break
            assert gate_path.exists() and time.time() - gate_path.stat().st_mtime < 4500, 'Bright watcher stopped updating'
            assert time.monotonic() - started < 14400, 'Continuation wait deadline reached'
            state['predecessor_progress'] = gate.get('progress', []); publish(); time.sleep(30)
        state['phase'] = 'verifying bright evidence'; publish(); frozen_inputs()
        reports, evidence = verify_reports(ROOT, config['gate_reports'])
        predecessor = read(ROOT / config['gate_plan'])
        names = [r['container'] for r in predecessor['runs']] + [predecessor['watcher']['container']]
        inspection = json.loads(subprocess.check_output(['docker', 'inspect', *names], text=True))
        assert all(not item['State']['Running'] and item['State']['ExitCode'] == 0 for item in inspection), 'Predecessor containers not all exited cleanly'
        review = dict(reviewed_at_utc=datetime.now(timezone.utc).isoformat(),
            scope='Automated overnight integrity/acceptance review; plots exist but have not been visually reviewed by an assistant.',
            plots_reviewed=False, distinct_evidence_files_verified=len(evidence), hash_failures=[],
            completed_transients=4, reads_per_transient=128, new_references_audited=384,
            batch_elapsed_seconds=gate['elapsed_seconds'], simulation_and_watcher_exit_codes=[0] * len(inspection),
            cases=[{k:r[k] for k in ['temperature_C', 'pattern', 'checks', 'max_total_error_uV', 'max_tracking_error_uV', 'max_refinement_uV', 'event_refinement_worst']} for r in reports],
            full_bank_accuracy_qualified=False, full_chip_qualified=False,
            reviewed_hashes={name:sha(ROOT / name) for name in config['gate_reports']})
        review_path = ROOT / config['review_output']; assert not review_path.exists()
        review_path.write_text(json.dumps(review, indent=2) + '\n')
        state['bright_review'] = config['review_output']; state['phase'] = 'launching placement batch'; publish()
        frozen_inputs()
        execute([sys.executable, 'scripts/launch-bank-placement.py', '--tag', config['placement_tag']], 'launch')
        plan_path = ROOT / f'build/compact-bank-placement-plan-{config["placement_tag"]}.json'
        plan = read(plan_path)
        assert all(r.get('container_id') for r in plan['runs']) and plan['watcher']['container_id']
        state.update(placement_launched=True, placement_plan=str(plan_path.relative_to(ROOT)), phase='placement simulations running')
        publish()
        execute(['bash', 'scripts/run-tools.sh', 'python3', 'scripts/render-bank-placement.py', '--plan', str(plan_path.relative_to(ROOT))], 'render-launch')
        while True:
            path = ROOT / plan['watcher']['path'] / 'status.json'; placement = read(path)
            assert time.monotonic() - started < 12 * 3600, 'Overnight continuation deadline reached'
            if path.exists():assert time.time() - path.stat().st_mtime < 4500, 'Placement watcher stopped updating'
            for key in ('audited', 'failures', 'render_failures', 'all_pairs_audited', 'all_selected_screens_pass', 'watcher_expired', 'progress'):
                if key in placement:state[key] = placement[key]
            if placement.get('all_pairs_audited'):
                state['phase'] = 'placement audits complete; review required'; publish(); return
            if placement.get('watcher_expired') or placement.get('failures'):
                raise RuntimeError('Placement watcher reports failure or expiry; retained for review')
            publish(); time.sleep(30)
    except Exception as error:
        state.update(phase='stopped; review required', failures={'continuation': str(error), 'automatic_progression': 'stopped'},
                     all_pairs_audited=False, all_selected_screens_pass=False)
        publish(); raise


if __name__ == '__main__':main()
