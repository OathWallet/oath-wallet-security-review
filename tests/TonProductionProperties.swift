import XCTest
@testable import OathAnkr

// Public deterministic inputs. These tests call the production module; no codec
// or signature implementation is duplicated here.
final class TonAuditProductionTests: XCTestCase {
    struct Random {
        var state: UInt64 = 0x4f415448544f4e31
        mutating func next() -> UInt64 {
            state ^= state << 13; state ^= state >> 7; state ^= state << 17
            return state
        }
    }
    func testIndependentIntegerVectors() throws {
        struct Vector: Decodable { let decimal: String, hex: String, lesser: String, difference: String }
        let url = try XCTUnwrap(Bundle.module.url(forResource: "amounts", withExtension: "json"))
        let vectors = try JSONDecoder().decode([Vector].self, from: Data(contentsOf: url))
        XCTAssertEqual(vectors.count, 1004)
        for v in vectors {
            let value = try XCTUnwrap(TonAmount(v.decimal))
            let lesser = try XCTUnwrap(TonAmount(v.lesser))
            XCTAssertEqual(value.description, v.decimal)
            XCTAssertEqual(value, TonAmount(v.hex, radix: 16))
            XCTAssertGreaterThanOrEqual(value, lesser)
            XCTAssertEqual((value - lesser).description, v.difference)
            var b = TonBuilder(); try b.jettonCoins(value)
            var r = TonReader(try b.cell())
            XCTAssertEqual(try r.jettonCoins(), value)
            XCTAssertEqual(try JSONDecoder().decode(TonAmount.self, from: JSONEncoder().encode(value)), value)
        }
        for invalid in ["1329227995784915872903807060280344576", "-1", "+1", "1e2", "1.0", " 1", "١", "", String(repeating: "0", count: 41)] {
            XCTAssertNil(TonAmount(invalid))
        }
    }
    func testBitWidthBoundaries() throws {
        var random = Random()
        for width in 0...64 {
            let mask: UInt64 = width == 64 ? .max : (UInt64(1) << width) - 1
            for value in [UInt64(0), mask, random.next() & mask] {
                var b = TonBuilder(); try b.uint(value, width)
                var r = TonReader(try b.cell())
                XCTAssertEqual(try r.uint(width), value)
                XCTAssertThrowsError(try r.uint(1))
            }
            if width < 64 {
                var b = TonBuilder()
                XCTAssertThrowsError(try b.uint(mask + 1, width))
            }
        }
        for width in [-1, 65, Int.max] {
            var b = TonBuilder(); XCTAssertThrowsError(try b.uint(0, width))
        }
    }
    func testSeededCellRoundTripsAndMutations() throws {
        var random = Random(), cells = [try TonCell()]
        var acceptedMutations = 0, rejectedMutations = 0
        for i in 0..<256 {
            let bitCount = [0, 1, 7, 8, 9, 1023][i % 6]
            let bits = (0..<bitCount).map { _ in UInt8(random.next() & 1) }
            let refs = (0..<(i % 5)).map { _ in cells[Int(random.next() % UInt64(cells.count))] }
            let cell = try TonCell(bits, refs)
            let boc = try cell.boc(), restored = try TonCell.parse(boc)
            XCTAssertEqual(restored.hash, cell.hash)
            XCTAssertEqual(restored.bits, cell.bits)
            XCTAssertEqual(restored.depth, cell.depth)
            cells.append(cell)
            // A mutation may describe another valid cell. Do not demand blanket
            // rejection: accepted inputs must survive canonical serialization.
            for _ in 0..<16 {
                var altered = boc
                let at = Int(random.next() % UInt64(altered.count))
                altered[at] ^= UInt8(1 << (random.next() % 8))
                if let parsed = try? TonCell.parse(altered) {
                    XCTAssertEqual(try TonCell.parse(parsed.boc()).hash, parsed.hash)
                    acceptedMutations += 1
                } else { rejectedMutations += 1 }
            }
        }
        XCTAssertEqual(acceptedMutations + rejectedMutations, 4096)
        XCTAssertGreaterThan(acceptedMutations, 0)
        XCTAssertGreaterThan(rejectedMutations, 0)
        print("TON mutation corpus: \(acceptedMutations) accepted and reserialized; \(rejectedMutations) rejected; seed 0x4f415448544f4e31")
    }
    func testStructuralBoundsAndTruncation() throws {
        XCTAssertThrowsError(try TonCell(Array(repeating: 0, count: 1024)))
        XCTAssertThrowsError(try TonCell([2]))
        XCTAssertThrowsError(try TonCell([], Array(repeating: try TonCell(), count: 5)))
        var c = try TonCell()
        for _ in 0..<128 { c = try TonCell([], [c]) }
        XCTAssertEqual(c.depth, 128)
        XCTAssertThrowsError(try TonCell([], [c]))
        let boc = try c.boc()
        for end in 0..<boc.count { XCTAssertThrowsError(try TonCell.parse(Data(boc.prefix(end)))) }
        XCTAssertThrowsError(try TonCell.parse(Data(repeating: 0, count: 1_048_577)))
        XCTAssertEqual(try TonCell.parse(boc).hash, c.hash)
        // A cell cannot reference itself, refer backward, or use a nonexistent index.
        for index: UInt8 in [0, 1, 255] {
            XCTAssertThrowsError(try TonCell.parse(Data([0xb5,0xee,0x9c,0x72,1,1,1,1,0,3,0,1,0,index])))
        }
    }
    func testDictionarySubsetsAndLimits() throws {
        var random = Random()
        for count in 1...256 {
            var keys = Set<UInt64>()
            while keys.count < count { keys.insert(random.next() & 255) }
            let entries = keys.sorted().map { ($0, Data([UInt8($0)])) }
            let root = try TonMultisigDictionary.encode(entries, width: 8)
            let decoded = try TonMultisigDictionary.decode(root, width: 8, limit: count)
            XCTAssertEqual(Set(decoded.keys), keys)
            for (key, data) in entries { XCTAssertEqual(decoded[key]?.padded, data) }
            XCTAssertThrowsError(try TonMultisigDictionary.decode(root, width: 8, limit: count - 1))
        }
        XCTAssertThrowsError(try TonMultisigDictionary.encode([(1, Data()), (1, Data())], width: 8))
        for width in [-1, 65] {
            XCTAssertThrowsError(try TonMultisigDictionary.decode(TonCell(), width: width, limit: 1))
        }
        for key: UInt64 in [0, 1, 1 << 63, .max] {
            var b = TonBuilder(); try b.uint(2, 2); try b.uint(64, 7); try b.uint(key, 64); try b.uint(42, 8)
            let decoded = try TonMultisigDictionary.decode(b.cell(), width: 64, limit: 1)
            XCTAssertEqual(decoded[key]?.padded, Data([42]))
        }
    }
}
