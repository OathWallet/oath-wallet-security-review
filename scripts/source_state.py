"""Reject uncommitted inputs before claiming evidence for a pinned source tree."""
import subprocess

def require_source_state(source, expected_commit):
    actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected_commit:
        raise ValueError('Wrong source revision')
    # Nonignored untracked Swift/C files can be discovered automatically by build
    # systems, so checking tracked modifications alone is insufficient.
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=normal'])
    if dirty.strip():
        raise ValueError('Source has modified or untracked inputs; use a clean checkout')
    return actual
