#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:?Usage: extract_rootfs.sh <firmware.bin> [output-dir]}
OUT=${2:-artifacts/extracted}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$OUT"
python3 "$ROOT/tools/carve_firmware.py" "$IMAGE" --output "$OUT/carved"
FS="$OUT/carved/rootfs.squashfs"
if ! command -v unsquashfs >/dev/null 2>&1; then
  cat >&2 <<'EOF'
ERROR: unsquashfs is not installed.
Install/build squashfs-tools with legacy LZMA1 support, then retry.
This image reports SquashFS 4.0 compression ID 4 (LZMA).
A generic unsquashfs build without LZMA support may reject it.
EOF
  exit 2
fi
mkdir -p "$OUT/rootfs"
unsquashfs -d "$OUT/rootfs" "$FS"
echo "Extracted rootfs to $OUT/rootfs"
