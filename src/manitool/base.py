from dataclasses import dataclass
from typing import Optional


@dataclass
class File:
    name: str
    path: int
    hash: Optional[int]
