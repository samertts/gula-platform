#include "my_application.h"

#include <flutter_linux/flutter_linux.h>
#include <gtk/gtk.h>

#include <string>

#include "flutter/generated_plugin_registrant.h"

struct _MyApplication {
  GtkApplication parent_instance;
  FlutterViewController* flutter_view;
};

G_DEFINE_TYPE(MyApplication, my_application, GTK_TYPE_APPLICATION)

static void activate_cb(GtkApplication* application, gpointer user_data) {
  auto* self = MY_APPLICATION(application);

  GtkWindow* window = GTK_WINDOW(gtk_application_window_new(application));
  gtk_window_set_default_size(window, 1280, 800);
  gtk_window_set_title(window, "GULA Platform");
  gtk_window_set_position(window, GTK_WIN_POS_CENTER);
  gtk_widget_set_name(GTK_WIDGET(window), "gula-desktop");

  GdkGeometry geom;
  geom.min_width = 800;
  geom.min_height = 600;
  gtk_window_set_geometry_hints(window, nullptr, &geom, GDK_HINT_MIN_SIZE);

  flutter::DartProject project("data");
  project.addPathPropertie("icu_data_path", "data/icudtl.dat");

  auto* flutter_view = flutter_view_new(project);
  self->flutter_view = flutter_view;

  GtkWidget* header_bar = gtk_header_bar_new();
  gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(header_bar), TRUE);
  gtk_header_bar_set_title(GTK_HEADER_BAR(header_bar), "GULA Platform");
  gtk_window_set_titlebar(window, header_bar);

  gtk_container_add(GTK_CONTAINER(window), GTK_WIDGET(flutter_view));
  gtk_widget_show_all(GTK_WIDGET(window));

  g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), nullptr);
}

static void open_cb(GtkApplication* application, GFile** files,
                    gint n_files, const gchar* hint, gpointer user_data) {
  // Handle file open requests if needed
}

MyApplication* my_application_new() {
  return MY_APPLICATION(g_object_new(
      my_application_get_type(), "application-id",
      "com.gula.platform.desktop", "resource-base-path",
      "/com/gula/platform/desktop", nullptr));
}

static void my_application_class_init(MyApplicationClass* klass) {
  G_APPLICATION_CLASS(klass)->activate = activate_cb;
  G_APPLICATION_CLASS(klass)->open = open_cb;
}

static void my_application_init(MyApplication* self) {}
