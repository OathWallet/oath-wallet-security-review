import Foundation

@main struct Events {
    static func main() {
        var seed: UInt64 = 0x20261102
        func next(_ n: Int) -> Int {
            seed = seed &* 6364136223846793005 &+ 1442695040888963407
            return Int((seed >> 32) % UInt64(n))
        }
        let distances = [Double.nan, -.infinity, .infinity, -1000, 0, 0.25, 1, 48, 95.99, 96, 192]
        var cycle = RefreshCycle()
        var gesture = RefreshPullGesture()
        var ticks = RefreshPullFeedback()
        var accepted = 0
        var steps = 0
        for _ in 0..<100000 {
            let before = cycle
            let distance = distances[next(distances.count)]
            let dragging = next(2) == 1
            gesture.observe(position: distance, isPanning: dragging)
            switch next(12) {
            case 0, 1, 2:
                cycle.pull(distance: distance, isDragging: dragging)
                if !distance.isFinite { precondition(cycle == before) }
                if !dragging && before.phase == .idle && !before.isReturning { precondition(cycle == before) }
            case 3, 4:
                if cycle.beginIfFilled(isDragging: dragging, eligible: gesture.allowsRefresh) {
                    precondition(dragging && gesture.allowsRefresh && before.phase == .pulling && before.progress == 1 && !before.isReturning)
                    precondition(cycle.phase == .refreshing && !cycle.begin())
                    accepted += 1
                }
            case 5:
                if cycle.begin() {
                    precondition(!before.isReturning && (before.phase == .idle || before.phase == .pulling))
                    precondition(!cycle.begin())
                    accepted += 1
                }
            case 6: cycle.complete(succeeded: dragging)
            case 7: cycle.acknowledge()
            case 8: cycle.returnToRest()
            case 9: cycle.finishPresentation()
            case 10: cycle.reset()
            default:
                if ticks.update(progress: distance, isDragging: dragging, eligible: gesture.allowsRefresh) {
                    precondition(distance.isFinite && distance > 0 && distance < 1 && dragging && gesture.allowsRefresh)
                    steps += 1
                }
            }
            precondition(cycle.progress.isFinite && (0...1).contains(cycle.progress))
        }
        precondition(accepted > 100 && steps > 0)
        print("100000 seeded events passed; activations=\(accepted), feedback=\(steps)")
    }
}
