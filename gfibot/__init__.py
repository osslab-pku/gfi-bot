import toml
import logging
import pymongo
import pymongo.database

from typing import List
from pathlib import Path


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
)

BASE_DIR = Path(__file__).parent.parent.absolute()
TOKENS: List[str] = []
if not (BASE_DIR / "tokens.txt").exists():
    logging.error("No tokens.txt file found. Please create one.")
else:
    with open(BASE_DIR / "tokens.txt") as f:
        TOKENS = f.read().strip().split("\n")

with open(BASE_DIR / "pyproject.toml", "r") as f:
    CONFIG = toml.load(f)


class Database(object):
    """Simple wrapper for accessing the MongoDB database

    Should be used like:
    ```
    with gfibot.Database() as db:
        db.repo.insert_one(...)
    ```
    """

    def __init__(self):
        pass

    def __enter__(self) -> pymongo.database.Database:
        global CONFIG
        self.client = pymongo.MongoClient(CONFIG["mongodb"]["url"])
        return self.client[CONFIG["mongodb"]["db"]]

    def __exit__(self, *args, **kwargs):
        self.client.close()
