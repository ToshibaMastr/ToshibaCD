from io import BufferedReader, IOBase
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional
from zlib import crc32

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


def get_crc(path: Path, chunk_size=8196):
    crc = 0
    with open(path, "rb") as file:
        while chunk := file.read(chunk_size):
            crc = crc32(chunk, crc)
    return format(crc, "08X")


class Manifest:
    def __init__(self, manifest: Optional[Dict] = None):
        self.data: Dict[str, Any] = manifest or {}

    @classmethod
    def from_file(cls, path: Path) -> "Manifest":
        if not path.is_file():
            return cls()

        with path.open("rb") as f:
            return cls.from_bytes(f)

    @classmethod
    def from_bytes(cls, stream: BufferedReader | IOBase | BinaryIO) -> "Manifest":
        if stream.read(4) != b"TCD\1":
            raise ValueError("Invalid data format")

        dctx = zstd.ZstdDecompressor()
        reader = dctx.stream_reader(stream)

        paths = parse_directory(reader)
        files = parse_files(reader)

        return cls(connect(paths, files))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            self.write(f)

    def write(self, stream: BinaryIO, compress_level: int = 22):
        data = create_manifest_dict(self.data)
        data = optimize_manifest(data)
        data = unify_manifest_paths(data)

        stream.write(b"TCD\1")
        compressor = zstd.ZstdCompressor()
        with compressor.stream_writer(stream, closefd=False) as cstream:
            _, files = process_directory(cstream, data)
            process_files(cstream, files)

    def scan(self, current: Path, ignore: str = "", base: Optional[Path] = None):
        if base is None:
            base = current

        for file_path in current.iterdir():
            if ignore == str(file_path.name):
                continue

            if file_path.is_file():
                filepath = str(file_path.relative_to(base))
                self.data[filepath] = get_crc(file_path)

            elif file_path.is_dir():
                self.scan(file_path, ignore, base)
