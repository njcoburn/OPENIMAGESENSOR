#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp/kicad-home -v "$repo:/work" -w /work openimagesensor-kicad:7 "$@"
