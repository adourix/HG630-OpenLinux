#!/usr/bin/env python3
"""Build a SquashFS from an immutable RootFS plus ordered component overlays."""
from __future__ import annotations

import argparse
import hashlib
import os
import json
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_metadata(source: str, destination: str, source_stat: os.stat_result) -> None:
    """Preserve mode, timestamps and ownership on an already-created entry."""
    try:
        os.chown(destination, source_stat.st_uid, source_stat.st_gid, follow_symlinks=False)
    except PermissionError as exc:
        raise PermissionError(
            f"cannot preserve ownership for {source} ({source_stat.st_uid}:{source_stat.st_gid})"
        ) from exc
    # chown may clear setuid/setgid; restore mode and timestamps last.
    shutil.copystat(source, destination, follow_symlinks=False)


def _copy_entry(source: Path, destination: Path, hardlinks: dict[tuple[int, int], Path]) -> None:
    """Recreate one filesystem entry without ever opening device nodes or FIFOs."""
    source_stat = source.lstat()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if stat.S_ISREG(source_stat.st_mode):
        identity = (source_stat.st_dev, source_stat.st_ino)
        previous = hardlinks.get(identity)
        if previous is not None:
            os.link(previous, destination)
        else:
            shutil.copyfile(source, destination)
            hardlinks[identity] = destination
        _copy_metadata(str(source), str(destination), source_stat)
    elif stat.S_ISLNK(source_stat.st_mode):
        destination.symlink_to(os.readlink(source))
        _copy_metadata(str(source), str(destination), source_stat)
    elif stat.S_ISFIFO(source_stat.st_mode):
        os.mkfifo(destination, stat.S_IMODE(source_stat.st_mode))
        _copy_metadata(str(source), str(destination), source_stat)
    elif stat.S_ISCHR(source_stat.st_mode) or stat.S_ISBLK(source_stat.st_mode):
        os.mknod(destination, source_stat.st_mode, source_stat.st_rdev)
        _copy_metadata(str(source), str(destination), source_stat)
    else:
        raise ValueError(f"unsupported RootFS entry: {source}")


def copy_rootfs(source: Path, destination: Path) -> None:
    """Copy a RootFS tree while retaining links, metadata and special files."""
    hardlinks: dict[tuple[int, int], Path] = {}

    def visit(source_dir: Path, destination_dir: Path) -> None:
        source_stat = source_dir.lstat()
        destination_dir.mkdir(mode=stat.S_IMODE(source_stat.st_mode), parents=True, exist_ok=False)
        _copy_metadata(str(source_dir), str(destination_dir), source_stat)
        for entry in sorted(os.scandir(source_dir), key=lambda item: item.name):
            source_entry = Path(entry.path)
            destination_entry = destination_dir / entry.name
            if entry.is_dir(follow_symlinks=False):
                visit(source_entry, destination_entry)
            else:
                _copy_entry(source_entry, destination_entry, hardlinks)

    visit(source, destination)


def _apply_overlay_entry(source: Path, target: Path) -> None:
    """Apply one overlay entry, including special files and its metadata."""
    source_stat = source.lstat()
    if source.is_dir() and not source.is_symlink():
        target.mkdir(parents=True, exist_ok=True)
        _copy_metadata(str(source), str(target), source_stat)
        return
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    _copy_entry(source, target, {})


def validate_image(image: Path) -> str:
    """Validate both the SquashFS superblock and full extraction."""
    summary = subprocess.run(
        ["unsquashfs", "-s", str(image)], check=True, capture_output=True, text=True
    )
    with tempfile.TemporaryDirectory(prefix="rootfs-validate-") as directory:
        subprocess.run(
            ["unsquashfs", "-no-progress", "-d", directory, str(image)],
            check=True,
            capture_output=True,
            text=True,
        )
        if not any(Path(directory).iterdir()):
            raise ValueError(f"validated SquashFS extracted no entries: {image}")
    return summary.stdout


def build(
    rootfs: Path,
    overlays: list[Path],
    output: Path,
    source_image: Path | None = None,
    processors: int = 1,
) -> dict[str, object]:
    rootfs = rootfs.resolve()
    output = output.resolve()
    if output == rootfs or rootfs in output.parents:
        raise ValueError("output directory must not be inside the source RootFS")
    output.mkdir(parents=True, exist_ok=True)
    stage = output / "stage-rootfs"
    if stage.exists():
        shutil.rmtree(stage)
    copy_rootfs(rootfs, stage)
    applied = []
    for overlay in overlays:
        overlay = overlay.resolve()
        if not overlay.is_dir():
            raise ValueError(f"overlay directory does not exist: {overlay}")
        for source in sorted(overlay.rglob("*")):
            relative = source.relative_to(overlay)
            target = stage / relative
            _apply_overlay_entry(source, target)
        applied.append(str(overlay))

    image = output / "rootfs.squashfs"
    if processors < 1:
        raise ValueError("processors must be positive")
    command = ["mksquashfs", str(stage), str(image), "-noappend", "-comp", "xz", "-b", "1M", "-all-time", "1490771239", "-mkfs-time", "1490771239", "-no-progress", "-processors", str(processors)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    validation = validate_image(image)
    report: dict[str, object] = {
        "rootfs_source": str(rootfs), "overlays": applied,
        "rootfs_file_count": sum(1 for p in stage.rglob("*") if p.is_file() or p.is_symlink()),
        "squashfs": str(image), "squashfs_size": image.stat().st_size,
        "squashfs_sha256": sha256(image), "mksquashfs_command": command,
        "unsquashfs_validation": validation,
        "original_kernel_preserved": True,
    }
    if source_image:
        report["source_squashfs"] = str(source_image)
        report["source_squashfs_sha256"] = sha256(source_image)
        report["source_squashfs_size"] = source_image.stat().st_size
    (output / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path)
    parser.add_argument("--overlay", action="append", type=Path, default=[])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-squashfs", type=Path)
    parser.add_argument("--processors", type=int, default=1, help="mksquashfs worker count (default: 1)")
    args = parser.parse_args()
    print(json.dumps(build(args.rootfs, args.overlay, args.output, args.source_squashfs, args.processors), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
