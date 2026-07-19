#include <flutter/dart_project.h>
#include <flutter/flutter_view_controller.h>
#include <flutter/method_channel.h>
#include <flutter/standard_method_codec.h>

#include <windows.h>
#include <windowsx.h>
#include <shellapi.h>

#include <memory>
#include <string>

#include "runner_utils.h"

namespace {

constexpr int kDesktopWidth = 1280;
constexpr int kDesktopHeight = 800;

void ScaleWindowForDpi(HWND hwnd, double dpi) {
  const double scale = dpi / 96.0;
  RECT rect;
  if (GetWindowRect(hwnd, &rect)) {
    int width = static_cast<int>(kDesktopWidth * scale);
    int height = static_cast<int>(kDesktopHeight * scale);
    SetWindowPos(hwnd, nullptr, rect.left, rect.top, width, height,
                 SWP_NOZORDER | SWP_NOACTIVATE);
  }
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wparam,
                            LPARAM lparam) {
  switch (msg) {
    case WM_DPICHANGED: {
      const double dpi = HIWORD(wparam);
      ScaleWindowForDpi(hwnd, dpi);
      RECT* const rect = reinterpret_cast<RECT*>(lparam);
      SetWindowPos(hwnd, nullptr, rect->left, rect->top,
                   rect->right - rect->left, rect->bottom - rect->top,
                   SWP_NOZORDER | SWP_NOACTIVATE);
      return 0;
    }
    case WM_DESTROY:
      PostQuitMessage(0);
      return 0;
    case WM_CLOSE:
      DestroyWindow(hwnd);
      return 0;
    case WM_SYSCOMMAND: {
      if ((wparam & 0xFFF0) == SC_MINIMIZE) {
        ShowWindow(hwnd, SW_MINIMIZE);
        return 0;
      }
      break;
    }
  }
  return DefWindowProc(hwnd, msg, wparam, lparam);
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE prev, LPSTR cmd_line,
                   int cmd_show) {
  const std::wstring app_name = L"GULA Platform";
  
  FlutterDesktopEnableHiDpiSupport(true);

  ::CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

  flutter::DartProject project(L"data");

  std::vector<std::string> command_line_arguments =
      GetCommandLineArguments();
  project.set_dart_entrypoint_arguments(std::move(command_line_arguments));

  FlutterWindowController flutter_controller;
  if (!flutter_controller.CreateViewForProcess(
          kDesktopWidth, kDesktopHeight, true, app_name, project)) {
    return EXIT_FAILURE;
  }

  HWND hwnd = flutter_controller.view()->GetNativeWindow();
  SetWindowLongPtr(hwnd, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(WindowProc));

  flutter_controller.Run();

  ::CoUninitialize();
  return EXIT_SUCCESS;
}
