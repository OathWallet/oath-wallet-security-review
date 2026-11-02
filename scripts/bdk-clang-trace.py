#!/usr/bin/env python3
"""Record exact target compile actions and compiler-generated header lists in a private scratch directory."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile

args=sys.argv[1:]
driver=os.environ['OATH_BDK_CLANGXX' if Path(sys.argv[0]).name.endswith('++') else 'OATH_BDK_CLANG']
if '-c' not in args or '-o' not in args:
    os.execv(driver,[driver,*args])
if args.count('-o')!=1 or any(v in args for v in ('-MD','-MMD','-M','-MM','-MF')):
    raise SystemExit('Unrecognized object or dependency output contract')
dest=Path(args[args.index('-o')+1]).resolve()
if dest.suffix!='.o':
    os.execv(driver,[driver,*args])
trace=Path(tempfile.mkdtemp(dir=os.environ['OATH_BDK_TRACE']))
dep=trace/'headers.d'
result=subprocess.run([driver,*args,'-MD','-MF',str(dep)])
if result.returncode==0:
    info=dict(cwd=str(Path.cwd()),object=str(dest),argv=args,object_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
              dependency_file_sha256=hashlib.sha256(dep.read_bytes()).hexdigest())
    (trace/'action.json').write_text(json.dumps(info)+'\n')
sys.exit(result.returncode)
