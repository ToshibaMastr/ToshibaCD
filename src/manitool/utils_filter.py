import struct
from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class FileFilter:
    name: str
    path: int
    hash: Set[int]


def process_directory(
    manifest: Dict, path: str = ".", count: int = 0, files: List[FileFilter] = []
) -> tuple[bytes, int, List[FileFilter]]:
    selfpf = count
    count += 1

    result = bytearray()
    dir_count = 0

    for pathi, value in manifest.items():
        if isinstance(value, dict):
            dir_result, count, files = process_directory(value, pathi, count, files)
            result += dir_result
            dir_count += 1
        else:
            files.append(FileFilter(pathi, selfpf, {int(hash, 16) for hash in value}))

    dir_name = path.encode("ascii")
    result = struct.pack(f"<{len(dir_name) + 1}sH", dir_name, dir_count) + result

    return result, count, files


def process_files(files: List[FileFilter]) -> bytearray:
    result = bytearray()
    for file in files:
        filename = file.name.encode("ascii")
        hash_count = len(file.hash)
        result += struct.pack(
            f"<{len(filename) + 1}sHB{hash_count}I",
            filename,
            file.path,
            hash_count,
            *file.hash,
        )

    return result


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
        name, path, hash_count = struct.unpack_from(f"<{name_length}sHB", data, offset)
        offset += struct.calcsize(f"<{name_length}sHB")
        name = name.rstrip(b"\0").decode("ascii")

        hashes = set(struct.unpack_from(f"<{hash_count}I", data, offset))
        offset += struct.calcsize(f"<{hash_count}I")

        files.append(FileFilter(name, path, hashes))

    return files, offset


def connect(paths: List[str], files: List[FileFilter]):
    manifest = {}

    for file in files:
        path = paths[file.path]
        fullparh = (path + file.name).lstrip("./")
        manifest[fullparh] = {format(hash, "08X") for hash in file.hash}

    return manifest
