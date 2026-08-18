import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.android.legacy-kapt")
    id("com.google.devtools.ksp")
    id("com.google.dagger.hilt.android")
}

configurations.all {
    resolutionStrategy {
        force("io.netty:netty-codec-http2:4.1.137.Final")
        force("io.netty:netty-handler:4.1.137.Final")
        force("io.netty:netty-handler-proxy:4.1.137.Final")
        force("io.netty:netty-codec-http:4.1.137.Final")
        force("io.netty:netty-codec:4.1.137.Final")
        force("com.google.protobuf:protobuf-java:3.25.5")
        force("com.google.protobuf:protobuf-kotlin:3.25.5")
        force("org.jdom:jdom2:2.0.6.1")
        force("org.bouncycastle:bcprov-jdk18on:1.80.2")
        force("org.bitbucket.b_c:jose4j:0.9.6")
        force("org.apache.commons:commons-compress:1.26.0")
        force("org.apache.httpcomponents:httpclient:4.5.14")
        force("org.apache.commons:commons-lang3:3.18.0")
    }
}
android {
    namespace = "io.gula.android"
    compileSdk = 37

    signingConfigs {
        create("release") {
            val injectedStoreFile = providers.gradleProperty("android.injected.signing.store.file").orNull
            val injectedStorePassword = providers.gradleProperty("android.injected.signing.store.password").orNull
            val injectedKeyAlias = providers.gradleProperty("android.injected.signing.key.alias").orNull
            val injectedKeyPassword = providers.gradleProperty("android.injected.signing.key.password").orNull
            val releaseSigningConfigured = listOf(
                injectedStoreFile,
                injectedStorePassword,
                injectedKeyAlias,
                injectedKeyPassword,
            ).all { !it.isNullOrBlank() }

            if (releaseSigningConfigured) {
                storeFile = file(requireNotNull(injectedStoreFile))
                storePassword = requireNotNull(injectedStorePassword)
                keyAlias = requireNotNull(injectedKeyAlias)
                keyPassword = requireNotNull(injectedKeyPassword)
            } else if (gradle.startParameter.taskNames.any { it.contains("Release", ignoreCase = true) }) {
                throw GradleException(
                    "Release signing is not configured. Inject the Android signing project properties from the approved CI secret store."
                )
            }
        }
    }

    // Release signing is deliberately supplied through CI project properties.
    // No local signing.properties or keystore is accepted from the repository.

        defaultConfig {
            applicationId = "iq.gula.lab"
            minSdk = 26
            targetSdk = 35
            versionCode = 20500
            versionName = "2.5.0"
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
            vectorDrawables { useSupportLibrary = true }
        }

        buildTypes {
            debug {
                isMinifyEnabled = false
                buildConfigField("String", "API_BASE_URL", "\"https://staging.gulaplatform.com/api/v1/\"")
                buildConfigField("String", "API_BASE_URL_ALTERNATE", "\"https://staging-api.gulaplatform.com/\"")
            }
            release {
                isMinifyEnabled = true
                isShrinkResources = true
                signingConfig = signingConfigs.getByName("release")
                proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
                buildConfigField("String", "API_BASE_URL", "\"https://api.gula-platform.org/api/v1/\"")
                buildConfigField("String", "API_BASE_URL_ALTERNATE", "\"https://api.gula-platform.org/\"")
            }
        }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        isCoreLibraryDesugaringEnabled = true
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    // Compose BOM
    val composeBom = platform("androidx.compose:compose-bom:2026.06.01")
    implementation(composeBom)
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material3:material3-window-size-class")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.runtime:runtime-livedata")
    implementation("androidx.compose.foundation:foundation")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")

    // Core
    implementation("androidx.core:core-ktx:1.19.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.activity:activity-compose:1.10.0")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.8.8")

    // Hilt
    implementation("com.google.dagger:hilt-android:2.60.1")
    kapt("com.google.dagger:hilt-android-compiler:2.60.1")
    implementation("androidx.hilt:hilt-navigation-compose:1.3.0")
    implementation("androidx.hilt:hilt-work:1.4.0")
    kapt("androidx.hilt:hilt-compiler:1.4.0")

    // Room
    implementation("androidx.room:room-runtime:2.8.4")
    implementation("androidx.room:room-ktx:2.8.4")
    kapt("androidx.room:room-compiler:2.8.4")

    // Retrofit + OkHttp
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.2")
    implementation("com.squareup.moshi:moshi-adapters:1.15.2")
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.2")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.squareup.okhttp3:okhttp-tls:4.12.0")

    // Kotlin Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    implementation("com.squareup.retrofit2:converter-kotlinx-serialization:2.11.0")

    // DataStore
    implementation("androidx.datastore:datastore-preferences:1.1.3")
    implementation("androidx.datastore:datastore-preferences-core:1.1.3")

    // WorkManager
    implementation("androidx.work:work-runtime-ktx:2.10.0")

    // Runtime permissions for Compose
    implementation("com.google.accompanist:accompanist-permissions:0.37.3")

    // CameraX
    val cameraxVersion = "1.5.0"
    implementation("androidx.camera:camera-core:$cameraxVersion")
    implementation("androidx.camera:camera-camera2:$cameraxVersion")
    implementation("androidx.camera:camera-lifecycle:$cameraxVersion")
    implementation("androidx.camera:camera-view:$cameraxVersion")

    // ML Kit Barcode Scanning
    implementation("com.google.mlkit:barcode-scanning:17.3.0")

    // Biometric
    implementation("androidx.biometric:biometric:1.1.0")

    // Security (EncryptedSharedPreferences)
    implementation("androidx.security:security-crypto:1.1.0")

    // Coil for image loading
    implementation("io.coil-kt:coil-compose:2.7.0")

    // Splash screen
    implementation("androidx.core:core-splashscreen:1.0.1")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.16.0")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
    testImplementation("app.cash.turbine:turbine:1.2.0")
    testImplementation("io.mockk:mockk:1.13.14")

    androidTestImplementation(composeBom)
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test:rules:1.6.1")
    androidTestImplementation("androidx.navigation:navigation-testing:2.8.8")
    androidTestImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")

    // Desugaring
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
}
