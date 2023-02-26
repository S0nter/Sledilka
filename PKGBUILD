pkgname="Sledilka"
pkgver="1.2.6"
pkgrel="1"
pkgdesc="Self-control program written with PyQt"
arch=("x86_64")
depends=("python-pyqt5-sip" "python-pyqt5" "python3" "git")
license=("GPL3")
source=("https://github.com/S0nter/Sledilka.git")
sha512sums=("SKIP")
package() {
  mkdir -p "${pkgdir}/usr/bin"
  echo -e "#!/bin/bash\ncd /opt/Sledilka && python3 -m Sledilka" > "${pkgdir}/usr/bin/Sledilka"
  chmod +x "${pkgdir}/usr/bin/Sledilka"
  mkdir -p "${pkgdir}/opt/Sledilka/build"
  chown -R $USER:users "${pkgdir}/opt/Sledilka"
  cd "${pkgdir}/opt/Sledilka/build"
  git clone $source -q
  cd Sledilka
  chmod +x setup.sh
  ./setup.sh
  rm -dr ${pkgdir}/opt/Sledilka/build
  echo -e '\nNow for using Sledilka run "python3 -m Sledilka" command and the directory will be used by it\n'  # . Or just run "Sledilka" and it will run in /opt/Sledilka\r\n
}

