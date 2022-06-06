import os
import sys
import toml
import nltk
import logging
import datetime
import mongoengine

from typing import List
from pathlib import Path


os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/gfibot-{datetime.datetime.now()}.log"),
    ],
)

BASE_DIR = Path(__file__).parent.parent.absolute()
with open(BASE_DIR / "pyproject.toml", "r") as f:
    CONFIG = toml.load(f)

TOKENS: List[str] = []
if not (BASE_DIR / "tokens.txt").exists():
    logging.error("No tokens.txt file found. Please create one.")
else:
    with open(BASE_DIR / "tokens.txt") as f:
        TOKENS = f.read().strip().split("\n")

mongoengine.connect(
    CONFIG["mongodb"]["db"],
    host=CONFIG["mongodb"]["url"],
    tz_aware=True,
    uuidRepresentation="standard",
)

nltk.download("wordnet")
nltk.download("omw-1.4")
