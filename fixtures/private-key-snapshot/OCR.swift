import Foundation
import Vision
let root = URL(fileURLWithPath: CommandLine.arguments[1])
var results: [String: Any] = [:]
for name in ["captures/foreground", "captures/foreground-after", "captures/snapshot-before-2", "captures/snapshot-before-3", "snapshots-clear-model/0", "snapshots-clear-model/1", "snapshots-clear-model/2", "snapshots-clear-model/3"] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]
    let handler = VNImageRequestHandler(url: root.appendingPathComponent(name + ".png"))
    try handler.perform([request])
    results[name] = (request.results ?? []).compactMap { $0.topCandidates(1).first }.map {
        ["text": $0.string, "confidence": $0.confidence] as [String: Any]
    }
}
let data = try JSONSerialization.data(withJSONObject: results, options: [.prettyPrinted, .sortedKeys])
try data.write(to: root.appendingPathComponent("ocr.json"))
print(String(data: data, encoding: .utf8)!)
