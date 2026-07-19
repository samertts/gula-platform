cmake_minimum_required(VERSION 3.13)
project(gula_desktop LANGUAGES Swift)

set(BINARY_NAME "GULA Platform")
set(FLUTTER_MANAGED_DIR "../flutter")

set(MACOSX_DEPLOYMENT_TARGET "10.14")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(${FLUTTER_MANAGED_DIR} flutter)

set(RUNNER_SOURCES
  AppDelegate.swift
  MainFlutterWindow.swift
)

add_executable(${BINARY_NAME} MACOSX_BUNDLE ${RUNNER_SOURCES})

target_include_directories(${BINARY_NAME} PRIVATE
  "${FLUTTER_MANAGED_DIR}"
  "${CMAKE_CURRENT_SOURCE_DIR}"
)

target_link_libraries(${BINARY_NAME} PRIVATE
  flutter_wrapper_flutter
  "-framework AppKit"
  "-framework Cocoa"
  "-framework CoreFoundation"
  "-framework CoreGraphics"
  "-framework CoreServices"
  "-framework FlutterMacOS"
  "-framework Foundation"
  "-framework IOKit"
  "-framework Security"
)

target_compile_options(${BINARY_NAME} PRIVATE
  -swift-version 5
)

set_target_properties(${BINARY_NAME} PROPERTIES
  MACOSX_BUNDLE_BUNDLE_NAME "GULA Platform"
  MACOSX_BUNDLE_BUNDLE_VERSION "2.1.0"
  MACOSX_BUNDLE_SHORT_VERSION_STRING "2.1.0"
  MACOSX_BUNDLE_BUNDLE_PACKAGE_TYPE "APPL"
  MACOSX_BUNDLE_COPYRIGHT "Copyright © 2025 GULA Platform"
  MACOSX_BUNDLE_GUI_IDENTIFIER "com.gula.platform.desktop"
  MACOSX_BUNDLE_ICON_FILE "app_icon.icns"
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist"
  XCODE_ATTRIBUTE_CODE_SIGN_ENTITLEMENTS
    "${CMAKE_CURRENT_SOURCE_DIR}/Release.entitlements"
  XCODE_ATTRIBUTE_DEVELOPMENT_TEAM ""
)

add_dependencies(${BINARY_NAME} flutter_assemble)

install(TARGETS ${BINARY_NAME} BUNDLE DESTINATION .)
