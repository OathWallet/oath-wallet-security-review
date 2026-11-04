import Foundation
import Dispatch

// Public synthetic markers only. The subject types are compiled from the complete production file.
@main struct ScannerStateChecks {
    struct Failed: Error { let message: String }
    static func require(_ value: Bool, _ message: String) throws {
        if !value { throw Failed(message: message) }
    }
    enum Event: Int, CaseIterable { case begin, acceptA, acceptB, dismiss, cancel, finish, reject }
    // Independent finite-state specification: row=state, column=event.
    // States: idle, scanning, dismissal-A, dismissal-B, destination, finished.
    static let next = [
        [1,0,0,0,0,0,0], [1,2,3,5,5,1,1], [2,2,2,4,5,2,2],
        [3,3,3,4,5,3,3], [4,4,4,4,4,5,1], [1,5,5,5,5,5,5]
    ]
    static let phases = ["idle", "scanning", "dismissingCamera", "dismissingCamera", "destination", "finished"]
    static func advance(_ event: Event, _ flow: inout OathScannerHandoff<String>) -> String {
        switch event {
        case .begin: return String(flow.begin())
        case .acceptA: return String(flow.accept("A"))
        case .acceptB: return String(flow.accept("B"))
        case .dismiss, .cancel:
            switch flow.cameraDidDismiss(stillPresented: event == .dismiss) {
            case .close: return "close"
            case .present(let payload): return payload
            case nil: return "nil"
            }
        case .finish: return String(flow.finishDestination())
        case .reject: return String(flow.rejectDestination())
        }
    }
    static func expected(_ event: Event, _ state: Int) -> String {
        switch event {
        case .begin: return String(state == 0 || state == 5)
        case .acceptA, .acceptB: return String(state == 1)
        case .finish, .reject: return String(state == 4)
        case .cancel: return (1...3).contains(state) ? "close" : "nil"
        case .dismiss:
            return state == 1 ? "close" : state == 2 ? "A" : state == 3 ? "B" : "nil"
        }
    }
    static func exhaustive() throws {
        var edges = 0
        func walk(_ flow: OathScannerHandoff<String>, _ state: Int, _ depth: Int, _ path: String) throws {
            if depth == 0 { return }
            for event in Event.allCases {
                var candidate = flow
                let observed = advance(event, &candidate), target = next[state][event.rawValue]
                let trace = path + String(event.rawValue)
                try require(observed == expected(event,state), "handoff return at trace \(trace)")
                try require(String(describing: candidate.phase) == phases[target], "handoff phase at trace \(trace)")
                edges += 1
                try walk(candidate, target, depth-1, trace)
            }
        }
        try walk(OathScannerHandoff<String>(),0,6,"")
        try require(edges == 137256, "trace count")
        print("DETAIL: 137256 transition prefixes through depth 6, 274512 return/phase comparisons")
    }
    final class Payload {}
    static func lifetime() throws {
        for approved in [false,true] {
            var flow = OathScannerHandoff<Payload>()
            _ = flow.begin()
            weak var witness: Payload?
            do { let p=Payload(); witness=p; try require(flow.accept(p),"payload acceptance") }
            try require(witness != nil,"payload retained until dismissal")
            if approved {
                do {
                    guard case .present(let p) = flow.cameraDidDismiss(stillPresented:true) else { throw Failed(message:"delivery missing") }
                    try require(p === witness,"same payload")
                }
            } else {
                guard case .close = flow.cameraDidDismiss(stillPresented:false) else { throw Failed(message:"canceled delivery") }
            }
            try require(witness == nil,"pending payload not released")
        }
    }
    final class Winners: @unchecked Sendable {
        let lock=NSLock(); var values:[UInt64]=[]
        func add(_ value:UInt64) { lock.lock(); values.append(value); lock.unlock() }
    }
    static func concurrency() throws {
        let state=OathScannerCaptureState()
        for _ in 0..<100 {
            guard let revision=state.request(true) else { throw Failed(message:"activation missing") }
            let wins=Winners()
            DispatchQueue.concurrentPerform(iterations:64) { _ in
                if let token=state.claimDelivery() { wins.add(token) }
            }
            try require(wins.values == [revision],"exactly one concurrent claim")
            _ = state.request(false)
            try require(!state.isCurrent(revision),"claimed callback invalid after stop")
            try require(state.claimDelivery() == nil,"inactive capture delivered")
        }
        print("DETAIL: 6400 concurrent claim attempts across 100 activations")
    }
    static func invalidation() throws {
        let state=OathScannerCaptureState()
        let a=state.request(true)!
        try require(state.claimDelivery() == a,"first activation claim")
        let b=state.request(true,retry:true)!
        try require(a != b && !state.isCurrent(a) && state.isCurrent(b),"retry invalidates old callbacks")
        try require(state.claimDelivery() == b,"retry permits one new claim")
        let c=state.request(false)!
        try require(!state.isCurrent(b) && state.isCurrent(c) && !state.isActive,"stop invalidates retry")
        let d=state.request(false,retry:true)!
        try require(d != c && !state.isCurrent(c) && state.claimDelivery() == nil,"inactive retry remains inactive")
    }
    static func idempotence() throws {
        let state=OathScannerCaptureState()
        try require(state.request(false) == nil && state.revision == 0,"initial stop no-op")
        let a=state.request(true)!
        try require(state.request(true) == nil && state.revision == a,"repeated start no-op")
        try require(state.claimDelivery() == a && state.claimDelivery() == nil,"duplicate claim refused")
        try require(state.request(true) == nil && state.claimDelivery() == nil,"same start cannot replay")
    }
    static func main() {
        let tests:[(String,() throws -> Void)] = [("exhaustive-handoff",exhaustive),("payload-lifetime",lifetime),("concurrent-claims",concurrency),("generation-invalidation",invalidation),("idempotent-start",idempotence)]
        var failed=0
        for (name,test) in tests {
            do { try test(); print("PASS: \(name)") }
            catch { failed += 1; print("FAIL: \(name): \(error)") }
        }
        print("Scanner state groups: \(tests.count-failed) passed, \(failed) failed")
        exit(failed == 0 ? 0 : 1)
    }
}
