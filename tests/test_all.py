import logging
import gfibot
import gfibot.data.update as upd
import gfibot.data.rest as rest

from gfibot.collections import *
from gfibot.data.dataset import *


def test_all(real_mongodb):
    upd.logger.setLevel(logging.DEBUG)
    rest.logger.setLevel(logging.DEBUG)

    token = gfibot.TOKENS[0] if len(gfibot.TOKENS) > 0 else None

    # Update twice to test incremental update
    upd.update_repo(token, "octocat", "Hello-World")
    upd.update_repo(token, "octocat", "Hello-World")

    upd.update_repo(token, "Mihara", "RasterPropMonitor")
    upd.update_repo(token, "Mihara", "RasterPropMonitor")

    for resolved_issue in ResolvedIssue.objects():
        get_dataset(resolved_issue, resolved_issue.resolved_at)
