import io
import tempfile

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response

from ..manitool import Manifest, ManifestDiff
from .api.models import StorageStatus, UploadResponse
from .api.startup import init_storages
from .api.utils import get_group, get_storage, permission_check
from .config import MANIFEST_PATH, STORAGE_DIR
from .config.models import Group, Storage

app = FastAPI(
    title="Toshiba Content Delivery",
    description="Modern content delivery and synchronization",
    version="1.0.2",
    contact={"name": "Toshiba Mastru", "email": "ggostem42@gmail.com"},
)


@app.on_event("startup")
async def startup_event():
    init_storages()


@app.get("/{storage}/manifest")
async def get_manifest_file(
    storage: Storage = Depends(get_storage),
    group: Group = Depends(get_group),
):
    await permission_check(storage, group, ["read"])

    manifest_path = STORAGE_DIR / storage.dir / MANIFEST_PATH

    if not manifest_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(manifest_path, filename="manifest")


@app.post("/{storage}/upload")
async def upload_archive(
    archive: UploadFile = File(..., description="Content archive"),
    storage: Storage = Depends(get_storage),
    group: Group = Depends(get_group),
):
    await permission_check(storage, group, ["write"])

    content = await archive.read()

    storage_dir = STORAGE_DIR / storage.dir
    manifest_path = storage_dir / MANIFEST_PATH

    manifest = Manifest.from_file(manifest_path)

    mdiff = ManifestDiff.from_zip(io.BytesIO(content), storage_dir)
    mdiff.apply_to(manifest)

    manifest.save(manifest_path)

    return UploadResponse(
        status=StorageStatus.SUCCESS,
        message="Archive uploaded and processed successfully",
    )


@app.post("/{storage}/download")
async def download_archive(
    manifest: UploadFile = File(None, description="Manifest file"),
    storage: Storage = Depends(get_storage),
    group: Group = Depends(get_group),
):
    await permission_check(storage, group, ["read"])

    storage_dir = STORAGE_DIR / storage.dir
    manifest_path = storage_dir / MANIFEST_PATH

    if not manifest_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if manifest:
        client_manifest = Manifest.from_bytes(manifest.file)
    else:
        client_manifest = Manifest()

    server_manifest = Manifest.from_file(manifest_path)
    mdiff = ManifestDiff.create(server_manifest, client_manifest)

    if not mdiff.has_changes:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        mdiff.to_zip(tmp_file, storage_dir)

    return FileResponse(tmp_file.name, media_type="application/zip")
