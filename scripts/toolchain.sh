#!/bin/sh
set -eu
mkdir -p evidence/ci
{
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  uname -a
  xcodebuild -version
  swift --version
  python3 --version
  git --version
} > evidence/ci/toolchain.txt
grep -q "Xcode ${OATH_REVIEW_XCODE:-27.0}" evidence/ci/toolchain.txt
grep -q 'Swift version 6.4' evidence/ci/toolchain.txt
