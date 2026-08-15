import XCTest
@testable import Gula

final class IOSUpdateGateTests: XCTestCase {
    func testVersionComparisonUsesSemanticComponents() {
        XCTAssertTrue(IOSVersionComparator.isLess("2.4.10", than: "2.5.0"))
        XCTAssertTrue(IOSVersionComparator.isLess("2.4", than: "2.4.1"))
        XCTAssertFalse(IOSVersionComparator.isLess("2.5.0", than: "2.5.0"))
        XCTAssertFalse(IOSVersionComparator.isLess("2.5.1", than: "2.5.0"))
    }

    func testVersionComparisonIgnoresPrereleaseSuffixForGate() {
        XCTAssertFalse(IOSVersionComparator.isLess("2.5.0-beta.1", than: "2.5.0"))
        XCTAssertTrue(IOSVersionComparator.isLess("2.4.9-rc.1", than: "2.5.0"))
    }
}
