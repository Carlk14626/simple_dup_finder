"""Core duplicate-finding logic.

The strategy is deliberately two-stage: group by size first (a single stat
call per file, no I/O of file contents), then within each size group compute
hashes.  A size collision is necessary but not sufficient for a duplicate, so
filtering by size dramatically cuts the number of files whose bytes we touch.

We iterate the filesystem exactly once; only paths that survive the size
filter are opened.  Paths that raise OSError during enumeration or reading are
silently skipped — the library reports duplicates among the files it *could*
read, which is the only sound behaviour for a tool that may be pointed at a
tree containing permission-denied or vanished files.
"""

import hashlib
import os
from typing import Dict, List, Tuple


def find_duplicates_by_size(paths: List[str]) -> List[List[str]]:
    """Group files by size; return only groups with more than one file.

    Reads file metadata only — never opens the files.  Files whose size
    cannot be determined are skipped.
    """
    groups: Dict[int, List[str]] = {}
    for root_path in paths:
        if os.path.isfile(root_path):
            try:
                size = os.path.getsize(root_path)
            except OSError:
                continue
            groups.setdefault(size, []).append(root_path)
            continue
        if not os.path.isdir(root_path):
            continue
        for dirpath, _dirnames, filenames in os.walk(root_path):
            for name in filenames:
                full = os.path.join(dirpath, name)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                groups.setdefault(size, []).append(full)
    return [group for group in groups.values() if len(group) > 1]


def find_duplicates_by_hash(paths: List[str], chunk_size: int = 65536) -> List[List[str]]:
    """Group files by SHA-256; return only groups with more than one file.

    Reads file contents.  Files that cannot be opened or read are skipped.
    "chunk_size" controls how much of each file is buffered per read.
    """
    groups: Dict[str, List[str]] = {}
    for root_path in paths:
        if os.path.isfile(root_path):
            h = _hash_file(root_path, chunk_size)
            if h is not None:
                groups.setdefault(h, []).append(root_path)
            continue
        if not os.path.isdir(root_path):
            continue
        for dirpath, _dirnames, filenames in os.walk(root_path):
            for name in filenames:
                full = os.path.join(dirpath, name)
                h = _hash_file(full, chunk_size)
                if h is not None:
                    groups.setdefault(h, []).append(full)
    return [group for group in groups.values() if len(group) > 1]


def find_duplicates(paths: List[str], chunk_size: int = 65536) -> List[List[str]]:
    """Find duplicate files by size then by SHA-256, cheapest test first.

    Returns a list of groups; each group is a list of file paths whose
    contents are byte-identical.  Groups with a single member are not
    returned.
    """
    candidates = find_duplicates_by_size(paths)
    result: List[List[str]] = []
    for size_group in candidates:
        hash_groups: Dict[str, List[str]] = {}
        for file_path in size_group:
            h = _hash_file(file_path, chunk_size)
            if h is not None:
                hash_groups.setdefault(h, []).append(file_path)
        for group in hash_groups.values():
            if len(group) > 1:
                result.append(group)
    return result


def _hash_file(file_path: str, chunk_size: int) -> str:
    """Return the hex SHA-256 of a file, or None on OSError.

    Using SHA-256 rather than a faster non-cryptographic hash keeps the
    dependency surface to the stdlib only; the collision risk of SHA-256 is
    negligible for duplicate detection.
    """
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None
