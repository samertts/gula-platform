buildscript {
    configurations.classpath {
        resolutionStrategy {
            force("io.netty:netty-codec-http2:4.1.136.Final")
            force("io.netty:netty-handler:4.1.136.Final")
            force("io.netty:netty-handler-proxy:4.1.136.Final")
            force("io.netty:netty-codec-http:4.1.136.Final")
            force("io.netty:netty-codec:4.1.136.Final")
            force("com.google.protobuf:protobuf-java:3.25.5")
            force("com.google.protobuf:protobuf-kotlin:3.25.5")
            force("com.google.guava:guava:33.4.0-jre")
            force("org.jdom:jdom2:2.0.6.1")
            force("org.bouncycastle:bcprov-jdk18on:1.84")
            force("org.bitbucket.b_c:jose4j:0.9.6")
            force("org.apache.commons:commons-compress:1.26.0")
            force("org.apache.httpcomponents:httpclient:4.5.14")
            force("org.apache.commons:commons-lang3:3.18.0")
            eachDependency {
                if (requested.group == "org.bouncycastle") {
                    useVersion("1.84")
                    because("CVE-2025-14813 and related Bouncy Castle advisories")
                }
                if (requested.group == "org.apache.httpcomponents" && requested.name == "httpclient") {
                    useVersion("4.5.14")
                    because("CVE-2020-13956: Apache HttpClient request-target XSS")
                }
                if (requested.group == "org.apache.commons" && requested.name == "commons-lang3") {
                    useVersion("3.18.0")
                    because("CVE-2025-48924: Commons Lang uncontrolled recursion")
                }
            }
        }
    }
}

plugins {
    id("com.android.application") version "9.3.1" apply false
    id("com.android.library") version "9.3.1" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20-RC" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "2.4.20-RC" apply false
    id("com.android.legacy-kapt") version "9.3.1" apply false
    id("com.google.devtools.ksp") version "2.3.11" apply false
    id("com.google.dagger.hilt.android") version "2.60.1" apply false
}

allprojects {
    configurations.all {
        resolutionStrategy {
            force("io.netty:netty-codec-http2:4.1.136.Final")
            force("io.netty:netty-handler:4.1.136.Final")
            force("io.netty:netty-handler-proxy:4.1.136.Final")
            force("io.netty:netty-codec-http:4.1.136.Final")
            force("io.netty:netty-codec:4.1.136.Final")
            force("com.google.protobuf:protobuf-java:3.25.5")
            force("com.google.protobuf:protobuf-kotlin:3.25.5")
            force("com.google.guava:guava:33.4.0-jre")
            force("org.jdom:jdom2:2.0.6.1")
            force("org.bouncycastle:bcprov-jdk18on:1.80.2")
            force("org.bitbucket.b_c:jose4j:0.9.6")
            force("org.apache.commons:commons-compress:1.26.0")
            force("org.apache.httpcomponents:httpclient:4.5.14")
            force("org.apache.commons:commons-lang3:3.18.0")
        }
    }
}

tasks.register("clean", Delete::class) {
    delete(rootProject.layout.buildDirectory)
}

// Security baseline: AGP 8.13.2 currently brings Bouncy Castle 1.79 transitively.
// Keep the cryptographic family aligned on the patched 1.84 release across all
// project configurations, including bcpkix and bcutil consumers.
allprojects {
    configurations.configureEach {
        resolutionStrategy.eachDependency {
            if (requested.group == "org.bouncycastle") {
                useVersion("1.84")
                because("CVE-2025-14813 and related Bouncy Castle advisories")
            }
            if (requested.group == "org.apache.httpcomponents" && requested.name == "httpclient") {
                useVersion("4.5.14")
                because("CVE-2020-13956: Apache HttpClient request-target XSS")
            }
            if (requested.group == "org.apache.commons" && requested.name == "commons-lang3") {
                useVersion("3.18.0")
                because("CVE-2025-48924: Commons Lang uncontrolled recursion")
            }
        }
    }
}
