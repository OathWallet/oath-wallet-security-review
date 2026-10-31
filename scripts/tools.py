#!/usr/bin/env python3
"""Install hash-pinned Linux scanner binaries without executing remote scripts."""
import hashlib, io, os, platform, tarfile, urllib.request
from pathlib import Path
root=Path('.work/tools');root.mkdir(parents=True,exist_ok=True)
mac = platform.system() == 'Darwin'
platform_name = 'darwin_arm64' if mac else 'linux_x64'
url=f'https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_{platform_name}.tar.gz'
data=urllib.request.urlopen(url,timeout=120).read()
assert hashlib.sha256(data).hexdigest()== ('b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5' if mac else '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb')
with tarfile.open(fileobj=io.BytesIO(data)) as archive:
    binary=archive.extractfile('gitleaks').read()
(root/'gitleaks').write_bytes(binary);(root/'gitleaks').chmod(0o700)
platform_name = 'darwin_arm64' if mac else 'linux_amd64'
url=f'https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_{platform_name}'
data=urllib.request.urlopen(url,timeout=120).read()
assert hashlib.sha256(data).hexdigest()== ('d4926ef8da134332543be276dff157e4c170f99ad91fc48e89448a8816bdf70b' if mac else '160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b')
(root/'osv-scanner').write_bytes(data);(root/'osv-scanner').chmod(0o700)
print('Verified Gitleaks 8.30.1 and OSV Scanner 2.7.0 release checksums')
