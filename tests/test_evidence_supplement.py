import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class EvidenceSupplementTests(unittest.TestCase):
    def test_transcripts_resolved_pins_and_generated_test_header_survive_bundling(self):
        script=Path(__file__).resolve().parents[1]/'scripts/bundle-evidence.py'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir()
            for name in ['before.jsonl','Package.resolved','TWHRP.h','unrelated.h','credentials.env']:
                (raw/name).write_text('synthetic public fixture\n')
            output=root/'public'
            subprocess.run([sys.executable,str(script),str(raw),'--output',str(output)],check=True,capture_output=True)
            rows=json.loads((output/'manifest.json').read_text())
            self.assertEqual({r['path'] for r in rows},{'raw/before.jsonl','raw/Package.resolved','raw/TWHRP.h'})
            for row in rows:self.assertEqual(hashlib.sha256((output/row['path']).read_bytes()).hexdigest(),row['published_sha256'])
