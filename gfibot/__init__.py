import toml
import logging
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    level=logging.INFO,
)

BASE_DIR = Path(__file__).parent.parent.absolute()
with open(BASE_DIR / "tokens.txt") as f:
    TOKENS = f.read().strip().split("\n")

with open(BASE_DIR / "pyproject.toml", "r") as f:
    CONFIG = toml.load(f)
