# GULA — Google Play Console Integration Guide

## 1. Overview

This guide details how to publish and maintain **GULA Health** (`io.gula.health`) on **Google Play Console** as the official national healthcare platform serving public, private, and mixed health sectors.

## 2. Prerequisites in Google Play Console

1. **Developer Account**: Active Google Play Developer Account with verified identity.
2. **App Creation**:
   - App name: `GULA Health`
   - Default language: Arabic (`ar`) / English (`en`)
   - App type: Apps
   - Category: Medical / Health & Fitness
3. **Store Listing Assets**:
   - High-resolution icon (512x512px)
   - Feature graphic (1024x500px)
   - Screenshots for Phone (1080x1920px) supporting RTL layout
   - Privacy Policy URL hosted on the platform (`https://www.gula-platform.org/privacy`)

## 3. App Bundle (.aab) Build & Signing & Secrets Management

The Android project is structured under `/android` in this repository. Production signing keys, Upload Keys, and API credentials for Google Play Console must never be stored in plaintext within the repository. Instead, they are managed securely using the platform's secret request utility (`webdev_request_secrets`).

### Play App Signing & Key Architecture
- **Upload Key**: Used to sign the App Bundle (`.aab`) before uploading it to Google Play Console. Managed securely and never exposed.
- **App Signing Key**: Managed securely by Google Play on Google's secure servers, used to sign APKs delivered to users.
- **Secret Management**: Keystore passwords and key aliases are requested via `webdev_request_secrets` at build/release time.

To build a signed App Bundle for Google Play Console:

```bash
# 1. Request release signing environment secrets securely
# (Managed via webdev_request_secrets tool in the sandbox environment)
export GULA_KEYSTORE_PASSWORD="$GULA_KEYSTORE_PASSWORD"
export GULA_KEY_ALIAS="$GULA_KEY_ALIAS"
export GULA_KEY_PASSWORD="$GULA_KEY_PASSWORD"

# 2. Build release bundle
cd android
./gradlew bundleRelease
```

The resulting signed App Bundle will be located at:
`android/app/build/outputs/bundle/release/app-release.aab`

## 4. Google Play Console Upload & Release Tracks

1. Navigate to **Google Play Console** -> **GULA Health** -> **Production** (or **Internal testing**).
2. Click **Create new release**.
3. Upload `app-release.aab`.
4. Enter release notes in Arabic and English describing the national health platform update (LIS, hospitals, clinics, pharmacy, radiology, emergency, and public health).
5. Submit for review.
