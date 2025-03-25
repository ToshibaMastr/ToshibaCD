import os
from pathlib import Path

from dotenv import load_dotenv

from .models import Config

load_dotenv()

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/app/config.yaml"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/storage/"))
METADATA_DIR = Path(".tcd/")

MANIFEST_PATH = METADATA_DIR / "manifest"


config = Config(CONFIG_PATH)

__all__ = [
    "config",
    "CONFIG_PATH",
    "STORAGE_DIR",
    "METADATA_DIR",
    "MANIFEST_PATH",
]
