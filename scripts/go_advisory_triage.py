#!/usr/bin/env python3
"""Classify raw module advisories by selected packages, never by text heuristics."""
import argparse
import hashlib
import json
from pathlib import Path


def classify(scan, inventory):
    targets = inventory.get('targets', [])
    if {t.get('target') for t in targets} != {'mac', 'ios', 'sim'} or len(targets) != 3:
        raise ValueError('All three reviewed targets are required')
    if any(not t.get('packages') for t in targets):
        raise ValueError('Empty dependency graph')
    vulnerabilities = {}
    occurrences = []
    for result in scan.get('results', []):
        for item in result.get('packages', []):
            module = item['package']['name']
            version = item['package']['version'].removeprefix('v')
            if inventory.get('module_graph', {}).get(module, '').removeprefix('v') != version:
                raise ValueError('Scanner and selected module versions differ')
            for advisory in item.get('vulnerabilities', []):
                vulnerabilities[advisory['id']] = advisory
                occurrences.append((module, item['package']['version'], advisory))
    if not occurrences:
        raise ValueError('Expected unfiltered module advisory evidence')
    output = []
    for module, version, advisory in occurrences:
        evidence = []
        # A GHSA can lack package-level metadata. Resolve only explicitly
        # declared Go advisory aliases present in the SAME raw scan result.
        candidates = [advisory] + [vulnerabilities[a] for a in advisory.get('aliases', [])
                                   if a.startswith('GO-') and a in vulnerabilities]
        imports = set()
        for candidate in candidates:
            for affected in candidate.get('affected', []):
                if affected.get('package', {}).get('name') != module:
                    continue
                values = affected.get('ecosystem_specific', {}).get('imports', [])
                paths = {i['path'] for i in values if i.get('path')}
                if paths:
                    imports.update(paths)
                    evidence.append(candidate['id'])
        intersections = {}
        for target in targets:
            selected = {p['import_path'] for p in target['packages']}
            intersections[target['target']] = sorted(imports & selected)
        matched = any(intersections.values())
        status = 'potentially-reachable' if matched else 'not-compiled' if imports else 'unresolved-metadata'
        output.append({'id': advisory['id'], 'module': module, 'version': version,
                       'affected_import_paths': sorted(imports), 'metadata_evidence_ids': sorted(set(evidence)),
                       'selected_intersections': intersections, 'status': status})
    return {'source_commit': inventory['source_commit'], 'advisories': output,
            'unresolved': sum(x['status'] != 'not-compiled' for x in output),
            'binary_clearance': False,
            'limitations': ['Source-selection evidence only; historical archive provenance remains unresolved.',
                            'No module-level advisory is deleted or suppressed.',
                            'Any new advisory without exact import-path metadata remains unresolved.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('scan', type=Path)
    p.add_argument('inventory', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    result = classify(json.loads(a.scan.read_text()), json.loads(a.inventory.read_text()))
    result['raw_scan_sha256'] = hashlib.sha256(a.scan.read_bytes()).hexdigest()
    result['source_inventory_sha256'] = hashlib.sha256(a.inventory.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{len(result['advisories'])} raw advisories; {result['unresolved']} unresolved source-reachability dispositions")
    raise SystemExit(1 if result['unresolved'] else 0)
