#!/bin/sh
set -eu
source_root=$1
output=$2
audit_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$output"
swiftc "$source_root/Packages/OathAnkr/Sources/OathAnkr/SolanaModels.swift" \
  "$source_root/Packages/OathAnkr/Sources/OathAnkr/WalletConnectJSON.swift" \
  "$audit_root/tests/WalletConnectJSONAdversarial.swift" -o "$output/parser-check"
"$output/parser-check"
