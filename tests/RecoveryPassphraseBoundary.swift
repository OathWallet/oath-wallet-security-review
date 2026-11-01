import Foundation
@main struct BoundaryCheck {
 static func main() throws {
  func require(_ condition: Bool) { precondition(condition, "Passphrase boundary regression") }
  func rejects(_ value: String) { do { _ = try RecoveryPassphrase.normalized(value); preconditionFailure("Invalid passphrase accepted") } catch is RecoveryPassphraseError {} catch { preconditionFailure("Unexpected error") } }
  require(try RecoveryPassphrase.normalized(String(repeating:"p",count:256)) == String(repeating:"p",count:256))
  rejects(String(repeating:"p",count:257));rejects("before\0after");rejects("")
  rejects(String(repeating:"é",count:86))
  require(try RecoveryPassphrase.normalized(String(repeating:"é",count:85)).utf8.count == 255)
  require(try RecoveryPassphrase.normalized("  TéST 🔑  ") == "  TéST 🔑  ".decomposedStringWithCompatibilityMapping)
  require(try RecoveryPassphrase.normalized("Ａ") == "A")
  let legacy=String(repeating:"p",count:300)
  require(try RecoveryPassphrase.normalizedLegacy(legacy) == legacy)
  rejects(legacy)
  do { _ = try RecoveryPassphrase.normalizedLegacy(String(repeating:"p",count:4097));preconditionFailure("Oversized legacy value accepted") } catch is RecoveryPassphraseError {}
  print("PASSPHRASE_BOUNDARY_OK checks=11")
 }
}
