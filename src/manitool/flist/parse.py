import struct
from pathlib import Path
from typing import Any, Dict, List

import zstandard as zstd

from .base import File


def parse(data: bytes) -> Dict[str, Any]:
    if not data.startswith(b"TCD\0"):
        raise ValueError("Invalid data format")

    decompressed_data = zstd.decompress(data[4:])
    paths, offset = parse_directory(decompressed_data)
    files, offset = parse_files(decompressed_data, offset)

    manifest = connect(paths, files)

    return manifest


def parse_directory(data: bytes, offset: int = 0, basepath: str = ""):
    paths = []

    dir_name_length = data[offset:].index(0) + 1
    dir_name, dir_count = struct.unpack_from(f"<{dir_name_length}sH", data, offset)
    dir_name = f"{basepath}{dir_name.rstrip(b'\0').decode('ascii')}/"
    offset += struct.calcsize(f"<{dir_name_length}sH")
    paths.append(dir_name)

    for _ in range(dir_count):
        sub_paths, offset = parse_directory(data, offset, dir_name)
        paths += sub_paths

    return paths, offset


def parse_files(data: bytes, offset: int = 0):
    files = []

    while offset < len(data):
        name_length = data[offset:].index(0) + 1
        name, path, hash = struct.unpack_from(f"<{name_length}sHI", data, offset)
        name = name.rstrip(b"\0").decode("ascii")
        files.append(File(name, format(hash, "08X"), path))
        offset += struct.calcsize(f"<{name_length}sHI")

    return files, offset


def connect(paths: List[Path], files: List[File]):
    manifest = {}

    for file in files:
        path = paths[file.path]
        fullparh = (path + file.name).lstrip("./")
        manifest[fullparh] = file.hash

    return manifest
