import gzip
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/5.0.1-build103/xrpl-signing'
class XRPSigningEvidenceTests(unittest.TestCase):
    def test_runtime_logs_and_fixture_binding(self):
        result=json.loads((E/'replay/result.json').read_text())
        self.assertEqual(result['source_commit'],'6783750661c43d3511d8973a2de77106fdf2001d')
        for field,path in [('script_sha256','scripts/xrpl-signing-vectors.py'),('generator_sha256','fixtures/xrpl-signing/generate.cjs'),('overlay_sha256','fixtures/xrpl-signing/XrplAuditSigningTests.swift')]:
            self.assertEqual(result[field],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
        fixture=gzip.decompress((E/'replay/vectors.json.gz').read_bytes())
        self.assertEqual(result['fixture_sha256'],hashlib.sha256(fixture).hexdigest())
        j=json.loads(fixture);self.assertEqual(len(j['vectors']),61);self.assertEqual(len(j['hashes']),13)
        self.assertEqual(len(result['methods']),4)
        for row in result['methods']:
            self.assertEqual((row['status'],row['exit_code']),('passed',0))
            self.assertEqual(row['log_sha256'],hashlib.sha256(gzip.decompress((E/'replay'/(row['log']+'.gz')).read_bytes())).hexdigest())
    def test_exact_hash_partial_coverage(self):
        ledger={r['path']:r for r in json.loads((ROOT/'scope/history/5.0.1-build103/inventory.json').read_text())['files']}
        entries=json.loads((E/'source.json').read_text())['files'];self.assertEqual(len(entries),5)
        for row in entries:
            self.assertEqual(row['sha256'],ledger[row['path']]['sha256'])
            self.assertEqual(ledger[row['path']]['status'],'partially-reviewed')
            self.assertEqual(row['read_ranges'],[[1,row['line_count']]])
if __name__=='__main__':unittest.main()
