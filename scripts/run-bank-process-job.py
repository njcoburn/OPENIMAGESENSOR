"""Run a process-corner job and retain its exit status even on an early error."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exit-record',type=Path,required=True)
    p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    assert a.command and not a.exit_record.exists()
    code=1
    try:code=subprocess.run(a.command,cwd=ROOT).returncode
    finally:
        a.exit_record.parent.mkdir(parents=True,exist_ok=True)
        tmp=a.exit_record.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(returncode=code,finished_at_utc=datetime.now(timezone.utc).isoformat()))+'\n')
        tmp.replace(a.exit_record)
    raise SystemExit(code)

if __name__=='__main__':main()
