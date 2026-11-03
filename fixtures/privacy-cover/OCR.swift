import Foundation
import Vision
let root = URL(fileURLWithPath: CommandLine.arguments[1])
var results: [String: Any] = [:]
for name in ["uncovered", "covered-light", "covered-dark", "compositor-dark"] {
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
