#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python3 scripts/prepare-size-study.py
for size in 5 10 20; do
 python3 "build/size-study/${size}um/scripts/make-array-schematics.py"
 (cd "build/size-study/${size}um" && bash scripts/verify-array.sh > verification-run.log 2>&1)
done
bash scripts/run-tools.sh python3 scripts/compare-diode-sizes.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
