from dataclasses import dataclass


@dataclass
class File:
    name: str
    hash: [int]
    path: int
