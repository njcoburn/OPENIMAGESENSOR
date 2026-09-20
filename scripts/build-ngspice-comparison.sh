#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs/build/ngspice-version-comparison
for version in 46 47; do
  test -d "ngspice-$version" || tar -xzf "ngspice-$version.tar.gz"
  mkdir -p "build-$version" "install-$version"
  (
    cd "build-$version"
    ../ngspice-"$version"/configure --prefix="/foss/designs/build/ngspice-version-comparison/install-$version" --with-x=no --with-readline=no --enable-klu --disable-debug CFLAGS='-O2' > configure.log 2>&1
    make -j4 > make.log 2>&1
    make install > install.log 2>&1
  )
  "install-$version/bin/ngspice" --version > "version-$version.txt"
  echo "Built ngspice $version"
done
sha256sum ngspice-*.tar.gz install-*/bin/ngspice > build-hashes.txt
