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
import fnmatch
from pathlib import Path, PurePosixPath


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


def _overlay_path_allowed(relative: str, patterns: list[str]) -> bool:
    """Allow an exact/glob match, or a directory that is an ancestor of one."""
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return False
    for raw in patterns:
        pattern = PurePosixPath(raw)
        if pattern.is_absolute() or ".." in pattern.parts or not pattern.parts:
            raise ValueError(f"unsafe overlay allowlist pattern: {raw}")
        parts = pattern.parts
        if fnmatch.fnmatchcase(relative, raw):
            return True
        if len(path.parts) < len(parts) and all(
            fnmatch.fnmatchcase(part, pattern_part)
            for part, pattern_part in zip(path.parts, parts)
        ):
            return True
    return False


def _assert_no_symlink_parents(stage: Path, relative: Path) -> None:
    """An overlay must never follow a vendor symlink while resolving its target."""
    current = stage
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"overlay target traverses symlink parent: {relative}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"overlay target traverses non-directory parent: {relative}")


def _apply_overlay_entry(source: Path, target: Path) -> None:
    """Apply one overlay entry; existing OEM directory metadata is immutable."""
    source_stat = source.lstat()
    if stat.S_ISDIR(source_stat.st_mode):
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        existed = target.is_dir() and not target.is_symlink()
        target.mkdir(parents=True, exist_ok=True)
        if not existed:
            _copy_metadata(str(source), str(target), source_stat)
        return
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    _copy_entry(source, target, {})


def _restore_oem_directory_metadata(rootfs: Path, stage: Path) -> None:
    """Restore OEM directory metadata changed by creating overlay children."""
    for source in [rootfs, *rootfs.rglob("*")]:
        if not source.is_dir() or source.is_symlink():
            continue
        relative = source.relative_to(rootfs)
        destination = stage / relative
        if destination.is_dir() and not destination.is_symlink():
            _copy_metadata(str(source), str(destination), source.lstat())


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
    bcj: str | None = None,
    pad_to: int | None = None,
    allowlist: list[str] | None = None,
    sort_overlay_files: bool = False,
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
    allowlist = allowlist or []
    if overlays and not allowlist:
        raise ValueError("overlay builds require an explicit path allowlist")
    for overlay in overlays:
        overlay = overlay.resolve()
        if not overlay.is_dir():
            raise ValueError(f"overlay directory does not exist: {overlay}")
        for source in sorted(overlay.rglob("*")):
            relative = source.relative_to(overlay)
            reltext = relative.as_posix()
            if not _overlay_path_allowed(reltext, allowlist):
                raise ValueError(f"overlay path is not allowlisted: {reltext}")
            _assert_no_symlink_parents(stage, relative)
            target = stage / relative
            _apply_overlay_entry(source, target)
        applied.append(str(overlay))
    _restore_oem_directory_metadata(rootfs, stage)

    image = output / "rootfs.squashfs"
    if processors < 1:
        raise ValueError("processors must be positive")
    command = ["mksquashfs", str(stage), str(image), "-noappend", "-comp", "xz"]
    sort_file = None
    if sort_overlay_files:
        if not applied:
            raise ValueError("overlay sort priorities require at least one overlay")
        sort_file = output / "overlay-sort.txt"
        priority_paths = sorted(
            path.relative_to(overlay.resolve()).as_posix()
            for overlay in overlays
            for path in overlay.resolve().rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        sort_file.write_text("".join(f"{path} 100\n" for path in priority_paths))
        command.extend(["-sort", str(sort_file)])
    if bcj:
        if bcj != "arm":
            raise ValueError("only the explicitly supported BCJ filter is arm")
        command.extend(["-Xbcj", bcj])
    # Preserve source inode mtimes. -all-time would rewrite every OEM timestamp;
    # only the SquashFS superblock timestamp is normalized for repeatable builds.
    command.extend(["-no-xattrs", "-b", "1M", "-mkfs-time", "1490771239", "-no-progress", "-processors", str(processors)])
    subprocess.run(command, check=True, capture_output=True, text=True)
    validation = validate_image(image)
    padding = 0
    if pad_to is not None:
        if pad_to < image.stat().st_size:
            raise ValueError(f"pad_to {pad_to} is smaller than generated SquashFS {image.stat().st_size}")
        padding = pad_to - image.stat().st_size
        if padding:
            with image.open("ab") as stream:
                stream.write(b"\0" * padding)
            validate_image(image)
    report: dict[str, object] = {
        "rootfs_source": str(rootfs), "overlays": applied,
        "rootfs_file_count": sum(1 for p in stage.rglob("*") if p.is_file() or p.is_symlink()),
        "squashfs": str(image), "squashfs_size": image.stat().st_size,
        "squashfs_padding": padding, "bcj_filter": bcj,
        "squashfs_sha256": sha256(image), "mksquashfs_command": command,
        "unsquashfs_validation": validation,
        "original_kernel_preserved": True,
        "filesystem_profile": {"version": "4.0", "compression": "xz", "endianness": "little", "block_size": 1048576, "fragments": True, "xattrs": False, "duplicate_checking": "mksquashfs default enabled", "bcj": bcj or "none"},
        "overlay_allowlist": allowlist,
        "sort_priorities": str(sort_file) if sort_file else None,
        "timestamp_policy": "preserve source entry mtimes; normalize SquashFS superblock time only",
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
    parser.add_argument("--bcj", choices=["arm"], help="optional XZ ARM BCJ filter")
    parser.add_argument("--pad-to", type=int, help="append deterministic zero padding to this image size")
    parser.add_argument("--allow", action="append", default=[], help="allowlisted overlay relative path/glob; repeat as needed")
    parser.add_argument("--sort-overlay-files", action="store_true", help="assign deterministic mksquashfs priority 100 to additive overlay files")
    args = parser.parse_args()
    print(json.dumps(build(args.rootfs, args.overlay, args.output, args.source_squashfs, args.processors, args.bcj, args.pad_to, args.allow, args.sort_overlay_files), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
