# Native build recipe

This recipe consolidates the successful recorded preparation commands. The
reusable test runners were executed locally; a fresh GitHub execution of this
entire preparation remains outstanding. It builds host libraries only, not
replacement Apple frameworks. Use a disposable arm64 Mac directory and public
source. No device, signing identity or private credential is required.

Prerequisites: Xcode 27.0, CMake 4.3.4, Ruby 4.0.5, Boost 1.90.0 headers,
Python 3.14.7, Git and curl. The observed build used Homebrew's CMake and Boost
and `/opt/homebrew/opt/ruby/bin` on PATH. Record `xcodebuild -version`,
`clang++ --version`, `cmake --version`, `ruby --version`, and the Boost header
version. Different toolchains require their own validation results.

Set `AUDIT_ROOT` to this audit checkout; `CORE_ROOT` and `CORE_TOOLS` must be
new disposable directories. `BOOST_ROOT` contains the Boost `include` directory.
Do not reuse these variable names for system directories or an unrelated project.

```sh
set -eu
export AUDIT_ROOT=/absolute/path/oath-wallet-security-review
export CORE_ROOT=/tmp/oath-core-native-reproduction
export CORE_TOOLS=/tmp/oath-core-native-tools
export BOOST_ROOT=/opt/homebrew/opt/boost
test ! -e "$CORE_ROOT"
test ! -e "$CORE_TOOLS"
git clone https://github.com/trustwallet/wallet-core.git "$CORE_ROOT"
git -C "$CORE_ROOT" checkout --detach d40d24a63d92619167903369308bf0e2f7eb3a59
git -C "$CORE_ROOT" apply "$AUDIT_ROOT/patches/walletcore-4.8.4-api-repairs.patch"
mkdir -p "$CORE_TOOLS"
export RUSTUP_HOME="$CORE_TOOLS/rustup"
export CARGO_HOME="$CORE_TOOLS/cargo"
export PREFIX="$CORE_ROOT/build/local"
export PATH="$PREFIX/bin:$CARGO_HOME/bin:/opt/homebrew/opt/ruby/bin:$PATH"
export CARGO_BUILD_JOBS=4
curl --fail --location --output "$CORE_TOOLS/rustup-init" \
  https://static.rust-lang.org/rustup/archive/1.29.2/aarch64-apple-darwin/rustup-init
python3 - <<'PY'
import hashlib, os
from pathlib import Path
p = Path(os.environ['CORE_TOOLS'])/'rustup-init'
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f7c7e11eb2e07f006e532a8aaac77b32f4527d305ac386c0c633ca6133d35ca9'
p.chmod(0o700)
PY
"$CORE_TOOLS/rustup-init" -y --no-modify-path --profile minimal \
  --default-toolchain nightly-2025-12-11
cargo install cbindgen --version 0.29.2 --locked
python3 "$AUDIT_ROOT/scripts/walletcore-native-inputs.py" "$PREFIX"
cd "$CORE_ROOT"
cmake -S build/local/src/protobuf/protobuf-3.20.3/cmake -B build/native-protobuf \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -Dprotobuf_BUILD_TESTS=OFF -Dprotobuf_MODULE_COMPATIBLE=ON \
  -Dprotobuf_BUILD_SHARED_LIBS=OFF -DCMAKE_INSTALL_PREFIX="$PREFIX"
cmake --build build/native-protobuf --parallel 4
cmake --install build/native-protobuf
cmake -S protobuf-plugin -B build/native-protobuf-plugin \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DProtobuf_DIR="$PREFIX/lib/cmake/protobuf" \
  -DCMAKE_INSTALL_PREFIX="$PREFIX"
cmake --build build/native-protobuf-plugin --parallel 4
cmake --install build/native-protobuf-plugin
cmake -S build/local/src/check/check-0.15.2 -B build/native-check \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX"
cmake --build build/native-check --parallel 4
cmake --install build/native-check
ruby codegen/bin/coins
(cd rust && cargo build --locked --release --lib)
bash tools/generate-files native
git diff HEAD --binary > "$CORE_TOOLS/source-after-generation.patch"
cmp "$CORE_TOOLS/source-after-generation.patch" \
  "$AUDIT_ROOT/patches/walletcore-4.8.4-api-repairs.patch"
cmake -S . -B build/native-core -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ -DBoost_ROOT="$BOOST_ROOT" \
  -DTW_UNIT_TESTS=ON -DTW_BUILD_EXAMPLES=ON
cmake --build build/native-core --parallel 4
```

Stop on any failed command; save stdout, stderr and exit statuses. Upstream
generation invokes additional Cargo commands: the exact tracked `rust/Cargo.lock`
and `codegen-v2/Cargo.lock` must remain unchanged, as checked by the whole diff
comparison. New advisories or download failures are not an instruction to replace
the locks or use unpinned substitutes.

Then run the two commands in [the native review](CORE-NATIVE-AND-EXTENDED-KEY.md).
`walletcore-native-tests.py` verifies the source revision and complete tracked
diff, builds the native target, places a byte-identical C++ executable at the
fixture directory depth expected by upstream, and runs both real suites.
`walletcore-extended.py --full-suite` additionally compiles the fifth repair
without altering the prepared checkout, runs identical before/after fixtures,
and relinks/runs the complete C++ suite. Neither command launches a simulator.
