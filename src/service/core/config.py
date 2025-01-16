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

{"ru": {"title": "HiTech", "description":{"large":"Some Large Text", "medium":"Это уникальный индустриальный сервер с большим количеством технических модов. Тут Вы найдете ваши любимые моды, такие как: Industrial Craft 2, Avaritia, Forestry, Applied Energistics 2, Draconic Evolution, а также ещё много чего интересного. Построй свой город с самой мощной электростанцией или лабораторию по производству иридия. Поторопись, твои друзья уже начали строить завод!", "small":"Some Small Text"}},"en": {"title": "HiTech", "description":{"large":"Some Large Text", "medium":"Some Medium Text", "small":"Some Small Text"}},"common": {}}
