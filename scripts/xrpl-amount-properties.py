#!/usr/bin/env python3
"""Bounded exact-arithmetic checks against unchanged production Swift functions."""
import argparse
from collections import Counter
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time
from source_state import require_source_state

BASE = 'a904515793b087289140e4411924f030b3fe61ff'
COMMIT = '6783750661c43d3511d8973a2de77106fdf2001d'
PREFIX = 'Packages/OathAnkr/Sources/OathAnkr/'
SEED = 20261103
BASE_FAILURES = [71,73,197,199,287,289,419,421,623,625,659,661,665,667,671,673,743,745,767,1007,1009,1213,1271,1367,1369,1595,1597,1625,1627,1685,1687,1727,1729,1763,1765,1913,1915,2063,2065,2135,2137,2267,2269,2351,2353,2555,2557,2867,2869,2993,2995,3215,3217,4895,4896,4897,4898]

def sha(data): return hashlib.sha256(data).hexdigest()

def vectors():
    rng = random.Random(SEED)
    rows = []
    def add(op, value, expected, **kwargs): rows.append(dict(op=op,value=value,expected=expected,**kwargs))
    for invalid in ['', '-1', '+1', '1.0', '1e2', ' 1', '1\n', '١', '１', '9'*194, 'x']:
        for op in ['canonical','round','value']: add(op,invalid,'ERROR',up=False)
    for i in range(600):
        n = rng.randrange(10**rng.randrange(1,194)); s = str(n)
        padded = '0'*rng.randrange(0,4)+s
        add('canonical',padded,s if len(padded)<=193 else 'ERROR')
        factor = 10**max(0,len(s)-16)
        for up in [False,True]:
            rounded = ((n+factor-1)//factor if up else n//factor)*factor
            add('round',s,str(rounded),up=up)
            num,den = rng.randint(1,2_000_000_000),rng.randint(1,2_000_000_000)
            product = n*num
            result = (product+den-1)//den if up else product//den
            add('ratio',s,str(result) if len(str(result))<=193 else 'ERROR',up=up,numerator=num,denominator=den)
        other = rng.randrange(10**rng.randrange(1,194))
        add('subtract',s,str(n-other) if n>=other else 'ERROR',other=str(other))
    for exponent in [-97,-96,-95,0,79,80,81]:
        for mantissa in [10**15,10**15+1,10**16-1]:
            for negative in [False,True]:
                value = ('-' if negative else '')+str(mantissa)+'e'+str(exponent)
                expected = str((-1 if negative else 1)*mantissa*10**(exponent+96)) if -96<=exponent<=80 else 'ERROR'
                add('parse',value,expected)
    for _ in range(600):
        mantissa = rng.randrange(10**15,10**16); exponent = rng.randint(-96,80)
        atomic = mantissa*10**(exponent+96)
        add('parse',str(mantissa)+'e'+str(exponent),str(atomic))
        add('value',str(atomic),'NUMERIC',atomic=str(atomic))
    for invalid in ['','1e','1e201','1e-201','1.','1..0','NaN','Infinity','--1','١','1e0e0','12345678901234567','1e-82','1e96']:
        add('parse',invalid,'ERROR')
    add('value','0','0'); add('parse','-0','0')
    for num,den in [(0,1),(1,0),(2_000_000_001,1),(1,2_000_000_001)]:
        add('ratio','1','ERROR',up=True,numerator=num,denominator=den)
    # 1e90 is within the issued-token range; internal scale is 96 decimals.
    for up in [False,True]:
        add('ratio',str(10**186),str(10**186),up=up,numerator=10**9,denominator=10**9)
        add('ratio',str(10**186),str(2*10**186),up=up,numerator=2*10**9,denominator=10**9)
    add('ratio',str(6*10**193//7),'ERROR',up=True,numerator=7,denominator=6)
    return rows

SWIFT = r'''
import Foundation
enum XrplSendError: Error { case amount, insufficientFunds }
enum XrplError: Error { case malformed }
struct Input: Decodable { let op:String, value:String; let up:Bool?; let numerator:UInt64?,denominator:UInt64?;let other:String? }
@main struct Checks {
 static func main() throws {
  let inputs = try JSONDecoder().decode([Input].self,from:FileHandle.standardInput.readDataToEndOfFile())
  let results = inputs.map { x -> String in
   do {
    switch x.op {
     case "canonical":return try XrplSendAmount.canonical(x.value)
     case "round":return try XrplSendAmount.roundedIssued(x.value,up:x.up!)
     case "ratio":return try XrplSendAmount.ratio(x.value,numerator:x.numerator!,denominator:x.denominator!,up:x.up!)
     case "value":return try XrplSendAmount.issuedValue(x.value)
     case "parse":return try XrplIdentity.issuedAmount(x.value)
     case "subtract":return try XrplSendAmount.subtract(x.value,x.other!)
     default:fatalError("Unknown fixture operation")
    }
   } catch { return "ERROR" }
  }
  FileHandle.standardOutput.write(try JSONEncoder().encode(results))
 }
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--expected-commit',choices=[BASE,COMMIT],default=COMMIT);a=p.parse_args()
    source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,a.expected_commit)
    sources={n:(source/(PREFIX+n)).read_text() for n in ['XrplSendAmount.swift','XrplModels.swift','SuiModels.swift','AptosModels.swift']}
    def cut(name,start,end):
        s=sources[name];assert s.count(start)==1 and s.count(end)==1
        return s[s.index(start):s.index(end)]
    parts=[cut('XrplSendAmount.swift','public enum XrplSendAmount {','    static func json(')+'}\n',
        'enum XrplIdentity {\n'+cut('XrplModels.swift','    public static let issuedScale = 96','    private static let alphabet')+cut('XrplModels.swift','    public static func issuedAmount(','    static func hash(')+'}\n',
        'enum SuiIdentity {\n'+cut('SuiModels.swift','    static func add(','\n}\nprivate struct MoveTypeParser')+'\n}\n',
        'enum AptosIdentity {\n'+cut('AptosModels.swift','    static func add(','\n}\npublic struct AptosToken')+'\n}\n']
    compiled=SWIFT+'\n'.join(parts);cases=vectors();fixture=json.dumps(cases,separators=(',',':')).encode()
    (out/'vectors.json').write_bytes(fixture)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='xrpl-amount-review-') as temporary:
        work=Path(temporary);(work/'Checks.swift').write_text(compiled)
        result=subprocess.run(['xcrun','swiftc','-swift-version','6','-parse-as-library',str(work/'Checks.swift'),'-o',str(work/'checks')],env=env,capture_output=True,timeout=120)
        (out/'compile.log').write_bytes(result.stdout+result.stderr)
        if result.returncode:raise ValueError('Compilation failed')
        result=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(work/'checks')],input=fixture,capture_output=True,env=env,timeout=45)
        (out/'output.json').write_bytes(result.stdout);(out/'runtime.log').write_bytes(result.stderr)
        if result.returncode:raise ValueError('Runtime failed')
    actual=json.loads(result.stdout)
    if not isinstance(actual,list) or len(actual)!=len(cases) or any(not isinstance(x,str) for x in actual):
        raise ValueError('Unexpected output type or missing cases')
    failures=[]
    with localcontext() as context:
        context.prec=512
        for i,(case,value) in enumerate(zip(cases,actual)):
            expected=case['expected']
            if expected=='NUMERIC':
                valid=value!='ERROR' and Decimal(value)==Decimal(case['atomic']).scaleb(-96)
            else:valid=value==expected
            if not valid:failures.append(dict(index=i,case=case,actual=value))
    require_source_state(source,a.expected_commit)
    report=dict(source_commit=a.expected_commit,seed=SEED,case_count=len(cases),operation_counts=dict(Counter(c['op'] for c in cases)),passed=len(cases)-len(failures),failed=len(failures),failures=failures,duration_seconds=round(time.monotonic()-start,2),
        source_hashes={PREFIX+n:sha(s.encode()) for n,s in sources.items()},compiled_sha256=sha(compiled.encode()),fixture_sha256=sha(fixture),output_sha256=sha(result.stdout),script_sha256=sha(Path(__file__).read_bytes()),
        scope='Unchanged selected production amount functions and their arithmetic dependencies; Python arbitrary precision oracle. No signer, transaction encoding, node, UI or real wallet execution.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['passed'],'passed;',report['failed'],'failed')
    expected = BASE_FAILURES if a.expected_commit==BASE else []
    if [f['index'] for f in failures] != expected: raise SystemExit('Unexpected case outcomes')
    if failures: print('Expected baseline failures reproduced; this is not a passing application result')

if __name__=='__main__':main()
