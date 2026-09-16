#!/usr/bin/env bash
# Run inside the pinned tools container.
set -euo pipefail
cd /foss/designs
python3 scripts/output-buffer.py
python3 scripts/check-buffer-acquisition.py
python3 scripts/build-overview.py
