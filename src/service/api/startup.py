from ...manitool import Manifest
from ..config import (
    MANIFEST_PATH,
    METADATA_DIR,
    STORAGE_DIR,
    config,
)


def init_storages():
    for storage in config.storages.values():
        storage_dir = STORAGE_DIR / storage.dir
        manifest_path = storage_dir / MANIFEST_PATH

        storage_dir.mkdir(parents=True, exist_ok=True)

        manifest = Manifest.from_file(manifest_path)
        manifest.scan(storage_dir, str(METADATA_DIR))
        manifest.save(manifest_path)
