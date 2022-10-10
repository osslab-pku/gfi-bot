import sys
import toml
import nltk
import logging
import os

from typing import List
from pathlib import Path


logging.basicConfig(
    format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_DIR = Path(__file__).parent.parent.absolute()
with open(BASE_DIR / "pyproject.toml", "r", encoding="utf-8") as f:
    CONFIG = toml.load(f)

TOKENS: List[str] = []
if not (BASE_DIR / "tokens.txt").exists():
    logging.error("No tokens.txt file found. Please create one.")
else:
    with open(BASE_DIR / "tokens.txt") as f:
        TOKENS = f.read().strip().split("\n")

# download if not exists to speedup startup
try:
    nltk.data.find("corpora/wordnet.zip")
except LookupError:
    nltk.download("wordnet")

try:
    nltk.data.find("corpora/omw-1.4.zip")
except LookupError:
    nltk.download("omw-1.4")

try:
    nltk.data.find("corpora/stopwords.zip")
except LookupError:
    nltk.download("stopwords")

# run in dev env
is_dev_env = os.environ.get("GFIBOT_ENV", "").lower()
if is_dev_env in ["dev", "development"]:
    logging.info("Running in development environment")
    CONFIG["mongodb"] = CONFIG["mongodb_dev"]
