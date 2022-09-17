import logging
import gfibot
import gfibot.data.update as update
import gfibot.data.rest as rest
import gfibot.data.dataset as dataset
import gfibot.model._predictor as predictor

from gfibot.collections import *
from gfibot.data.dataset import *

from gfibot.model.train import *
from gfibot.model.predict import *


def test_all(real_mongodb):
    update.logger.setLevel(logging.DEBUG)
    rest.logger.setLevel(logging.DEBUG)
    dataset.logger.setLevel(logging.DEBUG)

    token = gfibot.TOKENS[0] if len(gfibot.TOKENS) > 0 else None

    update.update_repo(token, "Mihara", "RasterPropMonitor")

    query = Q(owner="Mihara", name="RasterPropMonitor")
    repo1 = Repo.objects(query).first()

    update.update_repo(token, "Mihara", "RasterPropMonitor")
    repo2 = Repo.objects(query).first()
    assert len(repo2.monthly_stars) >= len(repo1.monthly_stars)
    assert len(repo2.monthly_commits) >= len(repo1.monthly_commits)
    assert len(repo2.monthly_pulls) >= len(repo1.monthly_pulls)
    assert len(repo2.monthly_issues) >= len(repo1.monthly_issues)

    dataset.get_dataset_all("2008.01.01")
    open_issues1 = list(
        Dataset.objects(query & Q(resolver_commit_num=-1)).scalar("number")
    )
    assert len(set(open_issues1)) == len(open_issues1)

    dataset.get_dataset_all("2008.01.01")
    open_issues2 = list(
        Dataset.objects(query & Q(resolver_commit_num=-1)).scalar("number")
    )
    assert len(set(open_issues2)) == len(open_issues2)
    assert len(set(open_issues1) - set(open_issues2)) == 0

    # Test the consistency of MongoDB
    open_issue_nums = set(OpenIssue.objects(query).scalar("number"))
    resolved_issue_nums = set(ResolvedIssue.objects(query).scalar("number"))
    assert len(open_issue_nums & resolved_issue_nums) == 0
    for num in open_issue_nums:
        data = Dataset.objects(query & Q(number=num))
        assert data.count() == 1
        assert data.first().resolver_commit_num == -1
    for num in resolved_issue_nums:
        data = Dataset.objects(query & Q(number=num))
        assert data.count() == 2
        assert data.first().resolver_commit_num >= 0

    predictor.update(cleanup=True)
    predictor.update()

    # Test the new training API
    train_all()
