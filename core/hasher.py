"""
core/hasher.py
SHA-256 hashing logic for files and directories.
"""

import hashlib
import os
from pathlib import Path


HASH_ALGORITHM = "sha256"
CHUNK_SIZE = 65536  # 64 KB chunks for large file support


def hash_file(filepath: str) -> str | None:
    """
    Compute SHA-256 hash of a single file.
    Returns hex digest string, or None if file is unreadable.
    """
    h = hashlib.new(HASH_ALGORITHM)
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError) as e:
        print(f"[hasher] Cannot read {filepath}: {e}")
        return None


def hash_directory(directory: str) -> dict[str, str]:
    """
    Walk a directory and return a dict of {relative_path: sha256_hash}.
    Skips files that cannot be read.
    """
    results = {}
    root = Path(directory)

    for filepath in root.rglob("*"):
        if filepath.is_file():
            rel = str(filepath.relative_to(root))
            digest = hash_file(str(filepath))
            if digest is not None:
                results[rel] = digest

    return results


def verify_file(filepath: str, expected_hash: str) -> bool:
    """
    Return True if the file's current hash matches the expected hash.
    """
    current = hash_file(filepath)
    if current is None:
        return False
    return current == expected_hash