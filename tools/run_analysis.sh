#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:?Usage: run_analysis.sh <firmware.bin> [output-dir]}
OUT=${2:-analysis/generated}
ROOT=$(cd "$(dirname "$0")/.." && pwd)

[[ -f "$IMAGE" ]] || { echo "error: firmware input not found: $IMAGE" >&2; exit 2; }
mkdir -p "$OUT"
python3 "$ROOT/tools/firmware_inspect.py" "$IMAGE" --json > "$OUT/firmware-inspect.json"
python3 "$ROOT/tools/carve_firmware.py" "$IMAGE" --output "$OUT/carved" > "$OUT/carve-summary.json"

if ! command -v unsquashfs >/dev/null 2>&1; then
  echo "error: unsquashfs is required for rootfs extraction" >&2
  exit 3
fi
unsquashfs -d "$OUT/rootfs" "$OUT/carved/rootfs.squashfs" > "$OUT/unsquashfs.log"
python3 "$ROOT/tools/inventory_rootfs.py" "$OUT/rootfs" -o "$OUT/rootfs-inventory.json" > "$OUT/rootfs-inventory-summary.json"
python3 "$ROOT/tools/detect_abi.py" "$OUT/rootfs" -o "$OUT/abi.json" > "$OUT/abi-summary.json"
echo "analysis complete: $OUT"
