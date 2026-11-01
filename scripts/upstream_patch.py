"""Test a published patch in a disposable checkout; never modify the baseline."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import subprocess
import tempfile
from source_state import require_source_state

PATCH = Path(__file__).resolve().parents[1] / 'patches/walletcore-4.8.4-api-repairs.patch'

@contextmanager
def upstream_source(source, pin, repair=False):
    source = source.resolve()
    require_source_state(source, pin)
    if not repair:
        try:
            yield source, None
        finally:
            require_source_state(source, pin)
        return
    patch = PATCH.read_bytes()
    with tempfile.TemporaryDirectory(prefix='oath-core-patched-') as directory:
        checkout = Path(directory)/'source'
        subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(source),str(checkout)],check=True,timeout=120)
        subprocess.run(['git','-C',str(checkout),'checkout','--quiet','--detach',pin],check=True,timeout=120)
        require_source_state(checkout, pin)
        subprocess.run(['git','-C',str(checkout),'apply','--check','-'],input=patch,check=True,timeout=30)
        subprocess.run(['git','-C',str(checkout),'apply','-'],input=patch,check=True,timeout=30)
        def diff():
            return subprocess.check_output(['git','-C',str(checkout),'diff','--binary'])
        before = diff()
        provenance = dict(baseline_commit=pin, patch_path=str(PATCH.relative_to(PATCH.parents[1])),
                          patch_sha256=hashlib.sha256(patch).hexdigest(),
                          applied_diff_sha256=hashlib.sha256(before).hexdigest(),
                          incorporated_in_shipped_framework=False)
        try:
            yield checkout, provenance
        finally:
            if diff()!=before:
                raise ValueError('Patched source changed during validation')
            if subprocess.check_output(['git','-C',str(checkout),'ls-files','--others','--exclude-standard']).strip():
                raise ValueError('Untracked inputs appeared during validation')
            if PATCH.read_bytes()!=patch:
                raise ValueError('Published patch changed during validation')
            require_source_state(source,pin)
