import logging
import requests

from . import TOKENS
from pprint import pformat
from datetime import datetime

from typing import Set, List


def _mask_token(token: str) -> str:
    return "*" * (len(token) - 5) + token[-5:]


def check_tokens(tokens: List[str]) -> Set[str]:
    """
    Check if the tokens are valid.
    :return: A set of invalid tokens.
    """
    failed_tokens = set()

    if len(tokens) == 0:
        logging.error("No tokens found")
        exit(1)

    for token in tokens:
        url = "https://api.github.com/"
        r = requests.get(url, headers={"Authorization": "token " + token})
        logging.info("Token: %s", _mask_token(token))
        logging.info("  Status %s: %s", r.status_code, r.reason)

        if r.status_code == 401:
            logging.info("  Token %s is invalid", _mask_token(token))
            failed_tokens.add(token)
            continue

        rate_limit, remaining, reset_at = (
            int(r.headers["X-RateLimit-Limit"]),
            int(r.headers["X-RateLimit-Remaining"]),
            datetime.fromtimestamp(int(r.headers["X-RateLimit-Reset"])),
        )

        logging.info(
            "  (REST) Rate limit: %d, remaining: %d, reset at: %s",
            rate_limit,
            remaining,
            reset_at.isoformat(),
        )
        if rate_limit != 5000:
            logging.error("  The token is likely not valid!")
        if remaining == 0:
            logging.error("  Rate limit exceeded!")

        url = "https://api.github.com/graphql"
        r = requests.post(
            url,
            headers={"Authorization": "token " + token},
            json={
                "query": """
                {
                    rateLimit {
                        limit
                        remaining
                        resetAt
                    }
                }
                """
            },
        )
        if r.status_code == 401:
            logging.info("  Token %s is invalid", _mask_token(token))
            failed_tokens.add(token)
            continue

        res = r.json()["data"]

        rate_limit, remaining, reset_at = (
            int(res["rateLimit"]["limit"]),
            int(res["rateLimit"]["remaining"]),
            datetime.fromisoformat(res["rateLimit"]["resetAt"].replace("Z", "")),
        )

        logging.info(
            "  (GraphQL) Rate limit: %d, remaining: %d, reset at: %s",
            rate_limit,
            remaining,
            reset_at.isoformat(),
        )
        if rate_limit != 5000:
            logging.error("  The token is likely not valid!")
        if remaining == 0:
            logging.error("  Rate limit exceeded!")

    if len(failed_tokens) > 0:
        logging.info(
            "Failed tokens: %s", pformat([_mask_token(x) for x in failed_tokens])
        )

    logging.info("Done!")

    return failed_tokens


if __name__ == "__main__":
    check_tokens(TOKENS)
