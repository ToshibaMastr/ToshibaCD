from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Set

import zstandard as zstd

from .manifest import Manifest
from .utils import (
    create_manifest_dict,
    optimize_manifest,
    unify_manifest_paths,
)
from .utils_filter import (
    connect,
    parse_directory,
    parse_files,
    process_directory,
    process_files,
)


class ManifestFilter:
    def __init__(self, manifest: Optional[Dict] = None):
        self.data: Dict[str, Set] = defaultdict(set)
        if manifest:
            self.data |= manifest

    def update(self, manifest: Manifest):
        for path, hash in manifest.data.items():
            self.data[path].add(hash)

    def filter(self, manifest: Manifest):
        paths_to_remove = []

        for path, hash_value in manifest.data.items():
            if not (path in self.data and hash_value in self.data[path]):
                paths_to_remove.append(path)

        for path in paths_to_remove:
            manifest.data.pop(path)

    @classmethod
    def from_file(cls, file: Path) -> "ManifestFilter":
        if file.is_file():
            return cls.from_bytes(file.read_bytes())
        return cls()

    @classmethod
    def from_bytes(cls, data: bytes) -> "ManifestFilter":
        if not data.startswith(b"TCD\2"):
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

        out = b"TCD\2" + zstd.compress(payload, level=compress_level)

        return out
