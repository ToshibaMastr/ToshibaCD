from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Group:
    name: str
    permissions: List[str] = field(default_factory=list)
    api_key: Optional[str] = None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass
class Storage:
    path: str
    name: str
    dir: Path
    permissions: Dict[str, List[str]] = field(default_factory=dict)

    def get_group_permissions(self, group: Group) -> List[str]:
        return self.permissions.get(group.name, group.permissions)

    def check_group_permission(self, group: Group, permission: str) -> bool:
        return permission in self.get_group_permissions(group)


class Config:
    def __init__(self, config: Path):
        config_data = yaml.safe_load(config.read_text())

        self.groups: Dict[str, Group] = {}
        for name, info in config_data.get("groups", {}).items():
            self.groups[name] = Group(
                name,
                info.get("permissions", []),
                info.get("apikey"),
            )

        self.storages: Dict[str, Storage] = {}
        for path, info in config_data.get("storages", {}).items():
            self.storages[path] = Storage(
                path,
                info.get("name", path),
                info.get("directory", path),
                info.get("permissions", {}),
            )

    def get_group(self, group: str) -> Optional[Group]:
        return self.groups.get(group)

    def get_group_by_api_key(self, api_key: str) -> Optional[Group]:
        for path, group in self.groups.items():
            if group.api_key == api_key:
                return group

        return self.groups.get("public", None)

    def get_storage(self, storage: str) -> Optional[Storage]:
        return self.storages.get(storage)
