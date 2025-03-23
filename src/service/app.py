import io
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response

from ..manitool import Manifest, ManifestDiff
from .api.models import StorageStatus, UploadResponse
from .api.utils import get_storage_dir
from .core.config import BASE_STORAGE_DIR, MANIFEST_FILE_PATH

app = FastAPI(
    title="Toshiba Content Delivery",
    description="Modern content delivery and synchronization",
    version="1.0.2",
    contact={"name": "Toshiba Mastru", "email": "ggostem42@gmail.com"},
)


@app.get("/{storage}/manifest")
async def get_manifest_file(storage: Path = Depends(get_storage_dir)):
    manifest_path = BASE_STORAGE_DIR / storage / MANIFEST_FILE_PATH

    if not manifest_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(manifest_path, filename="manifest")


@app.post("/{storage}/upload")
async def upload_archive(
    archive: UploadFile = File(..., description="Content archive"),
    storage: Path = Depends(get_storage_dir),
):
    content = await archive.read()

    storage_dir = BASE_STORAGE_DIR / storage
    manifest_path = storage_dir / MANIFEST_FILE_PATH

    manifest = Manifest.from_file(manifest_path)

    mdiff = ManifestDiff.from_zip(io.BytesIO(content), storage_dir)
    mdiff.apply_to(manifest)

    manifest.save_file(manifest_path)

    return UploadResponse(
        status=StorageStatus.SUCCESS,
        message="Archive uploaded and processed successfully",
    )


@app.post("/{storage}/download")
async def download_archive(
    manifest: UploadFile = File(None, description="Manifest file"),
    storage: Path = Depends(get_storage_dir),
):
    storage_dir = BASE_STORAGE_DIR / storage
    manifest_path = storage_dir / MANIFEST_FILE_PATH

    if not manifest_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if manifest:
        content = await manifest.read()
        client_manifest = Manifest.from_bytes(content)
    else:
        client_manifest = Manifest()

    server_manifest = Manifest.from_file(manifest_path)
    mdiff = ManifestDiff.create(server_manifest, client_manifest)

    if not mdiff.has_changes:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        mdiff.to_zip(tmp_file, storage_dir)

    return FileResponse(tmp_file.name, media_type="application/zip")
