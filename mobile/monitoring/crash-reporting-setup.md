# Crash Reporting Setup for GULA Platform Mobile Apps

This document describes how to configure crash reporting for GULA Platform mobile applications using Sentry and Datadog.

## Overview

GULA Platform uses two crash reporting solutions:
- **Sentry**: Primary crash reporting, symbolication, and issue tracking
- **Datadog RUM**: Real User Monitoring for performance and crash analytics

## Sentry Setup

### Prerequisites
1. Sentry account with access to `gula-platform` organization
2. Sentry auth token with `project:write` and `org:read` scopes
3. Sentry DSN for each project (android, ios, flutter-desktop)

### Android Setup

#### 1. Add Sentry Gradle plugin
In `mobile/android/build.gradle.kts` (root):
```kotlin
plugins {
    id("io.sentry.android.gradle") version "4.14.0" apply false
}
```

In `mobile/android/app/build.gradle.kts`:
```kotlin
plugins {
    id("io.sentry.android.gradle")
}

android {
    // ... existing configuration
}

sentry {
    includeProguardMapping = true
    uploadNativeSymbols = true
    autoUploadProguardMapping = true
    org.set("gula-platform")
    projectName.set("android")
    authToken.set(System.getenv("SENTRY_AUTH_TOKEN"))
}
```

#### 2. Initialize Sentry in Application class
```kotlin
import io.sentry.Sentry
import io.sentry.android.core.SentryAndroid

class GulaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        SentryAndroid.init(this) { options ->
            options.dsn = BuildConfig.SENTRY_DSN
            options.environment = BuildConfig.BUILD_TYPE
            options.release = "${BuildConfig.VERSION_NAME}-${BuildConfig.VERSION_CODE}"
            options.tracesSampleRate = 0.2
            options.isEnableUserInteractionTracing = true
            options.isEnableAppLifecycleBreadcrumbs = true
            options.isEnableSystemEventBreadcrumbs = true
            options.isEnableAppHangTracking = true
            options.appHangTimeoutIntervalMillis = 4000
        }
        
        // Set user context if available
        authManager.currentUser?.let { user ->
            Sentry.setUser(io.sentry.protocol.User().apply {
                id = user.id
                email = user.email
                username = user.name
                data = mapOf("lab_id" to user.labId)
            })
        }
    }
}
```

### iOS Setup

#### 1. Add Sentry via SPM
In Xcode: File > Add Package Dependency > `https://github.com/getsentry/sentry-cocoa`
Version: 8.40.0 or later

#### 2. Initialize Sentry
```swift
import Sentry

@main
struct GulaApp: App {
    init() {
        SentrySDK.start { options in
            options.dsn = Configuration.sentryDSN
            options.environment = Configuration.buildType
            options.releaseName = "\(Configuration.version)-\(Configuration.buildNumber)"
            options.tracesSampleRate = 0.2
            options.enableUserInteractionTracing = true
            options.enableAutoBreadcrumbTracking = true
            options.enableAppHangTracking = true
            options.appHangTimeoutInterval = 4.0
            options.attachScreenshot = false
            options.attachViewHierarchy = true
        }
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear {
                    // Set user context
                    if let user = authManager.currentUser {
                        let userObj = User()
                        userObj.id = user.id
                        userObj.email = user.email
                        userObj.username = user.name
                        userObj.data = ["lab_id": user.labId]
                        SentrySDK.setUser(userObj)
                    }
                }
        }
    }
}
```

### Flutter Desktop Setup

#### 1. Add Sentry dependency
In `mobile/desktop/pubspec.yaml`:
```yaml
dependencies:
  sentry_flutter: ^8.10.0
```

#### 2. Initialize Sentry
```dart
import 'package:sentry_flutter/sentry_flutter.dart';

Future<void> main() async {
  await SentryFlutter.init(
    (options) {
      options.dsn = const String.fromEnvironment('SENTRY_DSN');
      options.environment = const String.fromEnvironment('ENVIRONMENT');
      options.release = '${const String.fromEnvironment('VERSION')}-${const String.fromEnvironment('BUILD_NUMBER')}';
      options.tracesSampleRate = 0.2;
      options.enableUserInteractionTracing = true;
      options.enableAppLifecycleBreadcrumbs = true;
      options.maxBreadcrumbs = 200;
    },
    appRunner: () => runApp(const GulaApp()),
  );
}
```

## Datadog RUM Setup

### Prerequisites
1. Datadog account with RUM enabled
2. Datadog client token (not API key)
3. RUM application ID

### Android Setup

```kotlin
// In app/build.gradle.kts
dependencies {
    implementation("com.datadoghq:dd-sdk-android-rum:2.13.0")
    implementation("com.datadoghq:dd-sdk-android-logs:2.13.0")
    implementation("com.datadoghq:dd-sdk-android-trace:2.13.0")
}

// In GulaApp.kt initialization
import com.datadog.android.Datadog
import com.datadog.android.DatadogSite
import com.datadog.android.privacy.TrackingConsent
import com.datadog.android.rum.GlobalRum
import com.datadog.android.rum.RumConfiguration
import com.datadog.android.rum.tracking.ActivityViewTrackingStrategy
import com.datadog.android.rum.tracking.FragmentViewTrackingStrategy
import com.datadog.android.log.Logger
import com.datadog.android.tracing.TracingConfiguration

class GulaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        val configuration = DatadogConfiguration.Builder(
            clientToken = BuildConfig.DATADOG_CLIENT_TOKEN,
            environment = BuildConfig.BUILD_TYPE,
            service = "gula-platform-android"
        )
            .setSite(DatadogSite.US1)
            .setTrackingConsent(TrackingConsent.GRANTED)
            .build()
        
        Datadog.initialize(this, configuration)
        
        val rumConfig = RumConfiguration.Builder(BuildConfig.DATADOG_RUM_APP_ID)
            .setSessionSampleRate(80.0f)
            .setTelemetrySampleRate(20.0f)
            .setTrackFrustrations(true)
            .setTrackBackgroundEvents(true)
            .useViewTrackingStrategy(ActivityViewTrackingStrategy(true))
            .addFirstPartyHosts(listOf("api.gulaplatform.com"))
            .build()
        
        GlobalRum.registerIfAbsent(rumConfig)
        
        // Configure logging
        val logger = Logger.Builder()
            .setNetworkInfoEnabled(true)
            .setLogcatLogsEnabled(BuildConfig.DEBUG)
            .setDatadogLogsEnabled(true)
            .setBundleWithTraceEnabled(true)
            .build()
        
        // Set user info when available
        authManager.currentUser?.let { user ->
            Datadog.setUserInfo(user.id, user.email, user.name, mapOf("lab_id" to user.labId))
        }
    }
}
```

### iOS Setup

```swift
// In AppDelegate or App initialization
import DatadogCore
import DatadogRUM
import DatadogLogs

class GulaAppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        Datadog.initialize(
            with: Datadog.Configuration(
                clientToken: Configuration.datadogClientToken,
                env: Configuration.buildType,
                service: "gula-platform-ios"
            ),
            trackingConsent: .granted
        )
        
        let rumConfiguration = RUM.Configuration(
            applicationID: Configuration.datadogRUMAppID
        )
        rumConfiguration.sessionSampleRate = 80
        rumConfiguration.telemetrySampleRate = 20
        rumConfiguration.trackFrustrations = true
        rumConfiguration.trackBackgroundEvents = true
        rumConfiguration.firstPartyHosts = ["api.gulaplatform.com"]
        
        RUM.enable(with: rumConfiguration)
        Logs.enable()
        
        return true
    }
}
```

### Flutter Desktop Setup

```dart
// In main.dart
import 'package:datadog_flutter/datadog_flutter.dart';
import 'package:datadog_common/datadog_common.dart';

Future<void> main() async {
  final datadogSdk = DatadogSdk(
    configuration: DatadogConfiguration(
      clientToken: const String.fromEnvironment('DATADOG_CLIENT_TOKEN'),
      env: const String.fromEnvironment('ENVIRONMENT'),
      service: 'gula-platform-flutter',
      site: DatadogSite.us1,
      trackingConsent: TrackingConsent.granted,
      nativeCrashReportEnabled: true,
    ),
  );

  await datadogSdk.initialize();

  DatadogRumConfiguration rumConfiguration = DatadogRumConfiguration(
    applicationId: const String.fromEnvironment('DATADOG_RUM_APP_ID'),
    sessionSampleRate: 80.0,
    telemetrySampleRate: 20.0,
    trackFrustrations: true,
    firstPartyHosts: ['api.gulaplatform.com'],
  );

  datadogSdk.rum?.addRumConfiguration(rumConfiguration);

  runApp(const GulaApp());
}
```

## CI/CD Integration

### Sentry Upload Steps

#### Android (in CI workflow)
```yaml
- name: Upload ProGuard mapping to Sentry
  if: github.ref == 'refs/heads/main'
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
  run: |
    sentry-cli --auth-token $SENTRY_AUTH_TOKEN \
      upload-proguard \
      --org gula-platform \
      --project android \
      --version $VERSION \
      mobile/android/app/build/outputs/mapping/release/mapping.txt
```

#### iOS (in CI workflow)
```yaml
- name: Upload dSYMs to Sentry
  if: github.ref == 'refs/heads/main'
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
  run: |
    sentry-cli --auth-token $SENTRY_AUTH_TOKEN \
      upload-dsym \
      --org gula-platform \
      --project ios \
      --version $VERSION \
      mobile/ios/build/*.dSYM.zip
```

#### Flutter (in CI workflow)
```yaml
- name: Upload Flutter debug symbols to Sentry
  if: github.ref == 'refs/heads/main'
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
  run: |
    sentry-cli --auth-token $SENTRY_AUTH_TOKEN \
      upload-dif \
      --org gula-platform \
      --project flutter-desktop \
      --version $VERSION \
      mobile/desktop/build/
```

## Testing Crash Reporting

### Test Crash Buttons (Development Only)
Include test crash functionality in debug builds only:

#### Android
```kotlin
if (BuildConfig.DEBUG) {
    Button(onClick = { Sentry.captureMessage("Test debug message") }) {
        Text("Test Sentry Message")
    }
    Button(onClick = { throw RuntimeException("Test crash for Sentry") }) {
        Text("Test Crash")
    }
}
```

#### iOS
```swift
#if DEBUG
Button("Test Sentry Message") {
    SentrySDK.capture(message: "Test debug message")
}
Button("Test Crash") {
    SentrySDK.crash()
}
#endif
```

#### Flutter
```dart
if (kDebugMode) {
  ElevatedButton(
    onPressed: () => Sentry.captureMessage('Test debug message'),
    child: const Text('Test Sentry Message'),
  );
  ElevatedButton(
    onPressed: () => throw Exception('Test crash for Sentry'),
    child: const Text('Test Crash'),
  );
}
```

## Monitoring Dashboards

### Sentry
- **Issues**: https://sentry.io/organizations/gula-platform/issues/
- **Performance**: https://sentry.io/organizations/gula-platform/performance/
- **Releases**: https://sentry.io/organizations/gula-platform/releases/

### Datadog
- **RUM**: https://app.datadoghq.com/rum/explorer
- **Mobile Overview Dashboard**: Created automatically after first data ingestion
- **Custom Dashboards**: Available in Datadog Dashboards section

## Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Crash-free session rate | < 99.5% | < 99.0% | Page dev team |
| Error rate | > 1% | > 3% | Investigate errors |
| ANR rate (Android) | > 0.5% | > 1% | Profile app |
| App start time | > 3s | > 5s | Profile startup |
| Network error rate | > 2% | > 5% | Check API status |

## FAQ

### Q: Why use both Sentry and Datadog?
Sentry provides detailed crash analysis with symbolication and issue tracking. Datadog RUM provides broader performance monitoring, user session replay, and integration with other Datadog infrastructure monitoring.

### Q: How do I get the Sentry auth token?
1. Go to https://sentry.io/settings/account/api/auth-tokens/
2. Create new token with `project:write` and `org:read` scopes
3. Add to GitHub Secrets as `SENTRY_AUTH_TOKEN`

### Q: How do I get Datadog credentials?
1. Go to Datadog > UX Monitoring > RUM Applications > New Application
2. Copy Client Token and Application ID
3. Add to GitHub Secrets as `DATADOG_CLIENT_TOKEN` and `DATADOG_RUM_APP_ID`

### Q: Are crash reports disabled in debug builds?
Yes. Sentry auto-detects debug builds unless explicitly enabled. Datadog respects the build configuration.

### Q: What about user privacy?
- No personally identifiable information is sent to crash reporting services
- User IDs are internal platform IDs, not personal information
- Biometric data is never included in crash reports
- All crash data is transmitted over TLS 1.3
