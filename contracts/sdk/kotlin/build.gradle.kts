plugins {
    kotlin("jvm") version "2.1.20"
    kotlin("plugin.serialization") version "2.1.20"
    id("io.gitlab.arturbosch.detekt") version "1.23.8"
    `maven-publish`
}

group = "io.gula.sdk"
version = "1.0.0"

repositories {
    mavenCentral()
}

val ktorVersion = "3.1.2"
val kotlinxSerializationVersion = "1.8.0"
val kotlinxCoroutinesVersion = "1.11.0"
val logbackVersion = "1.6.1"

dependencies {
    // Ktor Client
    implementation("io.ktor:ktor-client-core:$ktorVersion")
    implementation("io.ktor:ktor-client-cio:$ktorVersion")
    implementation("io.ktor:ktor-client-content-negotiation:$ktorVersion")
    implementation("io.ktor:ktor-serialization-kotlinx-json:$ktorVersion")
    implementation("io.ktor:ktor-client-logging:$ktorVersion")
    implementation("io.ktor:ktor-client-auth:$ktorVersion")

    // Kotlinx Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:$kotlinxSerializationVersion")

    // Kotlinx Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$kotlinxCoroutinesVersion")

    // Logging
    implementation("ch.qos.logback:logback-classic:$logbackVersion")

    // Testing
    testImplementation("org.jetbrains.kotlin:kotlin-test:2.1.20")
    testImplementation("io.ktor:ktor-client-mock:$ktorVersion")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:$kotlinxCoroutinesVersion")
}

kotlin {
    jvmToolchain(17)
}

tasks.withType<Test> {
    useJUnitPlatform()
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            from(components["java"])
            pom {
                name.set("GULA Platform Kotlin SDK")
                description.set("Official Kotlin SDK for the GULA Platform API")
                url.set("https://github.com/samertts/gula-platform")
                licenses {
                    license {
                        name.set("MIT License")
                        url.set("https://opensource.org/licenses/MIT")
                    }
                }
            }
        }
    }
}
