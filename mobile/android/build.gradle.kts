buildscript {
    configurations.classpath {
        resolutionStrategy.eachDependency {
            if (requested.group == "org.bouncycastle") {
                useVersion("1.84")
                because("CVE-2025-14813 and related Bouncy Castle advisories")
            }
        }
    }
}

plugins {
    id("com.android.application") version "8.13.2" apply false
    id("com.android.library") version "8.13.2" apply false
    id("org.jetbrains.kotlin.android") version "2.1.20" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.1.20" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "2.1.20" apply false
    id("com.google.dagger.hilt.android") version "2.55" apply false
    id("com.google.devtools.ksp") version "2.1.20-1.0.31" apply false
}

allprojects {
    configurations.all {
        resolutionStrategy {
            force("io.netty:netty-codec-http2:4.1.118.Final")
            force("io.netty:netty-handler:4.1.118.Final")
            force("io.netty:netty-codec-http:4.1.118.Final")
            force("io.netty:netty-codec:4.1.118.Final")
            force("com.google.protobuf:protobuf-java:3.25.5")
            force("com.google.protobuf:protobuf-kotlin:3.25.5")
            force("org.jdom:jdom2:2.0.6.1")
            force("org.bouncycastle:bcprov-jdk18on:1.80")
            force("org.bitbucket.b_c:jose4j:0.9.6")
            force("org.apache.commons:commons-compress:1.26.0")
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
        }
    }
}
