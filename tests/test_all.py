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

    update.update_repo(token, "Mihara", "RasterPropMonitor")
    repo1 = Repo.objects(owner="Mihara", name="RasterPropMonitor").first()

    update.update_repo(token, "Mihara", "RasterPropMonitor")
    repo2 = Repo.objects(owner="Mihara", name="RasterPropMonitor").first()
    assert len(repo2.monthly_stars) >= len(repo1.monthly_stars)
    assert len(repo2.monthly_commits) >= len(repo1.monthly_commits)
    assert len(repo2.monthly_pulls) >= len(repo1.monthly_pulls)
    assert len(repo2.monthly_issues) >= len(repo1.monthly_issues)

    dataset.get_dataset_all()
    open_issues1 = list(
        Dataset.objects(
            owner="Mihara", name="RasterPropMonitor", resolver_commit_num=-1
        ).scalar("number")
    )
    assert len(set(open_issues1)) == len(open_issues1)

    dataset.get_dataset_all()
    open_issues2 = list(
        Dataset.objects(
            owner="Mihara", name="RasterPropMonitor", resolver_commit_num=-1
        ).scalar("number")
    )
    assert len(set(open_issues2)) == len(open_issues2)
    assert len(set(open_issues1) - set(open_issues2)) == 0
