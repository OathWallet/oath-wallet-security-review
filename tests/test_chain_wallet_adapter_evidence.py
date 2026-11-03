import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


class AdapterCoverageEvidence(unittest.TestCase):
    def test_new_wrapper_reads_remain_partial_and_hash_bound(self):
        binding = read('evidence/5.0.2-build104/chain-wallet-adapters/source-binding.json')
        dispositions = read('review/dispositions.json')
        inventory = {r['path']: r for r in read('scope/inventory.json')['files']}
        wrappers = [r for r in binding['files'] if r['disposition'] == 'partially-reviewed']
        self.assertEqual(len(wrappers), 4)
        self.assertEqual(binding['baseline_commit'], read('scope/source.json')['reviewed_commit'])
        for row in wrappers:
            name = row['path']
            self.assertEqual(dispositions[name]['sha256'], row['sha256'])
            self.assertEqual(inventory[name]['sha256'], row['sha256'])
            self.assertEqual(dispositions[name]['status'], 'partially-reviewed')
            self.assertEqual(inventory[name]['status'], 'partially-reviewed')
            self.assertIn('review/CHAIN-WALLET-ADAPTERS.md', dispositions[name]['evidence'])

    def test_reconciliation_carries_only_identical_existing_partial_decisions(self):
        receipt = read('evidence/5.0.2-build104/chain-wallet-adapters/compiler-reconciliation.json')
        historic = {r['path']: r for r in read(receipt['historical_ledger'])['files']}
        canonical = read('review/dispositions.json')
        current = {r['path']: r for r in read('evidence/5.0.2-build104/compiler/dispositions.json')['files']}
        self.assertEqual(len(receipt['files']), 16)
        self.assertEqual(len({r['path'] for r in receipt['files']}), 16)
        for row in receipt['files']:
            previous = historic[row['historical_compiler_path']]
            compiled = current[row['historical_compiler_path']]
            self.assertEqual(previous['review_status'], 'partially-reviewed')
            self.assertEqual(previous['sha256'], row['sha256'])
            self.assertEqual(canonical[row['path']]['sha256'], row['sha256'])
            self.assertEqual(canonical[row['path']]['status'], 'partially-reviewed')
            self.assertEqual(compiled['review_status'], 'partially-reviewed')
            self.assertTrue(compiled['additional_review'])
            self.assertIn(receipt['historical_ledger'], compiled['evidence'])

    def test_published_compiler_rows_reproduce_from_canonical_inputs(self):
        spec = importlib.util.spec_from_file_location('compiled_coverage', ROOT / 'scripts/compiled-coverage.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        trace = read('evidence/5.0.2-build104/compiler/release-inputs.json')
        ledgers = [read('scope/' + name) for name in
                   ('inventory.json', 'upstream-xcode-packages.json', 'upstream-swiftdraw.json')]
        rows = module.join(trace, *ledgers)
        self.assertEqual(rows, read('evidence/5.0.2-build104/compiler/dispositions.json')['files'])
