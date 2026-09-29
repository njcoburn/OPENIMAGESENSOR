"""Start a Windows desktop alert for the local bank audit, independently of this chat."""
import argparse
import base64
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def quoted(value):return "'"+value.replace("'","''")+"'"
def windows(path):return subprocess.check_output(['wslpath','-w',str(path.resolve())],text=True).strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--status',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True)
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args()
    assert a.status.exists() and not a.state.exists(), 'Use an existing status and a fresh notification state'
    script=(ROOT/'scripts/notify-bank-completion.ps1').read_text()
    command='& {\n'+script+'\n} -StatusPath '+quoted(windows(a.status))+' -NotificationStatePath '+quoted(windows(a.state))
    if a.check_only:command+=' -CheckOnly'
    encoded=base64.b64encode(command.encode('utf-16le')).decode()
    if a.check_only:
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],check=True)
    else:
        launch="Start-Process -FilePath powershell.exe -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand',"+quoted(encoded)+") | Select-Object Id | ConvertTo-Json"
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',launch],check=True)

if __name__=='__main__':main()
