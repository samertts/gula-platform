# Changelog

All notable changes to the GULA Platform multi-platform applications will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

---

## [2.5.0] - 2026-07-15

### Added
- Enhanced Master Patient Index with improved deduplication algorithms using ML-based matching
- New critical value notification preferences per test type with configurable thresholds
- SNDHS Health ID integration support for Iraqi national health system compatibility
- Custom branding support for PDF report templates (logo, colours, footer text)
- Delta-change detection for test results with visual indicators

### Changed
- Improved offline sync engine with delta updates reducing data transfer by 60%
- Enhanced Arabic RTL layout across all screens with improved typography
- Upgraded barcode scanning engine for better performance on Android 14+ devices
- Performance optimisations for patient databases exceeding 100,000 records
- Updated Kotlin SDK to support coroutines and Flow APIs

### Fixed
- Barcode scanning crash on devices running Android 14+
- Intermittent sync conflict with concurrent offline edits
- Arabic text rendering issues on iOS 18
- Memory leak in results dashboard when handling large datasets
- Edge case where push notifications were not delivered for critical values

### Security
- Upgraded biometric authentication with improved anti-spoofing
- Enhanced encryption key rotation mechanism
- Updated TLS configuration to enforce TLS 1.3

---

## [2.4.0] - 2026-05-20

### Added
- Integrated barcode and QR code scanning for specimen collection and verification
- Push notification support for critical results and order status changes
- Biometric authentication (Face ID / fingerprint) for secure app access
- Digital patient card generation with QR codes
- Offline mode with automatic sync

### Changed
- Redesigned results dashboard with colour-coded critical value flags
- Improved order management workflow with configurable test panels
- Updated UI/UX with Material Design 3
- Enhanced performance for large dataset handling

### Fixed
- Sync engine race condition during low-connectivity scenarios
- Patient search indexing issues with Arabic names
- Instrument integration timeout configuration

---

## [2.3.0] - 2026-03-15

### Added
- Instrument integration support for Sysmex, Roche, Mindray analysers
- ASTM/HL7 protocol adapter for bidirectional device communication
- Multi-facility support for laboratory networks
- Role-based access control with granular permissions

### Changed
- Migrated to Compose Multiplatform for Android UI
- Upgraded to Kotlin 2.0 for Android
- Updated SwiftUI implementation for iOS

### Fixed
- Database connection pool exhaustion under high load
- Audit log timestamp inconsistencies across timezones

---

## [2.2.0] - 2026-01-20

### Added
- Patient management with Master Patient Index deduplication
- Laboratory order creation and tracking
- Test result entry and validation with reference ranges
- Initial audit trail implementation
- Multi-language support (English + Arabic)

### Changed
- Complete UI redesign with RTL layout support
- Migration to modern Android architecture (Kotlin + Compose)
- iOS rewrite with SwiftUI

---

## [2.1.0] - 2025-11-01

### Added
- Initial mobile application release
- Basic patient lookup
- Test result viewing
- Secure authentication
- Arabic language support

---

## Template Instructions

For each new release:

1. Copy the `[Unreleased]` section template
2. Move all unreleased changes into the new version section
3. Add the version number and date
4. Categorise changes appropriately:
   - **Added**: New features
   - **Changed**: Changes to existing functionality
   - **Deprecated**: Features about to be removed
   - **Removed**: Removed features
   - **Fixed**: Bug fixes
   - **Security**: Security fixes
5. Update `mobile/version.json` with new version
6. Update version files in each platform project
7. Commit the changelog and version bump together

### Version Format
- **Android**: versionName and versionCode in `app/build.gradle.kts`
- **iOS**: CFBundleShortVersionString and CFBundleVersion in `Info.plist`
- **Flutter Desktop**: version in `pubspec.yaml`
- **Backend**: APP_VERSION in `config.py`
- **SDKs**: version in respective package files

### Maintaining the Changelog
- Changes should be grouped by platform where relevant
- Each entry should be a single concise sentence
- Reference issue/PR numbers where applicable
- Use present tense ("Add feature", not "Added feature") for unreleased
- Use past tense ("Added feature") for released versions
