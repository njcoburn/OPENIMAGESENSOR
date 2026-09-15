#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
image=${IIC_OSIC_IMAGE:-hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a}
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$repo_dir:/foss/designs" -w /foss/designs \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e PDK=gf180mcuD -e PDK_ROOT=/foss/pdks \
  -e PDKPATH=/foss/pdks/gf180mcuD \
  -e SPICE_USERINIT_DIR=/foss/pdks/gf180mcuD/libs.tech/ngspice \
  --entrypoint /bin/bash "$image" -lc 'exec "$@"' bash "$@"
