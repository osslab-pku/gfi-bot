import logging
import gfibot
import gfibot.data.update as update
import gfibot.data.rest as rest
import gfibot.data.dataset as dataset

from gfibot.collections import *
from gfibot.data.dataset import *


def test_all(real_mongodb):
    update.logger.setLevel(logging.DEBUG)
    rest.logger.setLevel(logging.DEBUG)
    dataset.logger.setLevel(logging.DEBUG)

    token = gfibot.TOKENS[0] if len(gfibot.TOKENS) > 0 else None

    # Update twice to test incremental update
    update.update_repo(token, "Mihara", "RasterPropMonitor")
    update.update_repo(token, "Mihara", "RasterPropMonitor")

    dataset.get_dataset_all()
