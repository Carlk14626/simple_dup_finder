# simple_dup_finder

Finds duplicate files by grouping on file size first, then by SHA-256, so the
cheapest test runs before any file is ever opened.

## Usage

```python
import simple_dup_finder

groups = simple_dup_finder.find_duplicates(["./some_dir", "./a_file.txt"])
for group in groups:
    print(group)
```

Three functions are exported:

- `find_duplicates(paths, chunk_size=65536)` — full two-stage search; returns a list of groups (each a list of paths) whose contents are byte-identical.
- `find_duplicates_by_size(paths)` — stage one only; groups files by size, returning groups of two or more.
- `find_duplicates_by_hash(paths, chunk_size=65536)` — stage two only; groups files by SHA-256, returning groups of two or more.

## Why

The problem is finding duplicates across large trees without reading every
byte up front. Size is a free filter (a stat call), so it is applied first.
Only files sharing a size with at least one other file are then hashed. The
trade-off is correctness over speed: SHA-256 is used (rather than a faster
non-cryptographic hash) so the library stays stdlib-only and collision risk is
negligible.

## Edge cases

Files that raise `OSError` during stat, open, or read are silently skipped.
The library reports duplicates among the files it could read, which is the
only sound behaviour for a tree that may contain permission-denied or
otherwise-inaccessible files. Empty files are treated as duplicates of one
another.

Run the tests with:

```
PYTHONPATH=src python -m unittest discover -s tests
```
