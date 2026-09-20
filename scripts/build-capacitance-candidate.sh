#!/usr/bin/env bash
set -euo pipefail
root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$root_dir/build/magic-8.3.664-source"
output_dir="$root_dir/build/capacitance-candidate"
mkdir -p "$output_dir"
test "$(git -C "$source_dir" rev-parse HEAD)" = 381714e2d5debf2ded71c5a6b6604e6b936422cf
git -C "$source_dir" diff --quiet
cd "$source_dir"
reader_applied=0
triangle_applied=0
area_applied=0
cleanup() {
  if [ "$area_applied" = 1 ]; then git apply -R "$root_dir/patches/magic-8.3.664-single-break-area.patch"; fi
  if [ "$triangle_applied" = 1 ]; then git apply -R "$root_dir/patches/magic-8.3.664-triangle-offset.patch"; fi
  if [ "$reader_applied" = 1 ]; then git apply -R "$root_dir/patches/magic-8.3.664-resistor-reader.patch"; fi
}
trap cleanup EXIT
git apply "$root_dir/patches/magic-8.3.664-resistor-reader.patch"
reader_applied=1
git apply "$root_dir/patches/magic-8.3.664-triangle-offset.patch"
triangle_applied=1
git apply "$root_dir/patches/magic-8.3.664-single-break-area.patch"
area_applied=1
make -j1 > "$output_dir/build.log" 2>&1
cp magic/magic "$output_dir/magic-area-fixed"
