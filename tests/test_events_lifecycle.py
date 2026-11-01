import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('events_lifecycle', Path(__file__).resolve().parents[1] / 'scripts/events-lifecycle.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EventsLifecycleEvidenceTests(unittest.TestCase):
    def transcript(self, before):
        result = []
        for method, count in m.CASES.items():
            name = f'-[SDKTests.EventsPrivacyLifecycleTests {method}]'
            result.append(f"Test Case '{name}' started.")
            if before:
                result += [f'fixture.swift:1: error: {name} : {detail}' for detail in m.EXPECTED[method]]
            status = 'failed' if before and count else 'passed'
            result.append(f"Test Case '{name}' {status} (0.01 seconds).")
        return '\n'.join(result) + '\n'

    def testExactExpectedFailuresAndPassingControlAreRequired(self):
        text = self.transcript(True)
        self.assertEqual(m.classify(text, 1, True), 'opt-out-defects-reproduced')
        for bad in ['', text + text, text.replace('XCTAssertTrue failed', 'Unexpected crash'), text.replace('Disabled initialization must not retain events', 'unrelated assertion'), text + 'fixture:1: error: unrelated\n']:
            self.assertEqual(m.classify(bad, 1, True), 'failed')
        self.assertEqual(m.classify(text, 0, True), 'failed')
        self.assertEqual(m.classify(text, 1, False), 'failed')

    def testEveryExactCaseMustPassAfterRepair(self):
        text = self.transcript(False)
        self.assertEqual(m.classify(text, 0, False), 'passed')
        for bad in ['', text + text, text.replace('passed', 'skipped'), text.replace('passed', 'failed'), text.replace('testDisabledClientDoesNotCollectOrRetainEvents', 'unrelated'), text + 'fixture:1: error: unrelated\n']:
            self.assertEqual(m.classify(bad, 0, False), 'failed')
        self.assertEqual(m.classify(text, 1, False), 'failed')
        self.assertEqual(m.classify(text, 0, True), 'failed')

    def testAdditionalForeignCaseOrMissingControlCannotPass(self):
        text = self.transcript(False)
        foreign = "Test Case '-[SDKTests.Other testOther]' started.\nTest Case '-[SDKTests.Other testOther]' passed (0.01 seconds).\n"
        self.assertEqual(m.classify(text + foreign, 0, False), 'failed')
        lines = [line for line in text.splitlines() if 'testExplicitlyEnabledClientCanDeliverSyntheticEvents' not in line]
        self.assertEqual(m.classify('\n'.join(lines), 0, False), 'failed')
