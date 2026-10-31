#!/usr/bin/env python3
"""Hash tracked source without interpreting a scanner result as human review."""
import argparse, hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inventory(source):
    config = json.loads((ROOT / 'scope/source.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != config['reviewed_commit']:
        raise ValueError('Source commit does not match pinned review')
    decisions = json.loads((ROOT / 'review/dispositions.json').read_text())
    paths = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).decode().split('\0')
    records = []
    for name in sorted(filter(None, paths)):
        path = source / name
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        category = ('dependency' if name.startswith('Vendor/') or '.xcframework/' in name else
                    'test' if '/Tests/' in name or name.startswith(('Tests/', 'Tools/Check', 'Tools/Test')) else
                    'website' if name.startswith('Website/') else
                    'application' if name.startswith(('OathApp/', 'OathAtmosphere/', 'Packages/')) else 'build-or-documentation')
        decision = decisions.get(name, {})
        if decision and decision.get('sha256') != digest:
            raise ValueError('Stale review disposition: ' + name)
        records.append(dict(path=name, sha256=digest, bytes=len(data), category=category,
                            status=decision.get('status', 'outstanding'),
                            evidence=decision.get('evidence', [])))
    return dict(source_commit=commit, files=records)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.source.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"Inventoried {len(result['files'])} files; status is explicit, never inferred from tests.")
