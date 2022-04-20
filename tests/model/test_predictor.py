from datetime import datetime, timezone
from pandas.testing import assert_frame_equal
import os
import sys

current_work_dir = os.path.dirname(__file__)
utpath = os.path.join(current_work_dir, "../..")
sys.path.append(utpath)
from gfibot.collections import *
from gfibot.model.predictor import *
from gfibot.model.utils import *
from tests.conftest import *


def test_get_update_set(mock_mongodb):
    threshold = 1
    dataset_batch = [
        Dataset.objects(name="name", owner="owner", number=5).first(),
        Dataset.objects(name="name", owner="owner", number=6).first(),
    ]
    update_set = get_update_set(threshold, dataset_batch)
    assert update_set == [
        ["name", "owner", [5, datetime(1970, 1, 3, 0, 0, tzinfo=timezone.utc)]],
        ["name", "owner", [6, datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc)]],
    ]


def test_update_basic_TrainingSummary(mock_mongodb):
    update_set = [
        ["name", "owner", [5, datetime(1970, 1, 3, 0, 0, tzinfo=timezone.utc)]],
        ["name", "owner", [6, datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc)]],
    ]
    dataset_batch = [
        Dataset.objects(name="name", owner="owner", number=5).first(),
        Dataset.objects(name="name", owner="owner", number=6).first(),
    ]
    min_test_size = 1
    threshold = 1
    get_update_set(threshold, dataset_batch)
    train_90_add = update_basic_TrainingSummary(update_set, min_test_size, threshold)
    assert train_90_add == [
        ["name", "owner", [6, datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc)]]
    ]


def test_update_models(mock_mongodb):
    update_set = [
        ["name", "owner", [5, datetime(1970, 1, 3, 0, 0, tzinfo=timezone.utc)]],
        ["name", "owner", [6, datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc)]],
    ]
    train_90_add = [
        ["name", "owner", [5, datetime(1970, 1, 3, tzinfo=timezone.utc)]],
        ["name", "owner", [6, datetime(1971, 1, 3, tzinfo=timezone.utc)]],
    ]
    batch_size = 100
    threshold = 2
    repo = TrainingSummary(
        owner="owner",
        name="name",
        threshold=threshold,
        model_90_file="",
        model_full_file="",
        issues_train=[],
        issues_test=[],
        n_resolved_issues=0,
        n_newcomer_resolved=0,
        accuracy=0,
        auc=0,
        last_updated=datetime.now(),
    )
    repo.save()
    model_90 = update_models(update_set, train_90_add, batch_size, threshold)
    assert isinstance(model_90, xgb.core.Booster)
