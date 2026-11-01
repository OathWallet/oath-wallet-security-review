#!/usr/bin/env python3
"""Run encrypted existing-wallet recovery through the app's real host restore fixture."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--expected-commit');a=p.parse_args()
    source=a.source.resolve();pin=require_source_state(source,a.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    f=ROOT/'fixtures/extended-key-wire/restore-fragment.swift';start=time.monotonic();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);log=out/'extended-key-restore.log'
    with tempfile.TemporaryDirectory(prefix='oath-wire-restore-') as t:
        work=Path(t)/'app';subprocess.run(['git','clone','-q','--local','--no-checkout',source,work],check=True)
        subprocess.run(['git','-C',work,'checkout','-q','--detach',pin],check=True)
        file=work/'Tools/CheckCloudRestore.swift';orig=file.read_bytes();marker='        print("Passed '
        text=orig.decode();assert text.count(marker)==1
        file.write_text('import OathBitcoin\n'+text.replace(marker,f.read_text()+'\n'+marker))
        vectors=Path(t)/'vectors.json'
        with vectors.open('w') as stream:subprocess.run([sys.executable,ROOT/'scripts/utxo-recovery-vectors.py'],stdout=stream,check=True)
        expected=json.loads((ROOT/'fixtures/extended-key-wire/scripts.json').read_bytes())
        assert {k:v['script'] for k,v in json.loads(vectors.read_bytes()).items()}==expected
        env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI')}
        env.update(OATH_VALIDATION_SCRATCH=str(a.scratch.resolve()),OATH_REVIEW_RECOVERY_VECTORS=str(vectors))
        with log.open('w') as stream:
            run=subprocess.run([sys.executable,'Tools/CheckMultiWallet.py','--cloud-restore'],env=env,cwd=work,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        assert subprocess.check_output(['git','-C',work,'diff','--name-only'],text=True).splitlines()==['Tools/CheckCloudRestore.swift']
        raw=log.read_text();matches=re.findall(r'^Passed (\d+) cloud-restore integration checks',raw,re.M)
        ok=run.returncode==0 and len(matches)==1 and int(matches[0])>=168 and raw.count('Four encrypted extended-key restorations retained their original scripts across cold reopen and re-backup.')==1
        result=dict(check='extended-key-restore',source_commit=pin,status='passed' if ok else 'failed',exit_code=run.returncode,assertion_count=int(matches[0]) if len(matches)==1 else None,
            original_test_sha256=sha(orig),fixture_sha256=sha(f.read_bytes()),oracle_scripts_sha256=sha((ROOT/'fixtures/extended-key-wire/scripts.json').read_bytes()),log=log.name,log_sha256=sha(log.read_bytes()),duration_seconds=round(time.monotonic()-start,2),
            scope='Local synthetic encrypted BackupDocument, app restore, descriptor, key identity, app vault reopen and encrypted re-backup. Host harness substitutes iOS WalletCore profile derivation and system storage; independent script comparison goes through the production Bitcoin package.')
        (out/'extended-key-restore.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['assertion_count']);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
