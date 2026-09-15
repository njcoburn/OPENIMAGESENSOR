#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
image=${IIC_OSIC_IMAGE:-hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a}
name=${IIC_VNC_NAME:-openimagesensor-vnc}
if docker container inspect "$name" >/dev/null 2>&1; then
 echo "Container $name already exists. Use docker start $name if stopped."
 exit 0
fi
docker run -d --name "$name" --user "$(id -u):$(id -g)" \
 --shm-size=1g -p 127.0.0.1:8080:80 -p 127.0.0.1:5902:5901 \
 -v "$repo_dir:/foss/designs" -e PDK=gf180mcuD -e PDK_ROOT=/foss/pdks \
 -e PDKPATH=/foss/pdks/gf180mcuD -e VNC_RESOLUTION=1680x1050 "$image"
echo 'Open http://localhost:8080/vnc.html?autoconnect=true&resize=scale (image default password: abc123).'
