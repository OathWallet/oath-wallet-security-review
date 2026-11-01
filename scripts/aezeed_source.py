"""Select the same source preparation as the reviewed bridge's build script."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
from bounded_process import logged_command


@contextmanager
def prepared_bridge(source, output=None):
    bridge = source/'Tools/AezeedBridge'
    preparer = bridge/'prepare_source.py'
    if not preparer.exists():
        yield bridge, None
        return
    with tempfile.TemporaryDirectory(prefix='oath-audit-aezeed-source-') as directory:
        work = Path(directory)
        log = (output/'prepare-source.log') if output else work/'prepare-source.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR']}
        with log.open('w') as stream:
            code, expired = logged_command(['python3',str(preparer),str(work/'source')],
                                           stream=stream, timeout=900, env=env)
        if code or expired:
            raise RuntimeError('Verified source preparation failed; see '+str(log))
        raw = (work/'source/prepared-source.json').read_bytes()
        manifest = json.loads(raw)
        expected = json.loads((bridge/'DependencyRepairs.json').read_text())
        if manifest['patch_sha256'] != expected['patch_sha256'] or manifest['repairs'] != expected['files']:
            raise ValueError('Prepared source does not match the application repair manifest')
        selected = work/'source/Tools/AezeedBridge'
        declared = manifest['vendor_files'] | manifest['source_files']
        actual = {str(p.relative_to(selected)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in selected.rglob('*') if p.is_file()}
        if actual != declared:
            raise ValueError('Prepared source tree differs from its complete hash inventory')
        if output:
            (output/'prepared-source.json').write_bytes(raw)
        yield selected, manifest
        after = {str(p.relative_to(selected)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in selected.rglob('*') if p.is_file()}
        if after != declared:
            raise ValueError('Prepared source changed during validation')
