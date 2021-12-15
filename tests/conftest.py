import pytest
import logging

from gfibot import CONFIG
from gfibot.init_db import init_db
from gfibot.check_tokens import check_tokens


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    logging.basicConfig(level=logging.DEBUG)

    CONFIG["mongodb"]["db"] = "gfibot-test"

    collections = CONFIG["mongodb"]["collections"].values()
    try:
        logging.info("Initializing database with default configurations...")
        init_db(CONFIG["mongodb"]["url"], CONFIG["mongodb"]["db"], collections, True)
    except:
        logging.error("Failed with default, try a local configuration")
        CONFIG["mongodb"]["url"] = "mongodb://localhost:27017"
        init_db(CONFIG["mongodb"]["url"], CONFIG["mongodb"]["db"], collections, True)

    check_tokens()
