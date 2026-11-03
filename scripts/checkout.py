#!/usr/bin/env python3
"""Prepare an exact clean source tree without publishing partial downloads."""
import json
from pathlib import Path
import subprocess
import tempfile

from source_state import require_source_state


def checkout(repository, revision, source, *, attempts=3, timeout=600):
    source = Path(source)
    if source.exists():
        require_source_state(source, revision)
        return revision
    source.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        # Keep the complete history: paired audit replays need older objects.
        # Each failed download stays isolated from the expected source path.
        with tempfile.TemporaryDirectory(prefix='.source-download-', dir=source.parent) as temporary:
            staged = Path(temporary) / 'source'
            try:
                subprocess.run(['git', 'clone', '--no-checkout', repository, str(staged)],
                               check=True, timeout=timeout)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if attempt + 1 == attempts:
                    raise
                print(f'Source download attempt {attempt + 1} failed; retrying in a fresh directory.', flush=True)
                continue
            # Invalid pins or dirty trees are validation failures, not network retries.
            subprocess.run(['git', '-C', str(staged), 'checkout', '--detach', revision],
                           check=True, timeout=timeout)
            require_source_state(staged, revision)
            if source.exists():
                raise ValueError('Source appeared during download; preserve it and use a fresh workspace')
            staged.rename(source)
            return revision
    raise ValueError('At least one download attempt is required')


def main():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'scope/source.json').read_text())
    revision = checkout(config['repository'], config['reviewed_commit'], root / '.work/source')
    print('Pinned clean source ready:', revision)


if __name__ == '__main__':
    main()
