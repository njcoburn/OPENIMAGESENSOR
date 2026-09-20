#!/usr/bin/env bash
set -euo pipefail
root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$root_dir/build/magic-8.3.664-source"
output_dir="$root_dir/build/network-investigation"
mkdir -p "$output_dir"
test "$(git -C "$source_dir" rev-parse HEAD)" = 381714e2d5debf2ded71c5a6b6604e6b936422cf
git -C "$source_dir" diff --quiet
cd "$source_dir"
# Reuse the configured isolated build from build-export-diagnostic.sh.
test -f defs.mak
git apply "$root_dir/patches/magic-8.3.664-construction-trace.patch"
make -j1 > "$output_dir/build-trace.log" 2>&1
cp magic/magic "$output_dir/magic-trace"
git apply "$root_dir/patches/magic-8.3.664-triangle-offset.patch"
make -j1 > "$output_dir/build-reduction.log" 2>&1
cp magic/magic "$output_dir/magic-reduction-fixed"
git apply -R "$root_dir/patches/magic-8.3.664-triangle-offset.patch"
git apply -R "$root_dir/patches/magic-8.3.664-construction-trace.patch"
