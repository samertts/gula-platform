import XCTest
@testable import Gula

final class APIClientTests: XCTestCase {
    var sut: APIClient!

    override func setUp() {
        super.setUp()
        sut = APIClient.shared
    }

    override func tearDown() {
        sut.clearTokens()
        super.tearDown()
    }

    func testLoginRequest() async {
        let endpoint = APIEndpoint.login
        XCTAssertEqual(endpoint.path, "/login")
        XCTAssertEqual(endpoint.method, "POST")
    }

    func testGetPatientEndpoint() {
        let endpoint = APIEndpoint.getPatient(id: 42)
        XCTAssertEqual(endpoint.path, "/patients/42")
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testListPatientsEndpoint() {
        let endpoint = APIEndpoint.listPatients(page: 1, limit: 20, search: nil, gender: nil, status: nil)
        XCTAssertEqual(endpoint.path, "/patients")
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testCreateOrderEndpoint() {
        let endpoint = APIEndpoint.createOrder
        XCTAssertEqual(endpoint.path, "/orders")
        XCTAssertEqual(endpoint.method, "POST")
    }

    func testVerifyResultEndpoint() {
        let endpoint = APIEndpoint.verifyResult(id: 99)
        XCTAssertEqual(endpoint.path, "/results/99/verify")
        XCTAssertEqual(endpoint.method, "PUT")
    }

    func testDeleteSampleEndpoint() {
        let endpoint = APIEndpoint.deleteSample(id: 7)
        XCTAssertEqual(endpoint.path, "/samples/7")
        XCTAssertEqual(endpoint.method, "DELETE")
    }

    func testDashboardEndpoint() {
        let endpoint = APIEndpoint.dashboard
        XCTAssertEqual(endpoint.path, "/dashboard")
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testListNotificationsWithParams() {
        let endpoint = APIEndpoint.listNotifications(page: 1, limit: 30, read: false, type: "critical")
        XCTAssertEqual(endpoint.path, "/notifications")
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testMarkNotificationRead() {
        let endpoint = APIEndpoint.markNotificationRead(id: 5)
        XCTAssertEqual(endpoint.path, "/notifications/5/read")
        XCTAssertEqual(endpoint.method, "PUT")
    }

    func testAdminListUsers() {
        let endpoint = APIEndpoint.adminListUsers(page: 1, limit: 50)
        XCTAssertEqual(endpoint.path, "/admin/users")
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testBulkRegisterSamples() {
        let endpoint = APIEndpoint.bulkRegisterSamples
        XCTAssertEqual(endpoint.path, "/samples/bulk-register")
        XCTAssertEqual(endpoint.method, "POST")
    }

    func testGenerateReport() {
        let endpoint = APIEndpoint.generateReport(id: 123)
        XCTAssertEqual(endpoint.path, "/results/123/report")
        XCTAssertEqual(endpoint.method, "POST")
    }

    func testPatientByPhone() {
        let endpoint = APIEndpoint.patientByPhone(phone: "+9647701234567")
        XCTAssertTrue(endpoint.path.contains("/patients/phone/"))
        XCTAssertEqual(endpoint.method, "GET")
    }

    func testAPIErrorEquality() {
        XCTAssertEqual(APIError.authentication, APIError.authentication)
        XCTAssertEqual(APIError.offline, APIError.offline)
        XCTAssertEqual(APIError.notFound, APIError.notFound)
        XCTAssertNotEqual(APIError.authentication, APIError.permissionDenied)
    }

    func testAPIErrorFromStatusCode() {
        let authError = APIError.from(statusCode: 401, data: nil)
        XCTAssertEqual(authError, .authentication)

        let notFound = APIError.from(statusCode: 404, data: nil)
        XCTAssertEqual(notFound, .notFound)

        let serverError = APIError.from(statusCode: 500, data: nil)
        if case .serverError(let code) = serverError {
            XCTAssertEqual(code, 500)
        } else {
            XCTFail("Expected serverError")
        }
    }

    func testAPIErrorDescriptions() {
        XCTAssertFalse(APIError.authentication.errorDescription?.isEmpty ?? true)
        XCTAssertFalse(APIError.offline.errorDescription?.isEmpty ?? true)
        XCTAssertFalse(APIError.notFound.errorDescription?.isEmpty ?? true)
    }
}
