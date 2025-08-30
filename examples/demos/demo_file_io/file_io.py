"""
Utility functions for simple file I/O, JSON, and CSV operations.

This module provides:
- write_file, append_to_file, read_file
- count_lines
- write_json, read_json
- write_csv, read_csv

All functions aim to be small, predictable, and cross-platform friendly.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

__all__ = [
    "write_file",
    "append_to_file",
    "read_file",
    "count_lines",
    "write_json",
    "read_json",
    "write_csv",
    "read_csv",
]


def _ensure_parent_dir(path: str) -> None:
    """
    Ensure the parent directory for 'path' exists.
    Safe to call for paths in the current directory as well.
    """
    # Use abspath to avoid empty dirname when the file is in the CWD.
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def write_file(filename: str, content: Union[str, bytes]) -> None:
    """
    Write 'content' to 'filename', overwriting any existing file.

    - Creates parent directories if they do not exist.
    - Supports both str and bytes content. Bytes are written in binary mode.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    _ensure_parent_dir(filename)

    if isinstance(content, bytes):
        # Binary write
        with open(filename, "wb") as f:
            f.write(content)
    else:
        # Text write
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(content))


def append_to_file(filename: str, content: Union[str, bytes]) -> None:
    """
    Append 'content' to 'filename'.

    - Creates the file and parent directories if they do not exist.
    - Supports both str and bytes content. Bytes are appended in binary mode.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    _ensure_parent_dir(filename)

    if isinstance(content, bytes):
        with open(filename, "ab") as f:
            f.write(content)
    else:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(str(content))


def read_file(filename: str) -> str:
    """
    Read and return the entire content of 'filename' as a string (utf-8).
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def count_lines(filename: str) -> int:
    """
    Count the number of lines in 'filename'.

    Uses an efficient streaming approach and returns the number of lines
    regardless of whether the file ends with a trailing newline.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    count = 0
    with open(filename, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def write_json(
    filename: str, data: Any, *, indent: int = 2, sort_keys: bool = False
) -> None:
    """
    Write JSON data to 'filename' using pretty formatting.

    - Ensures the JSON spans multiple lines via 'indent' (default 2).
    - 'sort_keys' can be used to sort dictionary keys for deterministic output.
    - Uses UTF-8 encoding with ensure_ascii=False to preserve unicode characters.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    _ensure_parent_dir(filename)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        # Add a trailing newline for POSIX-friendly files.
        f.write("\n")


def read_json(filename: str) -> Any:
    """
    Read and parse JSON from 'filename' (utf-8) and return the resulting object.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def _collect_fieldnames_from_rows(
    rows: Iterable[Mapping[str, Any]],
    explicit_fieldnames: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Determine fieldnames for CSV writing.

    - If explicit_fieldnames are provided, they are used as-is.
    - Otherwise, fieldnames are collected in insertion order from the rows.
    """
    if explicit_fieldnames is not None:
        return list(explicit_fieldnames)

    ordered: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def write_csv(
    filename: str,
    rows: Union[Iterable[Mapping[str, Any]], Iterable[Sequence[Any]]],
    fieldnames: Optional[Sequence[str]] = None,
) -> None:
    """
    Write CSV data to 'filename'.

    Supports two inputs:
    - Iterable of mappings (list of dicts): writes a header row using keys.
    - Iterable of sequences (e.g., list of lists/tuples): requires 'fieldnames' for header.

    Notes:
    - Uses newline='' per csv module recommendations for universal newlines handling.
    - Values are converted to strings for consistent CSV serialization.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    # Peek the first item to determine the type without exhausting the iterator
    iterable = iter(rows)
    try:
        first = next(iterable)
    except StopIteration:
        # No rows; still write header if provided
        _ensure_parent_dir(filename)
        if fieldnames is None:
            # Create an empty file
            with open(filename, "w", newline="", encoding="utf-8") as _:
                pass
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
            writer.writeheader()
        return

    # Rebuild iterator with the first element included
    def _chain_first_and_rest():
        yield first
        for item in iterable:
            yield item

    rows_iter = _chain_first_and_rest()

    # Branch based on type of first row
    if isinstance(first, Mapping):
        # Collect fieldnames from all rows if not provided
        materialized_rows: List[Mapping[str, Any]] = list(rows_iter)
        fns = _collect_fieldnames_from_rows(materialized_rows, fieldnames)
        _ensure_parent_dir(filename)
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fns, extrasaction="ignore")
            writer.writeheader()
            for row in materialized_rows:
                # Convert all values to strings for CSV
                writer.writerow(
                    {k: "" if row.get(k) is None else str(row.get(k)) for k in fns}
                )
    else:
        # Sequence rows: require explicit fieldnames
        if fieldnames is None:
            raise ValueError(
                "fieldnames must be provided when writing sequence rows to CSV"
            )
        _ensure_parent_dir(filename)
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(list(fieldnames))
            for seq in rows_iter:
                writer.writerow([("" if v is None else str(v)) for v in seq])


def read_csv(filename: str) -> List[Dict[str, str]]:
    """
    Read CSV from 'filename' and return a list of dictionaries keyed by header names.

    - All values are returned as strings to match typical CSV semantics.
    - If the CSV is empty (no rows), returns an empty list.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    with open(filename, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return []
        return [dict(row) for row in reader]
