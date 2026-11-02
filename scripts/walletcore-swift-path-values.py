#!/usr/bin/env python3
"""Run the upstream Swift path overlay against the locally compiled production Core libraries."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
CORE = "d40d24a63d92619167903369308bf0e2f7eb3a59"
OVERLAY = Path("swift/Sources/Extensions/DerivationPath+Extension.swift")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def no_core_dump():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("prepared", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    src, built, out = (p.resolve() for p in (args.source, args.prepared, args.output))
    require_source_state(src, CORE)
    out.mkdir(exist_ok=True, parents=True)
    native_patch = ROOT / "patches/walletcore-4.8.4-combined-eight.patch"
    def verify_native():
        if subprocess.check_output(["git", "-C", built, "rev-parse", "HEAD"], text=True).strip() != CORE:
            raise ValueError("Wrong native revision")
        if subprocess.check_output(["git", "-C", built, "diff", "HEAD", "--binary"]) != native_patch.read_bytes():
            raise ValueError("Unexpected native source changes")
        if subprocess.check_output(["git", "-C", built, "ls-files", "--others", "--exclude-standard"]).strip():
            raise ValueError("Unexpected native sources")
    verify_native()
    libs = [built / name for name in ("build/native-core/libTrustWalletCore.a", "build/native-core/trezor-crypto/libTrezorCrypto.a",
                                      "rust/target/release/libwallet_core_rs.a", "build/native-core/libprotobuf.a")]
    swift = built / "swift/Sources"
    wrappers = [swift / name for name in ("Generated/DerivationPath.swift", "Generated/DerivationPathIndex.swift",
                                         "Generated/Enums/Purpose.swift", "TWString.swift")]
    hashes = {str(p.relative_to(built)): digest(p) for p in libs + wrappers}
    fixture = ROOT / "tests/WalletCoreSwiftPathValues.swift"
    patch = ROOT / "patches/walletcore-4.8.4-swift-path-values.patch"
    rows = []
    expected_failures = {"short": "roundtrip", "long": "roundtrip", "bits": "roundtrip", "root": "roundtrip",
                         "unknown": "optional", "negative": "integer", "wide": "integer"}
    with tempfile.TemporaryDirectory(prefix="oath-path-check-") as temporary:
        work = Path(temporary)
        file = work / OVERLAY
        file.parent.mkdir(parents=True)
        file.write_bytes((src / OVERLAY).read_bytes())
        bridge = work / "Bridge.h"
        bridge.write_text("".join(f"#include <TrustWalletCore/{name}.h>\n" for name in
                                  ["TWPurpose", "TWDerivationPath", "TWDerivationPathIndex", "TWString"]))
        for stage in ["before", "after"]:
            if stage == "after":
                subprocess.run(["git", "apply", patch], cwd=work, check=True)
            binary = work / stage
            cmd = ["swiftc", "-Onone", "-I", built/"include", "-import-objc-header", bridge, *wrappers,
                   file, fixture, *libs, "-lc++", "-o", binary]
            subprocess.run(cmd, check=True, timeout=120)
            for case in ["standard", "legacy", "bounds", *expected_failures, "reject"]:
                result = subprocess.run(["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)", binary, case],
                                        capture_output=True, text=True, preexec_fn=no_core_dump, timeout=15)
                text = (result.stdout + result.stderr).replace(temporary, "<TEMP>")
                reason = expected_failures.get(case) if stage == "before" else None
                if reason in ("integer", "optional"):
                    evidence = "Fatal error:" in text and (("Negative value is not representable" in text or "Not enough bits to represent" in text) if reason == "integer" else "unwrapping an Optional" in text)
                    matches = result.returncode in (-signal.SIGILL, -signal.SIGTRAP) and evidence
                elif reason == "roundtrip":
                    matches = result.returncode == 1 and "Round-trip changed the derivation path" in text
                else:
                    matches = result.returncode == 0 and text.strip() == "Passed " + case
                log = out / f"{stage}-{case}.log"
                log.write_text(text)
                if not matches:
                    raise RuntimeError(f"Unexpected {stage} {case} result; see {log.name}")
                rows.append(dict(stage=stage, case=case, exit_code=result.returncode, status="reproduced" if reason else "passed",
                                 source_sha256=digest(file), log=log.name, log_sha256=digest(log)))
    require_source_state(src, CORE)
    verify_native()
    if hashes != {str(p.relative_to(built)): digest(p) for p in libs + wrappers}:
        raise ValueError("Native inputs changed during test")
    rec = dict(check="walletcore-swift-path-values", status="passed", upstream_commit=CORE, fixture_sha256=digest(fixture),
               patch_sha256=digest(patch), inputs=hashes, cases=rows,
               compiler=subprocess.check_output(["swiftc", "--version"], text=True).strip())
    (out/"result.json").write_text(json.dumps(rec, indent=2)+"\n")

if __name__ == "__main__":
    main()
