"""Use the pinned TrustedCoin scheme selection and upstream KDF with an independent address oracle."""
import argparse
import ast
import base64
import hashlib
import hmac
import json
from pathlib import Path
import string
import subprocess
import unicodedata

REVISION = 'a8b86f2c725ffad4e52d7fa5912906be914f1999'

def upstream_functions(root):
    mnemonic = ast.parse((root/'electrum/mnemonic.py').read_bytes())
    trustedcoin = ast.parse((root/'electrum/plugins/trustedcoin/trustedcoin.py').read_bytes())
    namespace = {'unicodedata': unicodedata, 'string': string, 'hashlib': hashlib}

    def load(nodes):
        exec(compile(ast.Module(body=nodes,type_ignores=[]), '<pinned-electrum>', 'exec'), namespace)

    load([node for node in mnemonic.body if isinstance(node,ast.Assign) and
          any(getattr(target,'id',None) == 'CJK_INTERVALS' for target in node.targets)])
    load([node for node in mnemonic.body if isinstance(node,ast.FunctionDef) and node.name in ('is_CJK','normalize_text')])
    for tree, name in [(mnemonic,'mnemonic_to_seed'),(trustedcoin,'xkeys_from_seed')]:
        method, = [method for cls in tree.body if isinstance(cls,ast.ClassDef)
                   for method in cls.body if isinstance(method,ast.FunctionDef) and method.name == name]
        method.decorator_list = []
        method.returns = None
        for arg in method.args.args + method.args.kwonlyargs:
            arg.annotation = None
        load([method])
    # Isolate the already-identified 2fa branch. Confirmed seed versions are checked below.
    namespace.update(calc_seed_type=lambda _: '2fa', is_any_2fa_seed_type=lambda kind: kind == '2fa')
    return namespace

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('electrum','address_oracle','app'):
        parser.add_argument(field, type=Path)
    args = parser.parse_args()
    source = args.electrum.resolve()
    revision = subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True).strip()
    dirty = subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'])
    if dirty or revision != REVISION:
        raise ValueError('Expected the unmodified Electrum 4.6.2 checkout')
    upstream = upstream_functions(source)

    class DerivationProbe:
        def get_xkeys(self, words, kind, password, path):
            return upstream['mnemonic_to_seed'](None,words,passphrase=password), path

    def derive(phrase, password):
        if not hmac.digest(b'Seed version', upstream['normalize_text'](phrase).encode(), 'sha512').hex().startswith('101'):
            raise ValueError('Wrong Electrum two-factor seed version')
        first,path1,second,path2 = upstream['xkeys_from_seed'](DerivationProbe(),phrase,password)
        legacy = path1 == 'm/'
        payload = {'seeds':[base64.b64encode(key).decode('ascii') for key in (first,second)],'legacy':legacy}
        address = subprocess.check_output([args.address_oracle.resolve()], input=json.dumps(payload).encode()).decode().strip()
        return first,second,[path1,path2],address

    controls = args.app/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures/electrum-reference.json'
    covered = set()
    for row in json.loads(controls.read_bytes()):
        if row['kind'] == '2fa':
            _,_,paths,address = derive(row['phrase'],row['password'])
            expected = next(item['address'] for item in row['addresses'] if item['change'] == 0 and item['index'] == 0)
            if address != expected:
                raise ValueError('Existing address fixture did not match')
            covered.add(paths[0])
    if covered != {'m/', "m/0'/"}:
        raise ValueError('Missing a TrustedCoin control scheme')
    results = {}
    for kind,length in [('post27',12),('pre27',24)]:
        for index in range(50_000):
            words = [chr(0x4e00+j) for j in range(length-1)] + [chr(0x4e00+index%512)+chr(0x5000+index//512)]
            phrase = ' '.join(words)
            if hmac.digest(b'Seed version',upstream['normalize_text'](phrase).encode(),'sha512').hex().startswith('101'):
                break
        else:
            raise ValueError('Synthetic search exhausted')
        first,second,paths,address = derive(phrase,'')
        results[kind] = dict(length=length, iteration=index, firstSeedHash=hashlib.sha256(first).hexdigest(),
                             secondSeedHash=hashlib.sha256(second).hexdigest(), branches=paths, firstReceiveAddress=address)
    print(json.dumps(results,indent=2))

if __name__ == '__main__':
    main()
