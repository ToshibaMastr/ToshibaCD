from pathlib import Path

from fastapi import HTTPException, status


async def get_storage_dir(storage: str) -> Path:
    if not storage or storage in {"..", "."} or "/" in storage or "\\" in storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage identifier"
        )

    return Path(storage)
