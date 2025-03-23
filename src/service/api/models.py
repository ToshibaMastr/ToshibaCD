from enum import Enum

from pydantic import BaseModel, Field


class StorageStatus(str, Enum):
    SUCCESS = "success"
    UNCHANGED = "unchanged"
    ERROR = "error"


class ManifestResponse(BaseModel):
    status: StorageStatus = Field(default=StorageStatus.SUCCESS)
    message: str = Field(default="Manifest retrieved successfully")


class UploadResponse(BaseModel):
    status: StorageStatus = Field(default=StorageStatus.SUCCESS)
    message: str = Field(default="Archive uploaded successfully")
