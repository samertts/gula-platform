import XCTest
@testable import Gula

final class AuthManagerTests: XCTestCase {
    var sut: AuthManager!

    override func setUp() {
        super.setUp()
        KeychainManager.shared.clearAll()
        sut = AuthManager.shared
    }

    override func tearDown() {
        sut.logout()
        KeychainManager.shared.clearAll()
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertFalse(sut.isAuthenticated)
        XCTAssertNil(sut.currentUser)
        XCTAssertFalse(sut.isLoading)
    }

    func testLogoutClearsState() {
        sut.logout()
        XCTAssertFalse(sut.isAuthenticated)
        XCTAssertNil(sut.currentUser)
    }

    func testBiometricDisable() {
        KeychainManager.shared.set(key: "biometric_enabled", value: "true")
        sut.biometricEnabled = true

        sut.disableBiometric()
        XCTAssertFalse(sut.biometricEnabled)
        XCTAssertNil(KeychainManager.shared.get(key: "biometric_email"))
        XCTAssertNil(KeychainManager.shared.get(key: "biometric_password"))
        XCTAssertEqual(KeychainManager.shared.get(key: "biometric_enabled"), "false")
    }

    func testUserRoleDisplayNames() {
        XCTAssertFalse(UserRole.labAdmin.displayName.isEmpty)
        XCTAssertFalse(UserRole.technician.displayName.isEmpty)
        XCTAssertFalse(UserRole.doctor.displayName.isEmpty)
        XCTAssertFalse(UserRole.receptionist.displayName.isEmpty)
    }

    func testBiometricType() {
        let type = BiometricAuth.biometryType
        XCTAssertNotNil(type)
    }

    func testKeychainSetAndGet() {
        let key = "test_key"
        let value = "test_value_123"

        let setResult = KeychainManager.shared.set(key: key, value: value)
        XCTAssertTrue(setResult)

        let retrieved = KeychainManager.shared.get(key: key)
        XCTAssertEqual(retrieved, value)

        KeychainManager.shared.delete(key: key)
        XCTAssertNil(KeychainManager.shared.get(key: key))
    }

    func testKeychainDataRoundTrip() {
        let key = "test_data"
        let data = "Hello World".data(using: .utf8)!

        XCTAssertTrue(KeychainManager.shared.setData(key: key, value: data))
        XCTAssertEqual(KeychainManager.shared.getData(key: key), data)

        KeychainManager.shared.delete(key: key)
        XCTAssertNil(KeychainManager.shared.getData(key: key))
    }

    func testKeychainClearAll() {
        KeychainManager.shared.set(key: "a", value: "1")
        KeychainManager.shared.set(key: "b", value: "2")

        KeychainManager.shared.clearAll()

        XCTAssertNil(KeychainManager.shared.get(key: "a"))
        XCTAssertNil(KeychainManager.shared.get(key: "b"))
    }

    func testUserEquality() {
        let user1 = User(id: 1, email: "test@test.com", name: "Test", role: .doctor, labId: 1)
        let user2 = User(id: 1, email: "test@test.com", name: "Test", role: .doctor, labId: 1)
        let user3 = User(id: 2, email: "other@test.com", name: "Other", role: .staff, labId: 2)

        XCTAssertEqual(user1, user2)
        XCTAssertNotEqual(user1, user3)
    }
}
