pkgname="Sledilka"
pkgver="1.2.7"
pkgrel="2"
pkgdesc="Self-control program written with PyQt"
arch=("x86_64")
depends=("python-pyqt5-sip" "python-pyqt5" "python3" "git")
license=("GPL3")
package() {
  mkdir -p "${pkgdir}/usr/bin"
  echo -e "#!/bin/bash\ncd /opt/Sledilka && python3 -m Sledilka.Sledilka" > "${pkgdir}/usr/bin/sledilka"
  chmod +x "${pkgdir}/usr/bin/sledilka"
  mkdir -p "${pkgdir}/opt/Sledilka/build"
  chown -R $USER:users "${pkgdir}/opt/Sledilka"
  cd "${pkgdir}/opt/Sledilka/build"
  git clone "https://github.com/S0nter/Sledilka.git"
  cd Sledilka
  chmod +x setup.sh
  ./setup.sh "${pkgdir}"  # /usr/lib/$(readlink $(which python3))/site-packages
  rm -dr "${pkgdir}/opt/Sledilka/build"
  rm -rdf "${pkgdir}/bin"
  mv "${pkgdir}/lib" "${pkgdir}/usr/lib"
  pypkg="$(ls "${pkgdir}/usr/lib/$(readlink $(which python3))/site-packages" | grep "Sledilka")"
  mv "${pkgdir}/usr/lib/$(readlink $(which python3))/site-packages/${pypkg}" "${pkgdir}/usr/lib/$(readlink $(which python3))/site-packages/Sledilka"
  chown -R $USER:users "${pkgdir}/usr/lib/$(readlink $(which python3))/site-packages/Sledilka"
  mkdir -p "${pkgdir}/usr/share/applications"
  cat > "${pkgdir}/usr/share/applications/Sledilka.desktop" << EOF
[Desktop Entry]
Type=Application
Exec=sledilka
Path=/opt/Sledilka
Icon=/usr/lib/$(readlink $(which python3))/site-packages/Sledilka/icon.ico
StartupNotify=true
Terminal=false
TerminalOptions=
X-DBUS-ServiceName=Sledilka
X-DBUS-StartupType=Unique
X-GNOME-Autostart-enabled=true
X-KDE-SubstituteUID=false
X-KDE-Username=
Hidden=false
NoDisplay=false
Name[en_IN]=Sledilka
Name[ru_RU]=Следилка
Name=Sledilka
Comment[en_IN]=
Comment=
EOF

  echo -e '\nNow for using Sledilka run "python3 -m Sledilka.Sledilka" command and the directory will be used by it\n'  # . Or just run "Sledilka" and it will run in /opt/Sledilka\r\n
}
