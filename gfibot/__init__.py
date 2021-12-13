import toml
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
)

BASE_DIR = Path(__file__).parent.parent.absolute()
TOKENS = []
if not (BASE_DIR / "tokens.txt").exists():
    logging.error("No tokens.txt file found. Please create one.")
else:
    with open(BASE_DIR / "tokens.txt") as f:
        TOKENS = f.read().strip().split("\n")

with open(BASE_DIR / "pyproject.toml", "r") as f:
    CONFIG = toml.load(f)
