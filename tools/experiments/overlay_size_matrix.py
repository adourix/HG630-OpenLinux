#!/usr/bin/env python3
"""Measure OEM RootFS size deltas for each overlay file and the full overlay."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.build_rootfs import build
from tools.experiments.oem_reproduction import summary


def run(source: Path, overlay: Path, output: Path, reserved: int = 5_931_008) -> dict[str, object]:
    source = source.resolve()
    overlay = overlay.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to reuse existing output directory: {output}")
    output.mkdir(parents=True)
    files = [path for path in sorted(overlay.rglob("*")) if path.is_file()]
    allow = [path.relative_to(overlay).as_posix() for path in files]
    results: list[dict[str, object]] = []

    def one(label: str, selected: list[Path]) -> None:
        target = output / label
        with tempfile.TemporaryDirectory(prefix="hg630-overlay-") as temporary:
            staged = Path(temporary) / "overlay"
            for path in selected:
                relative = path.relative_to(overlay)
                destination = staged / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                source_parent = path.parent
                parent_chain = []
                while source_parent != overlay:
                    parent_chain.append(source_parent)
                    source_parent = source_parent.parent
                for parent in reversed(parent_chain):
                    parent_destination = staged / parent.relative_to(overlay)
                    parent_destination.mkdir(parents=True, exist_ok=True)
                    shutil.copystat(parent, parent_destination, follow_symlinks=False)
                shutil.copy2(path, destination)
            if selected:
                report = build(source, [staged], target, processors=1, allowlist=[p.relative_to(staged).as_posix() for p in staged.rglob("*")])
            else:
                report = build(source, [], target, processors=1)
        image_summary = summary(target / "rootfs.squashfs")
        results.append({"label": label, "files": [p.relative_to(overlay).as_posix() for p in selected], "summary": image_summary, "delta_from_reserved": int(image_summary["bytes_used"]) - reserved, "build_report": report})

    one("baseline", [])
    for path in files:
        one("file-" + path.relative_to(overlay).as_posix().replace("/", "_"), [path])
    one("complete", files)
    report = {"schema": 1, "source": str(source), "overlay": str(overlay), "reserved_span": reserved, "results": results, "notes": ["The OEM source tree is copied without modifying OEM files.", "Results are host-side size experiments and do not establish kernel mount or device acceptance."]}
    (output / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.overlay, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
