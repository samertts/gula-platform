cmake_minimum_required(VERSION 3.14)
project(gula_desktop LANGUAGES CXX)

set(BINARY_NAME "gula_desktop")
set(FLUTTER_MANAGED_DIR "../flutter")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_definitions(-DUNICODE -D_UNICODE)

set(RUNNER_SOURCES
  main.cpp
  runner_utils.h
  runner_utils.cpp
  flutter_window.cpp
  flutter_window.h
)

add_executable(${BINARY_NAME} WIN32 ${RUNNER_SOURCES})

target_include_directories(${BINARY_NAME} PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")

target_link_libraries(${BINARY_NAME} PRIVATE
  flutter_wrapper_app
  comctl32.lib
  comdlg32.lib
  gdi32.lib
  kernel32.lib
  ole32.lib
  shell32.lib
  shlwapi.lib
  user32.lib
  uuid.lib
  version.lib
  winmm.lib
  ws2_32.lib
)

target_compile_definitions(${BINARY_NAME} PRIVATE
  NDEBUG
  FLUTTER_PLATFORM_WINDOWS
  UNICODE
  _UNICODE
)

add_custom_command(
  TARGET ${BINARY_NAME}
  POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_MANAGED_DIR}/app_icon.ico"
    "$<TARGET_FILE_DIR:${BINARY_NAME}>/app_icon.ico"
  COMMENT "Copying app icon"
)

set(INSTALL_BUNDLE_DIR "$<TARGET_FILE_DIR:${BINARY_NAME}>")
install(TARGETS ${BINARY_NAME} RUNTIME DESTINATION "${INSTALL_BUNDLE_DIR}")
