import Foundation
import XCTest
@testable import OathCloudBackup

final class BackupFileBoundaryTests: XCTestCase {
    func testExclusiveCreatorWinsAtPublicationBoundary() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("oath-boundary-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let url = directory.appendingPathComponent("audit-interleaving.oathbackup")
        XCTAssertThrowsError(try CloudFileWriter.write(Data([5, 7, 11]), to: url)) {
            XCTAssertEqual($0 as? CloudBackupError, .fileConflict)
        }
        XCTAssertEqual(try Data(contentsOf: url), Data([19, 23]), "Earlier complete file must survive")
    }
}
