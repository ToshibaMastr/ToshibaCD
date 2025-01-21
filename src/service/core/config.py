import os
from dataclasses import dataclass

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


@dataclass
class BaseConfig:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/data"
    DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
        "postgresql", "postgresql+asyncpg"
    )


config = BaseConfig()
