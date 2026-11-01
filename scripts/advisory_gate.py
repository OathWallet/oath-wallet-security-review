#!/usr/bin/env python3
"""Retain raw OSV results; gate on exact selected-source advisory dispositions."""
import argparse
import hashlib
import json
from pathlib import Path
from go_advisory_triage import classify
from source_state import require_source_state


def evaluate(scan, inventory, scanner_exit, commit, mod_sha, sum_sha):
    if scanner_exit not in (0, 1):
        raise ValueError('Scanner execution failed; cannot classify as a clean scan')
    if inventory.get('source_commit') != commit:
        raise ValueError('Selected-source inventory is for another application commit')
    if inventory.get('go_mod_sha256') != mod_sha or inventory.get('go_sum_sha256') != sum_sha:
        raise ValueError('Selected-source dependency lock hashes differ')
    if not isinstance(scan, dict) or not isinstance(scan.get('results'), list):
        raise ValueError('Missing structured raw scanner results')
    count = 0
    for result in scan['results']:
        if not isinstance(result, dict) or not isinstance(result.get('packages'), list):
            raise ValueError('Malformed raw package results')
        for package in result['packages']:
            if not isinstance(package, dict) or not isinstance(package.get('vulnerabilities'), list):
                raise ValueError('Missing raw advisory list')
            count += len(package['vulnerabilities'])
    if bool(count) != (scanner_exit == 1):
        raise ValueError('Raw scanner exit and advisory report disagree')
    if count:
        result = classify(scan, inventory)
    else:
        # A clean raw scan still requires the exact target inventory. Reuse the
        # classifier's graph checks without inventing a synthetic advisory.
        targets = inventory.get('targets', [])
        if len(targets) != 3 or {t.get('target') for t in targets} != {'mac','ios','sim'} or any(not t.get('packages') for t in targets):
            raise ValueError('All three nonempty selected-source targets are required')
        result = dict(source_commit=commit, advisories=[], unresolved=0, binary_clearance=False,
                      limitations=['A clean module scan is not a whole-wallet or binary-equivalence verdict.'])
    result.update(raw_scanner_exit_code=scanner_exit, raw_advisory_occurrences=count,
                  gate_status='passed' if result['unresolved'] == 0 else 'failed')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('scan',type=Path)
    p.add_argument('inventory',type=Path);p.add_argument('scanner_exit',type=Path)
    p.add_argument('output',type=Path);p.add_argument('--commit',required=True)
    a=p.parse_args();require_source_state(a.source,a.commit)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result=evaluate(json.loads(a.scan.read_text()),json.loads(a.inventory.read_text()),int(a.scanner_exit.read_text().strip()),
                    a.commit,digest(a.source/'Tools/AezeedBridge/go.mod'),digest(a.source/'Tools/AezeedBridge/go.sum'))
    result.update(raw_scan_sha256=digest(a.scan),selected_inventory_sha256=digest(a.inventory))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['raw_advisory_occurrences']} raw advisory occurrences; {result['unresolved']} unresolved; selected-source gate {result['gate_status']}")
    return 0 if result['gate_status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
