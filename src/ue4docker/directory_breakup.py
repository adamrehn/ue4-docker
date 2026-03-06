#!/usr/bin/env python3
import argparse
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple


def bytes_to_human(n: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if n < 1024 or unit == "TiB":
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TiB"


@dataclass
class GroupItem:
    kind: str  # "dir" or "files"
    rel_path: Path
    size: int
    files: Optional[List[Tuple[Path, int]]] = None  # only for kind == "files"


def analyze_directories(root: Path) -> Tuple[Dict[Path, int], Dict[Path, List[Tuple[Path, int]]]]:
    """Return (total_sizes, direct_file_lists) for each directory under root."""

    total_sizes: Dict[Path, int] = {}
    direct_files: Dict[Path, List[Tuple[Path, int]]] = {}

    def walk(path: Path) -> int:
        entries = sorted(path.iterdir())
        files_list: List[Tuple[Path, int]] = []
        files_size = 0
        subdirs_total = 0

        for entry in entries:
            if entry.is_file():
                size = entry.stat().st_size
                files_size += size
                files_list.append((entry.relative_to(root), size))

        for entry in entries:
            if entry.is_dir():
                subdirs_total += walk(entry)

        total = files_size + subdirs_total
        total_sizes[path] = total
        direct_files[path] = files_list
        return total

    walk(root)
    return total_sizes, direct_files


def breadth_first_groups(
    root: Path,
    total_sizes: Dict[Path, int],
    direct_files: Dict[Path, List[Tuple[Path, int]]],
    hard_limit: int,
) -> List[GroupItem]:
    """Produce BFS-ordered groups for directory moves and file bundles."""

    groups: List[GroupItem] = []
    queue: Deque[Path] = deque([root])

    while queue:
        current = queue.popleft()
        rel_current = Path(".") if current == root else current.relative_to(root)

        files_list = direct_files[current]
        files_size = sum(size for _path, size in files_list)
        if files_size:
            groups.append(GroupItem("files", rel_current, files_size, files_list))

        for child in sorted(current.iterdir()):
            if child.is_dir():
                child_size = total_sizes[child]
                if child_size <= hard_limit:
                    groups.append(
                        GroupItem("dir", child.relative_to(root), child_size)
                    )
                else:
                    # Directory too large to move as a whole, so traverse inside
                    queue.append(child)

    return groups


def split_file_group(group: GroupItem, hard_limit: int) -> List[GroupItem]:
    """Split a file group into chunks that respect the hard limit."""

    assert group.files is not None
    chunks: List[GroupItem] = []
    current_files: List[Tuple[Path, int]] = []
    current_size = 0

    for rel_file, size in group.files:
        if size > hard_limit:
            raise RuntimeError(
                f"File '{rel_file}' exceeds the hard limit ({bytes_to_human(size)} > {bytes_to_human(hard_limit)})."
            )

        if current_files and current_size + size > hard_limit:
            chunks.append(GroupItem("files", group.rel_path, current_size, current_files))
            current_files = []
            current_size = 0

        current_files.append((rel_file, size))
        current_size += size

    if current_files:
        chunks.append(GroupItem("files", group.rel_path, current_size, current_files))

    return chunks


def pack_groups(groups: List[GroupItem], soft_limit: int, hard_limit: int) -> List[List[GroupItem]]:
    packs: List[List[GroupItem]] = []
    current_pack: List[GroupItem] = []
    current_size = 0

    def flush_pack() -> None:
        nonlocal current_pack, current_size
        if current_pack:
            packs.append(current_pack)
            current_pack = []
            current_size = 0

    def add_group(item: GroupItem) -> None:
        nonlocal current_pack, current_size

        if current_pack and current_size + item.size > hard_limit:
            flush_pack()

        current_pack.append(item)
        current_size += item.size

        if current_size >= soft_limit:
            flush_pack()

    for group in groups:
        if group.size <= hard_limit or group.kind == "dir":
            if group.size > hard_limit:
                raise RuntimeError(
                    f"Group '{group.rel_path}' ({group.kind}) exceeds the hard limit ({bytes_to_human(group.size)} > {bytes_to_human(hard_limit)})."
                )
            add_group(group)
        else:
            # group.kind == "files" and size > hard limit -> split into chunks
            for chunk in split_file_group(group, hard_limit):
                add_group(chunk)

    flush_pack()

    return packs


def describe_packs(packs: List[List[GroupItem]]) -> List[str]:
    lines: List[str] = []
    for idx, pack in enumerate(packs, start=1):
        pack_size = sum(item.size for item in pack)
        lines.append(f"Pack {idx:03d}: {bytes_to_human(pack_size)}")
        for item in pack:
            lines.append(
                f"    - {item.kind:5s} {item.rel_path} ({bytes_to_human(item.size)})"
            )
    return lines


def create_output(root: Path, output_root: Path, packs: List[List[GroupItem]], dry_run: bool) -> List[str]:
    """Move grouped directories/files into numbered pack directories."""

    import shutil

    if dry_run:
        print("Dry run mode: no filesystem changes will be made.")
        for line in describe_packs(packs):
            print(line)
        return []

    created_dirs: List[str] = []

    for idx, pack in enumerate(packs, start=1):
        part_dir = output_root / f"{idx:03d}"
        part_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(f"{idx:03d}")

        for group in pack:
            if group.kind == "dir":
                src = root / group.rel_path
                dst = part_dir / group.rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            else:  # files bundle
                assert group.files is not None
                for rel_file, _size in group.files:
                    src_file = root / rel_file
                    dst_file = part_dir / rel_file
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src_file), str(dst_file))

    return created_dirs
def parse_size(s: str) -> int:
    """
    Parse human-friendly size like '10G', '500M', '100K', or plain bytes.
    """
    s = s.strip().lower()
    if s.endswith("k"):
        return int(float(s[:-1]) * 1024)
    if s.endswith("m"):
        return int(float(s[:-1]) * 1024**2)
    if s.endswith("g"):
        return int(float(s[:-1]) * 1024**3)
    return int(s)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Split a directory into numbered parts (001, 002, ...) "
            "based on total file size, with soft and hard per-part limits."
        )
    )
    parser.add_argument("source", type=Path, help="Source directory to split")
    parser.add_argument(
        "output",
        type=Path,
        help="Output directory under which 001, 002, ... will be created",
    )
    parser.add_argument(
        "--soft-limit",
        required=True,
        help="Preferred maximum size per part (e.g. 50G, 500M)",
    )
    parser.add_argument(
        "--hard-limit",
        required=True,
        help="Absolute maximum size per part (e.g. 60G, 600M)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print pack sizes and contents without moving anything",
    )

    args = parser.parse_args()
    root = args.source.resolve()
    output_root = args.output.resolve()
    soft_limit = parse_size(args.soft_limit)
    hard_limit = parse_size(args.hard_limit)

    if not root.is_dir():
        raise SystemExit(f"Source '{root}' is not a directory")

    if hard_limit < soft_limit:
        raise SystemExit("hard-limit must be >= soft-limit")

    total_sizes, direct_files = analyze_directories(root)
    total_size = total_sizes[root]
    print(f"Total size: {bytes_to_human(total_size)}")
    print(
        f"Soft limit: {bytes_to_human(soft_limit)}, "
        f"Hard limit: {bytes_to_human(hard_limit)}"
    )

    groups = breadth_first_groups(root, total_sizes, direct_files, hard_limit)
    packs = pack_groups(groups, soft_limit, hard_limit)
    print(f"Creating {len(packs)} part(s) under {output_root}")
    create_output(root, output_root, packs, args.dry_run)


if __name__ == "__main__":
    main()