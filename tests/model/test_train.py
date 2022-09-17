from gfibot.model.train import *


def test_load_dataset(mock_mongodb):
    df = load_full_dataset(1)
