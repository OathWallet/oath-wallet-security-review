# Artwork destinations and the pinned SwiftDraw document model

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

## Where a logo can go

The source policy accepts token metadata and builds candidates, including an original URL carried by a signed TonAPI thumbnail. ArtworkLoader uses those candidates for cache lookup and download. ArtworkURLTransport checks its input, each proposed redirect, and the final response URL. A similar check protects the shared catalog transport. It uses HTTPS, removes cookie and credential stores, and limits accepted response size. [OW-2026-031](../findings/OW-2026-031.md) covers a lexical bypass common to these entry points.

A syntactically valid public name can resolve to a private IP address or change its resolution. The repaired URL rule has no connected-socket address check. Neither the classifier nor the local fixtures prove DNS rebinding protection, same-IP connection pinning, successful TLS against a private service, or transfer of secrets. A separate network-policy review must evaluate that boundary. [RFC 8375](https://www.rfc-editor.org/rfc/rfc8375) specifies the special-use residential home.arpa namespace.

## SwiftDraw 0.29.0 source inspection

At revision `82699f4bdf2f075793cfa0d392eb27c59b41a3fe` the DOM holds shape geometry, ordered graphic children, text, reference URLs, fills, gradient stops and styles. The following dispositions apply to reading the listed source files at this precise revision:

- Element, Filter, FontFace, Image, Path, Pattern, SVG, Switch and Text are in-memory representations. Their initializers store data. Path construction starts with an absolute move and maps the supported command letters to coordinate spaces. The SVG definitions object separates the element dictionary from ordered filters, gradients, masks, clips and patterns. An anchor stores a URL; construction itself does not open it.
- The linear and radial gradient classes store optional reference URLs and ordered stops. Their equality methods compare only selected fields; e.g. linear gradient comparison omits href, transforms and units. These equalities are unsuitable as proof that two drawings or referenced destinations are equivalent. No such authorization use was established here.
- DOM.swift defines scalar types, fill choices, transform cases and unit conversion. Its floating-point calculations impose no finite-value limit by themselves. XML.Element stores names, attributes, children, text and source location.
- Image and Use parsers read xlink:href and coordinates. Text parsing trims whitespace, may select the first tspan, and populates text coordinates. The anchor parser reads the href without opening it. Pattern parsing constructs a named frame and optional coordinate units. The SVG parse facade has separate byte and URL entry points; Oath passes validated bytes to the drawing library. URL+Data's normalization and Base64 reader are string-processing helpers; callers and input policy determine which bytes can reach image or font decoding.
- Recursively extracting gradients/filters, processing transforms, the XML SAX tree builder, and convenience extensions retain partial dispositions. The SAX builder processes recognized namespaces and appends character chunks to element text. The coordinate-varargs helpers assume even length; production polygon/polyline XML parsing uses a points array instead. Caller reachability, adversarial CSS and namespace equivalence, numeric extremes, downstream font/renderer memory limits and every other consumer have not been proved safe.

The [dependency ledger](../scope/upstream-swiftdraw.json) retains file hashes and these individual boundaries. A separate host run executed the pinned library's **167 Swift Testing tests in 22 DOM suites** under network denial. This includes its own grammar and bundled document fixtures. These tests do not award source-review status to the files they exercise. Reproduce with `sh scripts/swiftdraw-dom.sh <pinned-SwiftDraw-checkout> .work/dom-build .work/dom-results`.
