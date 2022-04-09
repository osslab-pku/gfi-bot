import pytest
import logging
import mongoengine

from gfibot import CONFIG
from gfibot.check_tokens import check_tokens


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    logging.basicConfig(level=logging.DEBUG)

    CONFIG["mongodb"]["db"] = "gfibot-test"
    mongoengine.disconnect_all()
    db = mongoengine.connect(
        CONFIG["mongodb"]["db"], host=CONFIG["mongodb"]["url"], tz_aware=True
    )
    db.drop_database(CONFIG["mongodb"]["db"])

    check_tokens()
