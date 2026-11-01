#!/usr/bin/env python3
"""Link each prior failing selector to a pinned source file and an actual current XCTest result."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
RENAMES={
    'testHealthyReadIsQuietAndRealDeadlineRetainsSafeContext':'testDeadlineIsExcludedButInvalidTransactionRetainsSafeContext',
    'testRecoveredOutageStaysCorrelatedAndCancellationStaysQuiet':'testAvailabilityAndCancellationStayQuietButInvalidPricesAreReported',
    'testCancelledDeliveryIsQuietButActualConnectionLossStillReports':'testCancelledDeliveryAndOutageAreQuietButInvalidResponseReports',
    'testCancelledFallbacksStayQuietAndRealOutagesRemainCorrelated':'testCancellationAndOutagesAreQuietButMalformedResponsesRemainCorrelated',
    'testOriginalFailuresAreCorrelatedAndNeverContainAccountOrCursor':'testOutagesAreExcludedButInvalidResponsesNeverContainAccountOrCursor',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('bitcoin_results',type=Path);p.add_argument('ankr_results',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();pin=json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'];require_source_state(a.source,pin)
    history=ROOT/'review/TEST-TRIAGE.json';rows=[]
    for group in json.loads(history.read_bytes()):
        pkg=group['package'];result_dir={'OathBitcoin':a.bitcoin_results,'OathAnkr':a.ankr_results}[pkg]
        result=json.loads((result_dir/(pkg+'.json')).read_bytes());assert result['source_commit']==pin
        assert sha((result_dir/(pkg+'.log')).read_bytes())==result['log_sha256']
        cases=json.loads((result_dir/(pkg+'-cases.json')).read_bytes());lookup={c['selector']:c for c in cases};assert len(cases)==len(lookup)
        parsed=[re.search(r'^<SOURCE>/([^:]+):\d+: error: -\[([\w.]+) (\w+)\]',line) for line in group['failed_assertions']]
        assert all(parsed), 'Unmapped historical assertion'
        for file,cls,old in sorted({m.groups() for m in parsed}):
            new=RENAMES.get(old,old);previous=group['source_commit']
            old_bytes=subprocess.check_output(['git','-C',a.source,'show',previous+':'+file]);new_bytes=(a.source/file).read_bytes()
            assert ('func '+old+'(').encode() in old_bytes and ('func '+new+'(').encode() in new_bytes
            case=lookup[cls+'/'+new];log=(result_dir/case['log']).read_bytes();assert sha(log)==case['log_sha256']
            name='-['+cls+' '+new+']'
            assert case['status']=='passed' and case['exit_code']==0 and re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",log.decode(),re.M)==[(name,'started'),(name,'passed')]
            rows.append(dict(package=pkg,path=file,historical_selector=cls+'/'+old,source_commit_before=previous,source_hash_before=sha(old_bytes),
                current_selector=case['selector'],current_source_sha256=sha(new_bytes),renamed=new!=old,assertion_count_before=sum(m.groups()==(file,cls,old) for m in parsed),
                current_case_log=case['log'],current_case_sha256=case['log_sha256'],current_outcome='passed'))
    assert len(rows)==23 and sum(r['assertion_count_before'] for r in rows)==48
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(source_commit=pin,historical_record_sha256=sha(history.read_bytes()),cases=rows,
        scope='Current retest of each historical selector or its explicitly mapped successor. Renamed diagnostic tests exercise today’s outage policy and a retained invalid-data control; a new expectation does not retroactively make an old assertion pass.'),indent=2)+'\n')
    print(len(rows),'passing selectors back to 48 historical assertion failures')
if __name__=='__main__':main()
