import time
import logging
import requests

from . import TOKENS
from pprint import pformat
from datetime import datetime

if __name__ == "__main__":
    token2reset = {}
    failed_tokens = []

    for token in TOKENS:
        url = "https://api.github.com/"
        r = requests.get(url, headers={"Authorization": "token " + token})
        logging.info("Token: %s", token)
        logging.info("  Status %s: %s", r.status_code, r.reason)
        # logging.info("Headers: %s", pformat(dict(r.headers)))

        if r.status_code == 401:
            logging.info("  Token %s is invalid", token)
            failed_tokens.append(token)
            continue

        rate_limit, remaining, reset_at = (
            int(r.headers["X-RateLimit-Limit"]),
            int(r.headers["X-RateLimit-Remaining"]),
            datetime.fromtimestamp(int(r.headers["X-RateLimit-Reset"])),
        )
        token2reset[token] = reset_at
        logging.info(
            "  Rate limit: %d, remaining: %d, reset at: %s",
            rate_limit,
            remaining,
            reset_at.isoformat(),
        )
        if rate_limit != 5000:
            logging.error("  The token is likely not valid!")
        if any(reset_at == t for t in token2reset.values()):
            logging.error("  The token is likely a duplicate of existing token!")
        time.sleep(3)

    logging.info("Failed tokens: %s", pformat(failed_tokens))
    logging.info("Done!")
