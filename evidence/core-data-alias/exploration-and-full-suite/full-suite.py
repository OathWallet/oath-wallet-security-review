from pathlib import Path
import sys,os,json,time,hashlib,shlex
sys.path.insert(0,'/Volumes/WORKSPACE/oath-wallet-security-review/scripts')
from bounded_process import logged_command
s=Path('/tmp/oath-core-dependency-repairs');o=Path('/tmp/oath-core-data-alias-review');rows=[]
env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR']};env['TEST_TMPDIR']=str(o/'test-temp');Path(env['TEST_TMPDIR']).mkdir(exist_ok=True)
def run(args,name,cwd,timeout=1800):
 t=time.monotonic()
 with (o/(name+'.log')).open('w') as log:c,to=logged_command(args,stream=log,timeout=timeout,cwd=cwd,env=env)
 rows.append(dict(name=name,command=args,exit_code=c,timed_out=to,duration_seconds=round(time.monotonic()-t,3),log_sha256=hashlib.sha256((o/(name+'.log')).read_bytes()).hexdigest()))
 (o/'full-suite-commands.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,c,flush=True)
 if c or to:raise SystemExit(1)
obj=o/'TWData.o'
run(['clang++','-std=c++20','-O2','-DNDEBUG','-I',str(s/'include'),'-I',str(s/'src'),'-I',str(s/'trezor-crypto/include'),'-c',str(o/'TWData.cpp'),'-o',str(obj)],'full-suite-compile',s)
cmd=shlex.split((s/'build/native-core/tests/CMakeFiles/tests.dir/link.txt').read_text());cmd[2:2]=[str(obj),'/tmp/oath-core-native-toolchain/fixed-extended/HDWallet.o'];binary=s/'build/tests/tests-data-alias-fixed';cmd[cmd.index('-o')+1]=str(binary)
run(cmd,'full-suite-link',s/'build/native-core/tests',180)
run([str(binary),'--gtest_output=json:'+str(o/'full-suite.json')],'full-suite',s)
r=json.loads((o/'full-suite.json').read_text());print(json.dumps({k:r[k] for k in ['tests','failures','disabled','errors','time']}))
