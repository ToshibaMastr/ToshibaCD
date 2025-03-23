import struct
from typing import Any, Dict, List

from .base import File


def create_manifest_dict(manifest_raw: Dict):
    result = {}

    for path, hash_value in manifest_raw.items():
        current = result
        parts = path.split("/")

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = hash_value

    return result


def optimize_manifest(manifest: Dict[str, Any], path: str = "") -> Dict[str, Any]:
    result = {}

    for key, value in manifest.items():
        new_path = f"{path}/{key}" if path else key

        if isinstance(value, dict):
            while isinstance(value, dict) and len(value) == 1:
                sub_key = next(iter(value.keys()))
                sub_value = value[sub_key]

                new_path = f"{new_path}/{sub_key}"
                value = sub_value

            if isinstance(value, dict):
                optimized_subdict = optimize_manifest(value, "")
                result[new_path] = optimized_subdict
            else:
                result[new_path] = value
        else:
            result[new_path] = value

    return result


def unify_manifest_paths(d: Dict[str, Any]) -> Dict[str, Any]:
    result = {}

    for key, value in d.copy().items():
        if isinstance(value, str):
            if "/" in key:
                path, name = key.rsplit("/", 1)
                result[path] = {name: value}
            else:
                result[key] = value
        else:
            result[key] = unify_manifest_paths(value)

    return result


def process_directory(
    manifest: Dict, path: str = ".", count: int = 0, files: List[File] = []
) -> tuple[bytes, int, List[File]]:
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
            files.append(File(pathi, selfpf, int(value, 16)))

    dir_name = path.encode("ascii")
    result = struct.pack(f"<{len(dir_name) + 1}sH", dir_name, dir_count) + result

    return result, count, files


def process_files(files: List[File]) -> bytearray:
    result = bytearray()
    for file in files:
        filename = file.name.encode("ascii")
        result += struct.pack(
            f"<{len(filename) + 1}sHI", filename, file.path, file.hash
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
        name, path, hash = struct.unpack_from(f"<{name_length}sHI", data, offset)
        name = name.rstrip(b"\0").decode("ascii")
        files.append(File(name, path, hash))
        offset += struct.calcsize(f"<{name_length}sHI")

    return files, offset


def connect(paths: List[str], files: List[File]):
    manifest = {}

    for file in files:
        path = paths[file.path]
        fullparh = (path + file.name).lstrip("./")
        manifest[fullparh] = format(file.hash, "08X")

    return manifest
