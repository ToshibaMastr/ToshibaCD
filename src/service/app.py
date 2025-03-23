import io
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from ..manitool import Manifest, ManifestDiff

app = FastAPI(
    title="Toshiba Content Delivery",
    description="Modern content delivery and synchronization",
    version="2.0.0",
    contact={"name": "Toshiba Mastru", "email": "ggostem42@gmail.com"},
)

BASE_STORAGE_DIR = Path("storage/")
MANIFEST_FILE_PATH = Path(".tcd/manifest")


async def get_storage_dir(storage: str) -> Path:
    if not storage or storage in {"..", "."} or "/" in storage or "\\" in storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage identifier"
        )

    storage_dir = BASE_STORAGE_DIR / storage
    return storage_dir


@app.get("/{storage}/manifest")
async def get_manifest_file(storage: Path = Depends(get_storage_dir)):
    manifest_path = BASE_STORAGE_DIR / storage / MANIFEST_FILE_PATH

    if not manifest_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manifest file not found",
        )

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

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"status": "success", "message": "Archive uploaded successfully"},
    )


@app.post("/{storage}/download")
async def download_archive(storage: str, request: Request):
    client_manifest = Manifest(await request.json())

    storage_dir = BASE_STORAGE_DIR / storage
    manifest_path = storage_dir / MANIFEST_FILE_PATH

    if not manifest_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    server_manifest = Manifest.from_file(manifest_path)
    mdiff = ManifestDiff.create(server_manifest, client_manifest)

    if not mdiff.has_changes:
        return {"status": "unchanged"}

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        mdiff.to_zip(tmp_file, storage_dir)

    return FileResponse(tmp_file.name, media_type="application/zip")
