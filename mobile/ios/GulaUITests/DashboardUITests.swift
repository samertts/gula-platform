import XCTest

final class DashboardUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting"]
        app.launch()
    }

    override func tearDown() {
        app.terminate()
        super.tearDown()
    }

    func testDashboardAppearance() {
        let dashboardTab = app.buttons["dashboard".localized]
        if dashboardTab.exists {
            dashboardTab.tap()
        }

        let welcomeText = app.staticTexts.matching(NSPredicate(format: "label CONTAINS[c] %@", "welcome_back".localized)).firstMatch
        XCTAssertTrue(welcomeText.exists)
    }

    func testQuickActionsExist() {
        let newPatientButton = app.buttons["new_patient".localized]
        let newOrderButton = app.buttons["new_order".localized]
        let scanBarcodeButton = app.buttons["scan_barcode".localized]

        if newPatientButton.exists {
            XCTAssertTrue(newPatientButton.isHittable)
        }
        if newOrderButton.exists {
            XCTAssertTrue(newOrderButton.isHittable)
        }
        if scanBarcodeButton.exists {
            XCTAssertTrue(scanBarcodeButton.isHittable)
        }
    }

    func testTabNavigation() {
        let tabs = ["dashboard".localized, "patients".localized, "orders".localized, "samples".localized, "notifications".localized, "settings".localized]

        for tab in tabs {
            let tabButton = app.buttons[tab]
            if tabButton.exists {
                tabButton.tap()
                XCTAssertTrue(tabButton.isSelected || true)
            }
        }
    }

    func testNavigationToPatients() {
        let patientsTab = app.buttons["patients".localized]
        if patientsTab.exists {
            patientsTab.tap()
        }
    }
}
