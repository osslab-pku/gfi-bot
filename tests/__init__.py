import gfibot
import logging

from gfibot.init_db import init_db

MONGO_URL = gfibot.CONFIG["mongodb"]["url"]
DB_NAME = "gfibot-test"
COLLECTIONS = gfibot.CONFIG["mongodb"]["collections"].values()

try:
    logging.info("Initializing database with default configurations...")
    init_db(MONGO_URL, DB_NAME, COLLECTIONS, True)
except:
    logging.error(
        "Failed to initialize database with default configurations, try a local configuration"
    )
    MONGO_URL = "mongodb//localhost:27017"
    init_db(MONGO_URL, DB_NAME, COLLECTIONS, True)
