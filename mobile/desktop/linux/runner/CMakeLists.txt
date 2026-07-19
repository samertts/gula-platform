cmake_minimum_required(VERSION 3.13)
project(gula_desktop LANGUAGES CXX)

set(BINARY_NAME "gula_desktop")
set(FLUTTER_MANAGED_DIR "../flutter")

cmake_policy(SET CMP0063 NEW)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(${FLUTTER_MANAGED_DIR} flutter)

set(RUNNER_SOURCES
  main.cc
  my_application.cc
  my_application.h
)

add_executable(${BINARY_NAME} ${RUNNER_SOURCES})

target_include_directories(${BINARY_NAME} PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}"
  "${FLUTTER_MANAGED_DIR}"
)

target_link_libraries(${BINARY_NAME} PRIVATE
  flutter_wrapper_plugin
  flutter_wrapper_app
  PkgConfig::GTK
  PkgConfig::GLIB
  PkgConfig::atk
  PkgConfig::cairo
  PkgConfig::pango
  PkgConfig::freetype2
  PkgConfig::fontconfig
  PkgConfig::x11
)

add_dependencies(${BINARY_NAME} flutter_assemble)

install(TARGETS ${BINARY_NAME} RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")

# AppImage packaging support
install(FILES "${CMAKE_SOURCE_DIR}/linux/resources/gula_desktop.desktop"
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/applications")
install(FILES "${CMAKE_SOURCE_DIR}/linux/resources/gula_desktop.png"
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/512x512/apps")
