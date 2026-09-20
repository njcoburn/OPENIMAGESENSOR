#!/usr/bin/env bash
# Run inside the pinned tools container after fetching the source as documented.
set -euo pipefail
root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$root_dir/build/magic-8.3.664-source"
output_dir="$root_dir/build/extraction-diagnostics"
mkdir -p "$output_dir"
test "$(git -C "$source_dir" rev-parse HEAD)" = 381714e2d5debf2ded71c5a6b6604e6b936422cf
git -C "$source_dir" diff --quiet
cd "$source_dir"
git apply "$root_dir/patches/magic-8.3.664-resistor-reader.patch"
./configure --prefix="$root_dir/build/magic-export-diagnostic" --without-x > "$output_dir/configure.log" 2>&1
# Serial build avoids a generated database-header dependency race.
make -j1 > "$output_dir/make-serial.log" 2>&1
make install > "$output_dir/install.log" 2>&1
cp "$root_dir/build/magic-export-diagnostic/bin/magic" "$output_dir/magic-patched"
git apply -R "$root_dir/patches/magic-8.3.664-resistor-reader.patch"
make -j1 > "$output_dir/make-baseline.log" 2>&1
make install > "$output_dir/install-baseline.log" 2>&1
cd "$root_dir"
python3 scripts/check-export-patch.py
python3 scripts/check-export-patch.py --baseline
