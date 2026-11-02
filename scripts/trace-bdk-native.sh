#!/bin/sh
# Run after the isolated device reconstruction. All new outputs go into a fresh directory.
set -eu
[ "$#" = 2 ] || { echo 'usage: trace-bdk-native.sh isolated-reconstruction new-scratch' >&2; exit 2; }
[ "$(uname -sm)" = 'Darwin arm64' ]
original=$(cd "$1" && pwd); scripts=$(cd "$(dirname "$0")" && pwd)
mkdir "$2"; scratch=$(cd "$2" && pwd); mkdir "$scratch/cc" "$scratch/trace"
for driver in clang clang++; do ln -s "$scripts/bdk-clang-trace.py" "$scratch/cc/$driver"; done
case "${BDK_BUILD_LAYOUT:-isolated}" in
    isolated) source_dir="$original/bdk-ffi"; toolchains="$original/toolchains"; cargo_dir="$original/cargo" ;;
    publisher|publisher-rust-src)
        [ "${RUNNER_ENVIRONMENT:-}" = github-hosted ] && [ "$HOME" = /Users/runner ] || exit 2
        source_dir="$HOME/work/bdk-swift/bdk-swift/build/bdk-ffi"; toolchains="$HOME/.rustup"; cargo_dir="$HOME/.cargo" ;;
    *) exit 2 ;;
esac
cd "$source_dir"
printf '%s\n' 'a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9  Cargo.lock' | shasum -a 256 -c -
env -i HOME="$HOME" PATH="$cargo_dir/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
    RUSTUP_HOME="$toolchains" CARGO_HOME="$cargo_dir" RUSTUP_TOOLCHAIN=1.90.0 \
    DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}" IPHONEOS_DEPLOYMENT_TARGET=15.0 \
    CC_aarch64_apple_ios="$scratch/cc/clang" CXX_aarch64_apple_ios="$scratch/cc/clang++" \
    OATH_BDK_CLANG="$(xcrun --find clang)" OATH_BDK_CLANGXX="$(xcrun --find clang++)" \
    OATH_BDK_TRACE="$scratch/trace" CARGO_TARGET_DIR="$scratch/target" \
    "$cargo_dir/bin/cargo" build --locked --offline --package bdk-ffi --profile release-smaller \
    --target aarch64-apple-ios --jobs 4 --message-format=json > "$scratch/messages.jsonl"
