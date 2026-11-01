#!/bin/sh
set -eu
source_dir=$(cd "$1" && pwd)
mkdir -p "$2" "$3"
scratch=$(cd "$2" && pwd)
out=$(cd "$3" && pwd)
test "$(git -C "$source_dir" rev-parse HEAD)" = 82699f4bdf2f075793cfa0d392eb27c59b41a3fe
test -z "$(git -C "$source_dir" status --porcelain --untracked-files=normal)"
swift --version > "$out/toolchain.txt"
# SwiftDraw declares no external packages. Build the upstream tests without modifying them.
swift build --package-path "$source_dir" --build-tests --jobs 4 --build-system native --scratch-path "$scratch" > "$out/dom-build.log" 2>&1
/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' \
    swift test --package-path "$source_dir" --disable-sandbox --skip-build --disable-xctest --enable-swift-testing \
    --build-system native --scratch-path "$scratch" --filter SwiftDrawDOMTests > "$out/dom.log" 2>&1
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,re,sys
out=Path(sys.argv[1]);log=out/'dom.log';text=log.read_text()
assert re.findall(r'Test run with (\d+) tests in (\d+) suites passed',text)==[('167','22')]
assert len(re.findall(r'^.*? Test (?!run with ).+ passed after ',text,re.M))==167
assert not re.search(r'^.*? (?:Test|Suite) .+ (?:failed|skipped)',text,re.M)
result=dict(check='swiftdraw-dom',status='passed',source_commit='82699f4bdf2f075793cfa0d392eb27c59b41a3fe',tests=167,suites=22,log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),scope='Pinned upstream Swift Testing DOM suites on macOS with network denied. Excludes renderer XCTest and CLI execution.')
(out/'dom.json').write_text(json.dumps(result,indent=2)+'\n')
print('167 upstream DOM tests in 22 suites passed')
PY
