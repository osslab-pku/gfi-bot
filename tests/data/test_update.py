from gfibot import TOKENS
from datetime import datetime
from gfibot.data.update import update, count_by_month


def test_update():
    token = TOKENS[0] if len(TOKENS) > 0 else None
    update(token, "octocat", "hello-world")
    update(token, "octocat", "hello-world")  # Update twice to test incremental update


def test_count_by_month():
    c = count_by_month(
        [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2021, 3, 4)]
    )
    print(c)
    assert c[0]["count"] == 2 and c[1]["count"] == 1
