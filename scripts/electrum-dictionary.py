#!/usr/bin/env python3
"""Compare Electrum's ordered original Python tuple with Oath's shipped word-list resource."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
from source_state import require_source_state

REVISION = 'a8b86f2c725ffad4e52d7fa5912906be914f1999'
RESOURCE = 'electrum-old-words.txt'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def word_list(code):
    assignments = [node.value for node in ast.parse(code).body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == '_words' for target in node.targets)]
    if len(assignments) != 1 or not isinstance(assignments[0], ast.Tuple):
        raise ValueError('Expected exactly one literal tuple for the upstream Electrum dictionary')
    words = ast.literal_eval(assignments[0])
    if len(words) != 1626 or len(set(words)) != 1626 or any(not isinstance(w, str) or not w.isascii() or not w.isalpha() for w in words):
        raise ValueError('Unexpected upstream Electrum dictionary')
    return words

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('source', 'app', 'framework_result', 'output'):
        parser.add_argument(field, type=Path)
    args = parser.parse_args()
    framework = json.loads(args.framework_result.read_bytes())
    pin = require_source_state(args.source, framework['source_commit'])
    binary = plistlib.loads((args.app/'Info.plist').read_bytes())['CFBundleExecutable']
    binary_hash = sha((args.app/binary).read_bytes())
    if framework['status'] != 'passed' or binary_hash != framework['embedded'][binary]['sha256']:
        raise ValueError('Release product identity mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['git', 'init', '-q', tmp], check=True)
        subprocess.run(['git', '-C', tmp, 'fetch', '--quiet', '--depth=1', 'https://github.com/spesmilo/electrum.git', REVISION], check=True)
        upstream = subprocess.check_output(['git', '-C', tmp, 'show', REVISION+':electrum/old_mnemonic.py'])
    words = word_list(upstream)
    source_path = 'Packages/OathBitcoin/Sources/OathBitcoin/Resources/'+RESOURCE
    raw = (args.source/source_path).read_bytes()
    resources = list(args.app.rglob(RESOURCE))
    if len(resources) != 1 or raw != resources[0].read_bytes() or tuple(raw.decode().splitlines()) != words:
        raise ValueError('Legacy Electrum dictionary differs across upstream, source or product')
    result = dict(check='electrum-dictionary', source_commit=pin, status='passed', words=len(words),
                  upstream_revision=REVISION, upstream_source_sha256=sha(upstream), dictionary_sha256=sha(raw),
                  app_binary_sha256=binary_hash, source_path=source_path, bundle_path=str(resources[0].relative_to(args.app)))
    args.output.mkdir(parents=True, exist_ok=True)
    log = args.output/'electrum-dictionary.log'
    log.write_text(json.dumps(result, indent=2)+'\n')
    result.update(log=log.name, log_sha256=sha(log.read_bytes()))
    (args.output/'electrum-dictionary.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Verified all',len(words),'Electrum legacy dictionary positions')

if __name__ == '__main__':
    main()
