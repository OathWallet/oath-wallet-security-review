#!/usr/bin/env python3
"""Compare pinned wordlist resources; this is data verification, not crypto proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from source_state import require_source_state

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('wallet_core', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
config = json.loads((Path(__file__).resolve().parents[1]/'scope/source.json').read_text())
commit = require_source_state(a.source, config['reviewed_commit'])
upstream = 'd40d24a63d92619167903369308bf0e2f7eb3a59'
require_source_state(a.wallet_core, upstream)
module = json.loads(subprocess.check_output(['go', 'list', '-mod=readonly', '-m', '-json', 'github.com/lightningnetwork/lnd'], cwd=a.source/'Tools/AezeedBridge', text=True))
if module['Version'] != 'v0.19.3-beta' or module.get('Replace'):
    raise ValueError('Unexpected LND source')
lnd = Path(module['Dir'])/'aezeed/wordlist.go'
resources = list((a.source/'Packages/OathAezeed/Sources').glob('**/english.txt'))
if len(resources) != 1: raise ValueError('Ambiguous app wordlist')
app = resources[0]
trezor = a.wallet_core/'trezor-crypto/include/TrezorCrypto/bip39_english.h'
words = re.search(r'var englishWordList = `([^`]+)`', lnd.read_text()).group(1).splitlines()
if len(words) != 2048 or len(set(words)) != 2048 or words != app.read_text().splitlines() or words != re.findall(r'"([a-z]+)"', trezor.read_text()):
    raise ValueError('Wordlist identity mismatch')
result = {'status': 'passed', 'source_commit': commit, 'word_count': 2048, 'order_equal': True, 'unique': True, 'sources': [
    {'path':'github.com/lightningnetwork/lnd@v0.19.3-beta/aezeed/wordlist.go','sha256':hashlib.sha256(lnd.read_bytes()).hexdigest()},
    {'path':str(app.relative_to(a.source)), 'sha256':hashlib.sha256(app.read_bytes()).hexdigest()},
    {'path':str(trezor.relative_to(a.wallet_core)), 'commit':upstream, 'sha256':hashlib.sha256(trezor.read_bytes()).hexdigest()}]}
a.output.write_text(json.dumps(result, indent=2)+'\n')
print('2048 unique words match all three pinned resources, including order')
