import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('solana_vectors', Path(__file__).resolve().parents[1] / 'scripts/solana-vector-isolation.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SolanaVectorIsolationTests(unittest.TestCase):
    def declarations(self):
        return '\n'.join(
            f'    func testOfficialSquads{label}Vector{i:02d}() throws {{ try verifyOfficialSquadsVectors(kind: "{kind}", index: {i}) }}'
            for label, kind in m.KINDS.items() for i in range(19)
        )

    def testEveryVectorHasAUniqueSelector(self):
        cases = m.selectors(self.declarations())
        self.assertEqual(len(cases), 76)
        self.assertEqual(len(set(cases)), 76)

    def testMissingDuplicateAndExtraVectorsAreRejected(self):
        lines = self.declarations().splitlines()
        for bad in ['\n'.join(lines[1:]), '\n'.join(lines[:-1] + [lines[0]]), '\n'.join(lines + [lines[0]])]:
            with self.assertRaises(ValueError):
                m.selectors(bad)

    def testKindAndIndexMustMatchTheDeclaredTest(self):
        source = self.declarations()
        for bad in [source.replace('index: 0)', 'index: 1)', 1), source.replace('kind: "setup"', 'kind: "spl"', 1)]:
            with self.assertRaises(ValueError):
                m.selectors(bad)

    def testOnlyTheRequestedCompletedCasePasses(self):
        selector = m.selectors(self.declarations())[0]
        cls, method = selector.split('/')
        for name in [f'-[{cls} {method}]', f'{cls.split(".")[-1]}.{method}']:
            output = f"Test Case '{name}' started.\nTest Case '{name}' passed (0.01 seconds).\n"
            self.assertEqual(m.classify(output, 0, selector), 'passed')
            for bad in ['', output + output, output.replace('passed', 'skipped'), output.replace('passed', 'failed'), output.replace(method, 'unrelatedTest'), output + 'file:1: error: unrelated\n']:
                self.assertEqual(m.classify(bad, 0, selector), 'failed')
            self.assertEqual(m.classify(output, 1, selector), 'failed')

    def testAssertionBodyCannotSilentlyBeEmptyOrMissing(self):
        prefix = '            let p = try plan(row), policy = p.multisig!.policy\n'
        body = prefix + '            XCTAssertEqual(actual, expected)'
        self.assertEqual(m.assertion_body('before\n' + body + '\n        }\n    }\n    func testMainnetAndDevnet'), body)
        for bad in ['', body, '\n        }\n    }\n    func testMainnetAndDevnet']:
            with self.assertRaises(ValueError):
                m.assertion_body(bad)
