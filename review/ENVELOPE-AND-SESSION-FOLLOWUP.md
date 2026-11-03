# Envelope and session follow-up: hypotheses not confirmed

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

At `235a730de504e47fb961c34f68f9426ffdbdfe6d`, the session rejection handler force-unwraps `session.publicKey`. Source tracing shows that this computed optional always wraps `selfParticipant.publicKey`, which is a nonoptional immutable String. Codable requires that String. A nil value is not representable through the inspected constructors or decoder. This suspected nil crash was therefore not confirmed; the rest of the settlement lifecycle remains partially reviewed.

The envelope decoder's first-byte expression appeared to risk an empty-data range error. The original implementation rejected the empty string without a process trap on the tested host. The same ten production-code cases passed on the immutable 5.0.1 (103) baseline and the later public source, with networking denied. These cover empty standard/URL base64 at the envelope and serializer APIs, all truncated type-1 public-key lengths, unsupported type bytes, malformed base64 and valid type-0/1/2 serialization controls. A provisional one-line guard change was discarded. No application fix or vulnerability finding is claimed.

The replay's inherited before/after labels identify two source revisions; the envelope implementation has the same hash in both. It would be incorrect to present this as failed-before/passed-after evidence. [Twenty case records](../evidence/5.0.1-build103/envelope-boundaries/result.json) · [Source hashes and scope](../evidence/5.0.1-build103/envelope-boundaries/review.json) · [Fixture](../fixtures/envelope-boundaries/EmptyEnvelopeBoundaryTests.swift).

The relay and Link Mode dispatchers additionally reject missing type bytes before calling the serializer. Other direct decryption-service APIs also call the serializer; their full call chains remain outstanding. These checks establish host behavior for the corpus, not every platform/Foundation version or all parsing inputs. No simulator or phone was used.

To reproduce from a clean audit checkout with compatible Xcode and a clone of the public Oath repository:

```sh
python3 scripts/envelope-boundaries.py /path/to/oath-wallet /tmp/oath-envelope-build /tmp/oath-envelope-results
```

No previous reviewed status is strengthened merely by these test passes. The earlier full KMS source read remains a historical record; the key-hex finding separately documents the defect missed there.
