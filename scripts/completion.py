#!/usr/bin/env python3
"""Completion is distinct from a passing CI suite."""
import json
from pathlib import Path

def gaps(config, inventory, findings):
    result = []
    if inventory['source_commit'] != config['reviewed_commit']: result.append('source mismatch')
    for item in inventory['files']:
        if item['category'] != 'website' and item['status'] not in ['reviewed','non-security-content','generated-verified']: result.append(item['path'])
    for finding in findings:
        if finding['status'] not in ['fixed-and-retested','documented-limitation']: result.append(finding['id'])
    return result

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    pending = gaps(json.loads((root/'scope/source.json').read_text()),
                   json.loads((root/'scope/inventory.json').read_text()),
                   json.loads((root/'findings/index.json').read_text()))
    print(f'{len(pending)} outstanding review items. This is not an audit-completion certificate.')
    raise SystemExit(1 if pending else 0)
