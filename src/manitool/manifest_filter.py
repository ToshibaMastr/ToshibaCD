from pathlib import Path
from typing import Any, Dict, Optional

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


class ManifestFilter:
    def __init__(self, manifest: Optional[Dict] = None):
        self.data: Dict[str, Any] = manifest or {}

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

    def process_directory(
        self, current: Path, ignore: str = "", base: Optional[Path] = None
    ):
        if base is None:
            base = current

        for file_path in current.iterdir():
            if ignore == str(file_path.name):
                continue

            if file_path.is_file():
                filepath = str(file_path.relative_to(base))
                self.data[filepath] = self.data.get(filepath, None)

            elif file_path.is_dir():
                self.process_directory(file_path, ignore, base)
