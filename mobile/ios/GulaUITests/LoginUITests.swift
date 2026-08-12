import XCTest

final class LoginUITests: XCTestCase {
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

    func testLoginScreenElements() {
        let emailField = app.textFields["email_placeholder".localized]
        let passwordField = app.secureTextFields["password_placeholder".localized]
        let loginButton = app.buttons["login".localized]

        XCTAssertTrue(emailField.exists)
        XCTAssertTrue(passwordField.exists)
        XCTAssertTrue(loginButton.exists)
    }

    func testEmptyFieldsShowsValidation() {
        let loginButton = app.buttons["login".localized]
        loginButton.tap()

        let errorText = app.staticTexts["field_required".localized]
        XCTAssertTrue(errorText.exists)
    }

    func testLoginButtonDisabledWithEmptyFields() {
        let loginButton = app.buttons["login".localized]
        XCTAssertFalse(loginButton.isEnabled)
    }

    func testRememberMeToggle() {
        let toggle = app.switches["remember_me".localized]
        if toggle.exists {
            toggle.tap()
            XCTAssertTrue(toggle.isSelected)
        }
    }

    func testForgotPasswordButton() {
        let forgotButton = app.buttons["forgot_password".localized]
        XCTAssertTrue(forgotButton.exists)
        XCTAssertTrue(forgotButton.isHittable)
    }
}
