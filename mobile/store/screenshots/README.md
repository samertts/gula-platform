# Screenshot Generation Guide

This document describes how to generate store screenshots for GULA Platform using Fastlane screengrab (Android) and Fastlane snapshot (iOS).

## Prerequisites

### Android (Screengrab)
- Android device or emulator running API 26+
- Android SDK with build tools
- Fastlane installed (`gem install fastlane`)
- Screengrab test class in your androidTest source set

### iOS (Snapshot)
- Xcode 16.1+
- Fastlane installed (`gem install fastlane`)
- Snapshot test target in your Xcode project
- Simulator with matching iOS version

### Desktop
- macOS: Built-in screenshot tools + simulator
- Windows: Built-in Snipping Tool or third-party tools
- Linux: GNOME Screenshot or similar

## Setup

### Android Screengrab Setup

1. Create the screengrab test class:
```kotlin
// mobile/android/app/src/androidTest/java/io/gula/android/screenshots/ScreenshotsTest.kt
package io.gula.android.screenshots

import androidx.test.runner.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import tools.fastlane.screengrab.Screengrab
import tools.fastlane.screengrab.UiAutomatorScreenshotStrategy
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ScreenshotsTest {
    private lateinit var device: UiDevice

    @Before
    fun setUp() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        Screengrab.setDefaultScreenshotStrategy(UiAutomatorScreenshotStrategy())
    }

    @Test
    fun testCaptureScreenshots() {
        // Navigate through the app and capture screenshots
        Screengrab.screenshot("01_login_screen")
        Screengrab.screenshot("02_dashboard")
        Screengrab.screenshot("03_patient_list")
        Screengrab.screenshot("04_patient_details")
        Screengrab.screenshot("05_order_creation")
        Screengrab.screenshot("06_order_details")
        Screengrab.screenshot("07_results_dashboard")
        Screengrab.screenshot("08_result_details")
        Screengrab.screenshot("09_settings")
    }
}
```

2. Add Fastlane Screengrab dependency to `app/build.gradle.kts`:
```kotlin
androidTestImplementation("tools.fastlane:screengrab:2.1.1")
```

3. Run from Fastlane:
```bash
fastlane android screenshots_android
```

### iOS Snapshot Setup

1. Create a UI test target for screenshots in Xcode.

2. Configure Fastlane Snapshot in `Fastfile`:
```ruby
lane :screenshots_ios do
  capture_screenshots(
    workspace: "Gula.xcworkspace",
    scheme: "GulaScreenshots",
    output_directory: "../fastlane/screenshots/ios",
    languages: ["en-US", "ar-SA"],
    devices: ["iPhone 16 Pro", "iPad Pro 13-inch (M4)"]
  )
end
```

3. Run from Fastlane:
```bash
fastlane ios screenshots_ios
```

## Screenshot Requirements

### Google Play Store
| Requirement | Value |
|------------|-------|
| Format | PNG |
| Min dimensions | 320px |
| Max dimensions | 3840px |
| Aspect ratio | Between 2:1 and 1:2 |
| Max file size | 8MB per screenshot |
| Min screenshots | 2 |
| Max screenshots | 8 |
| Phone screenshots | 5-8 recommended |
| Tablet screenshots | 3-5 recommended (7-inch + 10-inch) |

### Apple App Store
| Requirement | Value |
|------------|-------|
| Format | PNG or JPG |
| 6.5" Display | 1242 x 2688 pixels |
| 5.5" Display | 1242 x 2208 pixels |
| 12.9" iPad Pro | 2048 x 2732 pixels |
| Max file size | 10MB per screenshot |
| Min screenshots | 1 per display size |
| Max screenshots | 10 per display size |

### Microsoft Store
| Requirement | Value |
|------------|-------|
| Format | PNG |
| Desktop screenshot | 1366 x 768 minimum |
| Min screenshots | 1 |

## Recommended Screenshot Captures

### For All Platforms (English + Arabic)

1. **Login Screen** - Clean login interface with biometric option
2. **Dashboard** - Main dashboard with key metrics and quick actions
3. **Patient List** - Searchable patient registry
4. **Patient Details** - Patient profile with clinical history
5. **Order Creation** - New lab order form with test selection
6. **Order Tracking** - Order status and tracking view
7. **Results Dashboard** - Test results with critical value flags
8. **Result Details** - Detailed result with reference ranges
9. **Settings** - App settings and preferences

### iOS Specific
- Include both 6.5" (iPhone 16 Pro Max) and 12.9" (iPad Pro) screenshots
- Show Face ID authentication screen
- Show Arabic RTL layout versions

### Android Specific
- Include both phone and tablet screenshots
- Show biometric authentication
- Show Arabic RTL layout versions

### Desktop Specific (Microsoft Store)
- Full window screenshots at 1920x1080
- Multi-window workflow demonstration
- Keyboard shortcuts overlay (optional)

## Output Structure

Screenshots should be organized as follows:

```
mobile/fastlane/screenshots/
├── android/
│   ├── en-US/
│   │   ├── 01_login_screen.png
│   │   ├── 02_dashboard.png
│   │   └── ...
│   └── ar-SA/
│       ├── 01_login_screen.png
│       ├── 02_dashboard.png
│       └── ...
├── ios/
│   ├── en-US/
│   │   ├── iPhone_16_Pro/
│   │   │   ├── 01_login_screen.png
│   │   │   └── ...
│   │   └── iPad_Pro_13/
│   │       ├── 01_login_screen.png
│   │       └── ...
│   └── ar-SA/
│       ├── iPhone_16_Pro/
│       └── iPad_Pro_13/
└── desktop/
    ├── en-US/
    │   ├── 01_dashboard.png
    │   └── ...
    └── ar-SA/
        ├── 01_dashboard.png
        └── ...
```

## Automation Tools

### Android
```bash
# Capture all screenshots
fastlane android screenshots_android

# Verify screenshots
fastlane run validate_screenshots
```

### iOS
```bash
# Capture all screenshots
fastlane ios screenshots_ios

# Frame screenshots for devices (optional)
fastlane run frameit
```

### Desktop (Manual)
For desktop versions, screenshots must be captured manually or using automated UI testing tools:
- **Windows**: WinAppDriver + Appium
- **macOS**: XCUITest
- **Linux**: AT-SPI2 + LDTP

## Store-Specific Upload

### Google Play
Screenshots are uploaded via the Google Play Console or Fastlane supply:
```bash
fastlane supply --json_key service_account.json \
  --package_name "io.gula.android" \
  --screenshots_path "fastlane/screenshots/android/"
```

### Apple App Store
Screenshots are uploaded via App Store Connect or Fastlane deliver:
```bash
fastlane deliver --json_key service_account.json \
  --screenshots_path "fastlane/screenshots/ios/"
```

## Notes
- Arabic screenshots must show RTL layout correctly
- All screenshots should be in the target locale
- Avoid showing real patient data; use test data
- Maintain consistent UI state across language variants
- Update screenshots with each major feature release
- Compress screenshots to meet store file size limits while maintaining quality
