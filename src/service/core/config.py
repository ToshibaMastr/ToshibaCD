from pathlib import Path

from dotenv import load_dotenv

# import logging
# import sys
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     handlers=[logging.StreamHandler(sys.stdout)],
# )
# malogger = logging.getLogger(__name__)
# logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

load_dotenv()


BASE_STORAGE_DIR = Path("storage/")
BASENAME = Path(".tcd/")
MANIFEST_FILE_PATH = BASENAME / "manifest"
