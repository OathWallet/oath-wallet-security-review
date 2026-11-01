import importlib.util
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location('host_policy', scripts / 'artwork-host-policy.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def transcript(case, status, errors=()):
    name = f'-[{policy.SUITE} {case}]'
    lines = [f"Test Case '{name}' started."]
    lines.extend(f'fixture.swift:1: error: {name} : {error}' for error in errors)
    lines.append(f"Test Case '{name}' {status} (0.1 seconds).")
    return '\n'.join(lines)


class ArtworkHostEvidenceTests(unittest.TestCase):
    def test_before_requires_every_literal_failure_once(self):
        case = 'testResolverRecognizedIPv4SpellingsAreRejected'
        errors = ['XCTAssertFalse failed - ' + host for host in policy.literal_inputs]
        good = transcript(case, 'failed', errors)
        self.assertEqual(policy.outcome(good, 1, case, True), 'expected-admission-failure')
        for invalid in [errors[:-1], errors + errors[:1], errors[:-1] + errors[:1], ['unrelated'] + errors[1:]]:
            self.assertEqual(policy.outcome(transcript(case, 'failed', invalid), 1, case, True), 'failed')
        self.assertEqual(policy.outcome(good, 1, case, False), 'failed')
        self.assertEqual(policy.outcome(good, 124, case, True), 'failed')

    def test_controls_and_repaired_cases_require_an_actual_pass(self):
        for case in policy.CASES:
            good = transcript(case, 'passed')
            self.assertEqual(policy.outcome(good, 0, case, False), 'passed')
            self.assertEqual(policy.outcome(good, 0, case, True), 'failed' if case in policy.EXPECT else 'passed')
            for invalid in [transcript(case, 'skipped'), good + '\n' + good, good + '\nfile: error: other', '']:
                self.assertEqual(policy.outcome(invalid, 0, case, False), 'failed')

    def test_unexpected_test_identity_is_rejected(self):
        case = 'testRedirectRejectsNumericHost'
        text = transcript(case, 'failed', ['XCTAssertNil failed: "https://0x7f.0.0.1/asset"'])
        self.assertEqual(policy.outcome(text, 1, case, True), 'expected-admission-failure')
        self.assertEqual(policy.outcome(text.replace(policy.SUITE, 'UnrelatedTests'), 1, case, True), 'failed')
        self.assertEqual(policy.outcome(text, 1, 'unlisted', True), 'failed')
