pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

// CVE-2026-59903: Pin the UTP/Gradle settings classpath to the patched Netty release.
buildscript {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    dependencies {
        classpath("io.netty:netty-codec-http:4.1.137.Final")
    }
    configurations.classpath {
        resolutionStrategy.force("io.netty:netty-codec-http:4.1.137.Final")
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "GULA"
include(":app")
