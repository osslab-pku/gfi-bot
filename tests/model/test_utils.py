import os

import pandas as pd
from gfibot.model.utils import split_train_test, get_full_path


def test_split_train_test():
    data = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "created_at": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "closed_at": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "is_gfi": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        }
    )
    for split_by in ["random", "created_at", "closed_at"]:
        train_x, test_x, train_y, test_y = split_train_test(
            data, by=split_by, test_size=0.2
        )
        assert len(train_x) == 8, "Train set should have 8 rows"
        assert len(train_x) + len(test_x) == len(data), "Train + test should equal data"
        assert (
            len(train_x.merge(test_x, how="inner")) == 0
        ), "Train and test should not intersect"
    train_x, test_x, train_y, test_y = split_train_test(data, by="random", test_size=0)
    assert len(test_x) != 0, "Test set should not be empty when test_size=0"


def test_get_full_path():
    path = get_full_path("tests", "data", "test.txt")
    assert path == os.path.abspath(os.path.join("tests", "data", "test.txt"))
    assert os.path.exists(os.path.dirname(path)) and os.path.isdir(
        os.path.dirname(path)
    )
