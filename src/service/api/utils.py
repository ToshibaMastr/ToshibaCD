from typing import List, Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param

from ..config import config
from ..config.models import Group, Storage

api_key_header = APIKeyHeader(name="Authorization", scheme_name="API key")


async def get_group(
    request: Request,
    api_key_header: Optional[str] = Security(api_key_header),
) -> Group:
    scheme, credential = get_authorization_scheme_param(api_key_header)
    if scheme == "Key":
        if group := config.get_group_by_api_key(credential):
            return group
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Key"},
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing API Key",
        headers={"WWW-Authenticate": "Key"},
    )


async def get_storage(storage: str) -> Storage:
    if not storage or storage in {"..", "."} or "/" in storage or "\\" in storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage identifier"
        )

    if storagec := config.get_storage(storage):
        return storagec

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found"
    )


async def permission_check(storage: Storage, group: Group, permissions: List[str]):
    group_permissions = storage.get_group_permissions(group)
    missing_permissions = [pm for pm in permissions if pm not in group_permissions]

    if missing_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permissions: {', '.join(missing_permissions)}",
            headers={"WWW-Authenticate": "Key"},
        )
