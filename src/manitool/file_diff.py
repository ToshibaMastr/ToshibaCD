from dataclasses import dataclass
from enum import IntEnum


class FileChangeType(IntEnum):
    UNCHANGED = 0
    DELETED = 1
    ADDED = 2


@dataclass
class FileRef:
    file: str
    hash: str
