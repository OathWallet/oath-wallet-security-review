#!/bin/sh
# Use a new scratch directory, a clean checkout of the publisher revision and an isolated Rust install.
set -eu
[ "$#" = 3 ] || { echo 'usage: rebuild-bdk-ios.sh bdk-ffi-checkout empty-scratch resolved-ios-lib.a' >&2; exit 2; }
[ "$(uname -sm)" = 'Darwin arm64' ]
bridge=$(cd "$1" && pwd)
mkdir "$2"
scratch=$(cd "$2" && pwd)
published=$(cd "$(dirname "$3")" && pwd)/$(basename "$3")
scripts=$(cd "$(dirname "$0")" && pwd)
rev=1c5f4863c6a53cc9d063d34c4e13c91fea5c58de
[ "$(git -C "$bridge" rev-parse HEAD)" = "$rev" ]
cd "$scratch"
curl -fsSL --retry 2 --max-time 90 -o rustup-init https://static.rust-lang.org/rustup/archive/1.28.2/aarch64-apple-darwin/rustup-init
curl -fsSL --retry 2 --max-time 90 -o channel-rust-1.90.0.toml https://static.rust-lang.org/dist/channel-rust-1.90.0.toml
printf '%s\n' '20ef5516c31b1ac2290084199ba77dbbcaa1406c45c1d978ca68558ef5964ef5  rustup-init' '489c19f20d331765ab2835661eb546de90f6446a107a8db83045e7371e45cae2  channel-rust-1.90.0.toml' | shasum -a 256 -c -
chmod 700 rustup-init
export RUSTUP_HOME="$scratch/toolchains" CARGO_HOME="$scratch/cargo" RUSTUP_INIT_SKIP_PATH_CHECK=yes
./rustup-init -y --no-modify-path --profile minimal --default-toolchain 1.90.0 --target aarch64-apple-ios
git -C "$bridge" archive --output="$scratch/bridge.tar" "$rev" bdk-ffi
tar xf bridge.tar
export RUSTUP_TOOLCHAIN=1.90.0
export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"
"$scratch/cargo/bin/rustc" -vV | grep -Fx 'commit-hash: 1159e78c4747b02ef996e55082b704c09b970588'
cd bdk-ffi
printf '%s\n' 'a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9  Cargo.lock' | shasum -a 256 -c -
env -i HOME="$HOME" DEVELOPER_DIR="$DEVELOPER_DIR" PATH="$scratch/cargo/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" RUSTUP_HOME="$RUSTUP_HOME" RUSTUP_TOOLCHAIN=1.90.0 CARGO_HOME="$CARGO_HOME" IPHONEOS_DEPLOYMENT_TARGET=15.0 "$scratch/cargo/bin/cargo" build --locked --package bdk-ffi --profile release-smaller --target aarch64-apple-ios --jobs 4 --message-format=json > "$scratch/artifacts.jsonl"
python3 "$scripts/bdk-build-packages.py" "$scratch/artifacts.jsonl" Cargo.lock "$CARGO_HOME" target "$scratch/packages.json"
python3 "$scripts/compare-bdk-archives.py" "$published" target/aarch64-apple-ios/release-smaller/libbdkffi.a "$scratch/comparison.json"
