from gfibot.data.graphql import *

from pprint import pprint
from datetime import datetime, timedelta, timezone
from gfibot import TOKENS


def _pprint_node(node: GraphQLQueryComponent, indent=0):
    print(f"{' ' * indent}{str(node)}")
    for k, v in node.args.items():
        print(f"{' ' * (indent + 2)} {k}: {v}")
    for c in node.children:
        if isinstance(c, GraphQLQueryComponent):
            _pprint_node(c, indent + 2)
        else:
            pprint(f"{' ' * (indent + 2)} {c}")


def test_gen_query():
    q = GraphQLQueryComponent(
        "query",
        {},
        None,
        "rateLimit {\n  cost\n  limit\n  remaining\n  resetAt\n}",
        GraphQLQueryComponent(
            "user",
            {"login": "xmcp"},
            None,
            "login",
            "name",
            GraphQLQueryPagedComponent(
                "issueComments",
                {"first": 100},
                None,
                "totalCount",
                "nodes {\n  url\n  body\n  publishedAt\n}",
            ),
            GraphQLQueryPagedComponent(
                "pullRequests",
                {"first": 100},
                None,
                "totalCount",
                "nodes {\n  url\n  body\n  publishedAt\n}",
            ),
            GraphQLQueryDateComponent(
                "contributionsCollection",
                {"from": "2020-01-01", "interval_days": 365},
                None,
                "contributionCalendar {\n  totalContributions\n}",
            ),
        ),
    )
    s = q.gen_query()
    _pprint_node(q)
    assert "2020-12-31" in s
    assert "interval" not in s


def test_update_state():
    q = GraphQLQueryComponent(
        "query",
        {},
        None,
        "rateLimit {\n  cost\n  limit\n  remaining\n  resetAt\n}",
        GraphQLQueryComponent(
            "user",
            {"login": "xmcp"},
            None,
            "login",
            "name",
            GraphQLQueryPagedComponent(
                "issueComments",
                {"first": 100},
                None,
                "totalCount",
                "nodes {\n  url\n  body\n  publishedAt\n}",
            ),
            GraphQLQueryPagedComponent(
                "pullRequests",
                {"first": 100},
                None,
                "totalCount",
                "nodes {\n  url\n  body\n  publishedAt\n}",
            ),
            GraphQLQueryDateComponent(
                "contributionsCollection",
                {"from": "2020-01-01", "interval_days": 365},
                None,
                "contributionCalendar {\n  totalContributions\n}",
            ),
        ),
    )
    mock_r = {
        "rateLimit": {
            "cost": 1,
            "limit": 5000,
            "remaining": 4996,
            "resetAt": "2022-04-28T11:08:39Z",
        },
        "user": {
            "login": "xmcp",
            "name": "xmcp",
            "issueComments": {
                "nodes": [
                    {
                        "url": "https://github.com/rspivak/slimit/issues/76#issuecomment-140697326",
                        "body": "+1\n",
                        "publishedAt": "2015-09-16T10:20:25Z",
                    }
                ],
                "totalCount": 558,
                "pageInfo": {
                    "hasNextPage": True,
                    "endCursor": "Y3Vyc29yOnYyOpHOCGLe7g==",
                },
            },
            "pullRequests": {
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "Y3Vyc29yOnYyOpHOAqk5_Q==",
                },
                "nodes": [
                    {
                        "url": "https://github.com/byt3bl33d3r/MITMf/pull/193",
                        "body": "",
                        "publishedAt": "2015-09-10T09:22:02Z",
                    }
                ],
            },
            "contributionsCollection": {
                "endedAt": "2023-04-27T15:43:38Z",
                "startedAt": "2022-04-27T15:43:38Z",
                "contributionCalendar": {"totalContributions": 442},
            },
        },
    }
    q.update_state(mock_r)
    _pprint_node(q)

    assert not q.children[1].children[2].finished
    assert q.children[1].children[3].finished
    assert q.children[1].children[4].finished


def test_user_fetcher():
    # requires access to GitHub API
    token = TOKENS[0] if len(TOKENS) > 0 else None
    uf = UserFetcher(
        token=token,
        login="antfu",
        since=datetime.now() - timedelta(days=1),
        callbacks={
            "query": lambda x: print("query", x),
            "user": lambda x: print("\033[31muser", x),
            "issues": lambda x: print("\033[32missues", x),
            "contributionsCollection": lambda x: print(
                "\033[33mcontributionsCollection", x
            ),
            "commitContributionsByRepository": lambda x: print(
                "\033[34mcommitContributionsByRepository", x
            ),
            "pullRequestReviewContributions": lambda x: print(
                "\033[35mpullRequestReviewContributions", x
            ),
            "pullRequestContributions": lambda x: print(
                "\033[0mpullRequestContributions", x
            ),
        },
    )
    uf.fetch()
