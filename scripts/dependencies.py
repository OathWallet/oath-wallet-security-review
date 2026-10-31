#!/usr/bin/env python3
"""Inventory pins/licenses and network/build surfaces. This is not a code review."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
source = a.source.resolve()
names = subprocess.check_output(['git','-C',str(source),'ls-files','-z'],text=True).split('\0')
pins, licenses, binaries, surfaces = [], [], [], []
for name in filter(None,names):
    path = source/name
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if path.name == 'Package.resolved':
        value = json.loads(data)
        for pin in value.get('pins',value.get('object',{}).get('pins',[])):
            pins.append({'manifest':name,'identity':pin.get('identity',pin.get('package')),
                         'url':pin.get('location',pin.get('repositoryURL')),'state':pin['state']})
    if any(word in path.name.upper() for word in ['LICENSE','NOTICE','COPYING']):
        licenses.append({'path':name,'sha256':digest})
    if path.suffix in ['.a','.dylib'] or '.xcframework/' in name or path.name in ['go.mod','go.sum']:
        binaries.append({'path':name,'sha256':digest,'bytes':len(data)})
    if not name.startswith(('Website/','Vendor/')) and path.suffix in ['.swift','.plist','.entitlements','.pbxproj']:
        text = data.decode('utf-8',errors='replace')
        for line, content in enumerate(text.splitlines(),1):
            if re.search(r'URLSession|NWConnection|WKWebView|SecItem|SecRandom|AnySigner|https?://|application-groups|keychain-access-groups|associated-domains',content):
                # Only source locations are published; do not dump arbitrary values.
                surfaces.append({'path':name,'line':line,'status':'candidate-requires-trace'})
a.output.mkdir(parents=True,exist_ok=True)
for filename,value in [('dependencies',pins),('licenses',licenses),('binaries',binaries),('entry-points',surfaces)]:
    (a.output/(filename+'.json')).write_text(json.dumps(value,indent=2)+'\n')
print(f'{len(pins)} lockfile pins, {len(licenses)} notices, {len(binaries)} binary/module records, {len(surfaces)} candidate entry points')
