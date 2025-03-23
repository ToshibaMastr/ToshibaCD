import zipfile
from pathlib import Path
from typing import List, Optional

from .file_diff import FileChangeType, FileRef
from .manifest import Manifest


class ManifestDiff:
    def __init__(
        self,
        added: Optional[List[FileRef]] = None,
        deleted: Optional[List[FileRef]] = None,
        unchanged: Optional[List[FileRef]] = None,
    ):
        self.added = added or []
        self.deleted = deleted or []
        self.unchanged = unchanged or []

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.deleted)

    @classmethod
    def create(cls, a: Manifest, b: Manifest) -> "ManifestDiff":
        added = []
        deleted = []
        unchanged = []

        a_copy = a.data.copy()
        b_copy = b.data.copy()

        for file, hash_value in a_copy.items():
            other_hash = b_copy.pop(file, None)
            if other_hash is None:
                added.append(FileRef(file, hash_value))
            elif other_hash == hash_value:
                unchanged.append(FileRef(file, hash_value))

        for file, hash_value in b_copy.items():
            deleted.append(FileRef(file, hash_value))

        return cls(added, deleted, unchanged)

    def apply_to(self, manifest: Manifest):
        for diff in self.added:
            manifest.data[str(diff.file)] = diff.hash

        for diff in self.deleted:
            manifest.data.pop(str(diff.file), None)

    def to_zip(self, stream, directory: Path):
        def process_file(zipf, diff, change_type, content=None):
            filepath = str(diff.file)
            if content is None:
                file_path = directory / diff.file
                zipf.write(file_path, arcname=filepath)
            else:
                zipf.writestr(filepath, content)

            zinfo = zipf.getinfo(filepath)
            zinfo.internal_attr = change_type

        with zipfile.ZipFile(
            stream,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as zipf:
            for diff in self.added:
                process_file(zipf, diff, FileChangeType.ADDED)

            for diff in self.deleted:
                process_file(zipf, diff, FileChangeType.DELETED, "оборачивайся...")

    @classmethod
    def from_zip(cls, stream, directory: Path):
        added = []
        deleted = []
        unchanged = []

        with zipfile.ZipFile(stream, "r") as zip_ref:
            for info in zip_ref.infolist():
                file_path = directory / info.filename
                file_content = zip_ref.read(info.filename)
                hash = format(info.CRC, "08X")

                if info.internal_attr == FileChangeType.ADDED:
                    added.append(FileRef(info.filename, hash))
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(file_content)

                elif info.internal_attr == FileChangeType.DELETED:
                    deleted.append(FileRef(info.filename, hash))
                    file_path.unlink(missing_ok=True)

                else:
                    unchanged.append(FileRef(info.filename, hash))

        return cls(added, deleted, unchanged)
