Name:           gula-platform
Version:        2.1.0
Release:        1%{?dist}
Summary:        GULA Platform medical laboratory desktop client
License:        Proprietary
URL:            https://github.com/samertts/gula-platform
Source0:        %{name}-%{version}.tar.gz
Source1:        gula_desktop.desktop
Source2:        gula_desktop.png
BuildArch:       x86_64

%description
Secure desktop application for medical laboratory information management.

%prep
%setup -q

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/gula-platform
cp -a . %{buildroot}/opt/gula-platform/
install -Dpm 755 /dev/null %{buildroot}/usr/bin/gula_desktop
cat > %{buildroot}/usr/bin/gula_desktop <<'EOF'
#!/bin/sh
exec /opt/gula-platform/gula_desktop "$@"
EOF
install -Dpm 644 %{SOURCE1} %{buildroot}/usr/share/applications/gula_desktop.desktop
install -Dpm 644 %{SOURCE2} %{buildroot}/usr/share/icons/hicolor/512x512/apps/gula_desktop.png

%files
/opt/gula-platform
/usr/bin/gula_desktop
/usr/share/applications/gula_desktop.desktop
/usr/share/icons/hicolor/512x512/apps/gula_desktop.png

%changelog
* Thu Aug 13 2026 GULA Platform <apps@gulaplatform.com> - 2.1.0-1
- Initial desktop package
