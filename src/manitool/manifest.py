from pathlib import Path
from typing import Any, Dict

import zstandard as zstd

from .utils import (
    connect,
    create_manifest_dict,
    optimize_manifest,
    parse_directory,
    parse_files,
    process_directory,
    process_files,
    unify_manifest_paths,
)


class Manifest:
    def __init__(self, manifest: Dict = {}):
        self.data: Dict[str, Any] = manifest

    @classmethod
    def from_file(cls, file: Path) -> "Manifest":
        if file.is_file():
            return cls.from_bytes(file.read_bytes())
        return cls()

    @classmethod
    def from_bytes(cls, data: bytes) -> "Manifest":
        if not data.startswith(b"TCD\0"):
            raise ValueError("Invalid data format")

        decompressed_data = zstd.decompress(data[4:])
        paths, offset = parse_directory(decompressed_data)
        files, _ = parse_files(decompressed_data, offset)

        return cls(connect(paths, files))

    def save_file(self, file: Path):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(self.dumps())

    def dumps(self, compress_level: int = 22):
        data = create_manifest_dict(self.data)
        data = optimize_manifest(data)
        data = unify_manifest_paths(data)

        directory_data, _, files = process_directory(data, files=[])
        payload = directory_data + process_files(files)

        out = b"TCD\0" + zstd.compress(payload, level=compress_level)

        return out
