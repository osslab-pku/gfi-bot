import sys
import toml
import nltk
import logging
import os
from typing import List
from pathlib import Path

# ---------------- Logging Setup ----------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ---------------- Paths & Config ----------------
BASE_DIR = Path(__file__).parent.parent.absolute()
config_path = BASE_DIR / "pyproject.toml"

if not config_path.exists():
    logger.error(f"Config file not found at {config_path}")
    CONFIG = {}
else:
    with open(config_path, "r", encoding="utf-8") as f:
        CONFIG = toml.load(f)

# ---------------- Tokens ----------------
TOKENS: List[str] = []
tokens_path = BASE_DIR / "tokens.txt"

if not tokens_path.exists():
    logger.error("No tokens.txt file found. Please create one.")
else:
    with open(tokens_path) as f:
        TOKENS = [line.strip() for line in f if line.strip()]

# ---------------- NLTK Setup ----------------
for corpus in ["wordnet", "omw-1.4", "stopwords"]:
    try:
        nltk.data.find(f"corpora/{corpus}")
    except LookupError:
        logger.info(f"Downloading missing NLTK corpus: {corpus}")
        nltk.download(corpus)

# ---------------- Environment ----------------
is_dev_env = os.environ.get("GFIBOT_ENV", "").lower()
if is_dev_env in ["dev", "development"]:
    logger.info("Running in development environment")
    CONFIG["mongodb"] = CONFIG.get("mongodb_dev", CONFIG.get("mongodb", {}))

__all__ = ["CONFIG", "TOKENS"]
