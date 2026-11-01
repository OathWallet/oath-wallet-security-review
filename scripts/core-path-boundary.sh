#!/bin/sh
# Replay the production public C API from the pinned upstream checkout.
set -eu
root=$(cd "$1" && pwd)
audit=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
test "$(git -C "$root" rev-parse HEAD)" = d40d24a63d92619167903369308bf0e2f7eb3a59
test -z "$(git -C "$root" status --porcelain --untracked-files=normal)"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
ccflags='-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
# TWCoinType includes a generated header. Run the exact upstream generator in
# scratch, leaving the source pin clean. Compile using its generated include tree.
git -C "$root" archive HEAD codegen registry.json include rust/tw_coin_registry/src/tw_derivation.rs > "$scratch/codegen.tar"
tar -xf "$scratch/codegen.tar" -C "$scratch"
mkdir -p "$scratch/docs"
(cd "$scratch" && ruby codegen/bin/coins)
clang --version
clang $ccflags -c "$root/trezor-crypto/crypto/memzero.c" -o "$scratch/memzero.o"
clang++ $ccflags -std=c++17 -I"$scratch/include" -I"$root/trezor-crypto/include" \
    "$audit/fixtures/core-path/derivation_path.cpp" "$root/src/DerivationPath.cpp" \
    "$root/src/interface/TWDerivationPath.cpp" "$root/src/interface/TWDerivationPathIndex.cpp" \
    "$root/src/interface/TWString.cpp" "$scratch/memzero.o" -o "$scratch/core-path"
"$scratch/core-path"
