#!/bin/sh
set -eu
source=$1
output=$2
pin=d40d24a63d92619167903369308bf0e2f7eb3a59
[ "$(git -C "$source" rev-parse HEAD)" = "$pin" ]
[ -z "$(git -C "$source" status --porcelain --untracked-files=no)" ]
mkdir -p "$output"
cc --version
cc -std=c11 -Wall -Wextra -Werror -I "$source/trezor-crypto/include" \
  -Dopen=entropy_open -Dread=entropy_read -Dclose=entropy_close \
  -c "$source/trezor-crypto/crypto/rand.c" -o "$output/rand.o"
cc -std=c11 -Wall -Wextra -Werror -I "$source/trezor-crypto/include" \
  tests/UpstreamEntropyFailure.c "$output/rand.o" -o "$output/entropy-tests"
"$output/entropy-tests"
