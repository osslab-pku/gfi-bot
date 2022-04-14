import toml
import nltk
import logging
import mongoengine

from typing import List
from pathlib import Path


logging.basicConfig(
    format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
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

mongoengine.connect(
    CONFIG["mongodb"]["db"],
    host=CONFIG["mongodb"]["url"],
    tz_aware=True,
    uuidRepresentation="standard",
)

nltk.download("wordnet")
nltk.download("omw-1.4")
