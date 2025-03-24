import struct
from typing import Any, BinaryIO, Dict, List

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
        if not isinstance(value, Dict):
            if "/" in key:
                path, name = key.rsplit("/", 1)
                result[path] = {name: value}
            else:
                result[key] = value
        else:
            result[key] = unify_manifest_paths(value)

    return result


def process_directory(
    stream: BinaryIO,
    manifest: Dict,
    path: str = ".",
    count: int = 0,
) -> tuple[int, List[File]]:
    selfpf = count
    count += 1

    files = []
    dir_count = 0

    for pathi, value in manifest.items():
        if isinstance(value, dict):
            dir_count += 1

    dir_name = path.encode("ascii")
    stream.write(
        struct.pack(f"<B{len(dir_name)}sH", len(dir_name), dir_name, dir_count)
    )

    for pathi, value in manifest.items():
        if isinstance(value, dict):
            count, files_ = process_directory(stream, value, pathi, count)
            files.extend(files_)
        else:
            files.append(File(pathi, selfpf, int(value, 16)))

    return count, files


def process_files(strean: BinaryIO, files: List[File]):
    for file in files:
        filename = file.name.encode("ascii")
        strean.write(
            struct.pack(
                f"<B{len(filename)}sHI", len(filename), filename, file.path, file.hash
            )
        )


def parse_directory(stream: BinaryIO, basepath: str = ""):
    paths = []

    dir_name_length = struct.unpack("<B", stream.read(1))[0]
    dir_name, dir_count = struct.unpack(
        f"<{dir_name_length}sH", stream.read(dir_name_length + 2)
    )

    dir_name = f"{basepath}{dir_name.decode('ascii')}/"
    paths.append(dir_name)

    for _ in range(dir_count):
        sub_paths = parse_directory(stream, dir_name)
        paths.extend(sub_paths)

    return paths


def parse_files(stream: BinaryIO):
    files = []

    while name_length_data := stream.read(1):
        name_length = struct.unpack("<B", name_length_data)[0]
        name, path, hash = struct.unpack(
            f"<{name_length}sHI", stream.read(name_length + 6)
        )

        name = name.decode("ascii")
        files.append(File(name, path, hash))

    return files


def connect(paths: List[str], files: List[File]):
    manifest = {}

    for file in files:
        path = paths[file.path]
        fullpath = (path + file.name).lstrip("./")
        manifest[fullpath] = format(file.hash, "08X")

    return manifest
