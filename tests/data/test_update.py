from gfibot import TOKENS
from gfibot.data.update import update


def test_update():
    token = TOKENS[0] if len(TOKENS) > 0 else None
    update(token, "octocat", "hello-world")
    update(token, "octocat", "hello-world")  # Update twice to test incremental update
