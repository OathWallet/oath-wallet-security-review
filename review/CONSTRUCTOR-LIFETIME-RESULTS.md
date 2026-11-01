# Constructor and entropy-lifetime experiments

Wallet Core 4.8.4 source: `d40d24a63d92619167903369308bf0e2f7eb3a59`.
Oath call-path target: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
This supersedes only the untested-experiment status in the progress-13
[constructor source trace](HDWALLET-CONSTRUCTOR-REACHABILITY.md).

## Faithful but limited compilation

The runner compiles the unchanged contiguous constructor/destructor definitions
from `src/HDWallet.cpp:39–107`, the actual `HDWallet.h` layout, full upstream
`Mnemonic.cpp` and six production C mnemonic/KDF sources. It generates the
missing HRP header using pinned upstream Ruby code. Includes and explicit
template instantiations isolate the unrelated Rust/signing methods; there are
no substitute constructor or derivation implementations. The exact slice/source
hashes are retained. This is not a full Wallet Core translation-unit build or
proof about the distributed Apple binary.

Both assertion-enabled and `NDEBUG` constructor builds run under ASan/UBSan.
The fixture keeps its own assertions enabled in both. Twenty-two positive checks
pass in each configuration: exact-size raw seeds, invalid-size rejection, valid
64-byte mnemonic/entropy equivalence and all five supported entropy strengths.
An initial link failure from unused inline extended-key methods is retained;
dead stripping removes those unrelated sections instead of stubbing them.

## DEP-CORE-003 — unsafe 32-byte mnemonic constructor (unrepaired)

`updateSeedAndEntropy` passes a 32-byte `seed` member to `mnemonic_to_seed`, which
writes 64 bytes. The real class stores mnemonic/passphrase objects after it.
For the public BIP39 fixture, both mnemonic and entropy constructors abort on
the invalid-entropy assertion in the assertion-enabled build. With assertions
disabled they return with empty entropy, recorded by the fixture's exit code 1.
The seeded raw-data constructor remains correct because it copies exactly the
template's declared size. An exploratory random-strength call additionally
produced an ASan crash; the reproducible gate uses deterministic inputs instead.

This is confirmed direct misuse of an upstream API, not a reachable Oath exploit:
the four exported C creation wrappers use the default 64-byte specialization,
and the only explicit upstream 32-byte caller uses the bounded raw-data overload.
A safe upstream contract would disallow mnemonic/entropy constructors on the
32-byte specialization or define a bounded conversion explicitly. No such fix
is included in the pinned dependency; do not describe its failing cases as fixed.

## DEP-CORE-004 — entropy retained at deallocation (unrepaired hygiene limitation)

The actual destructor wipes seed, mnemonic and passphrase, but not its entropy
vector. The test registers only the entropy allocation of a 64-byte wallet made
from 16 public fixture bytes. A replacement global delete observes that exact
allocation immediately before freeing it: all sixteen bytes remain unchanged
in both configurations. The hook uses a matching malloc/free allocator and does
not read freed memory or production credentials.

This establishes a local erasure limitation, not remote leakage or an
attacker-accessible process-memory disclosure. It does not measure every Swift,
C++ or allocator copy. Adding an entropy wipe would address this one allocation;
broader ownership and replacement-binary verification still need review. There
is no tested source repair or App Store claim for this dependency limitation.

## Reproduce

Use Ruby 4.0.5 and the recorded macOS Clang toolchain:

```sh
python3 scripts/walletcore-constructors.py /path/to/wallet-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --output /tmp/oath-constructor-evidence
```

Expected failing API characterizations and positive tests have separate result
entries. A successful harness invocation means it reproduced the documented
behavior; it does not mean the API hazards were repaired. No simulator, physical
device, real credentials or transaction is involved.
