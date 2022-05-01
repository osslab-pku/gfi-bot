import logging
import time

from typing import Dict, List, Tuple, Callable, Any
from datetime import datetime, timedelta

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
from dateutil.parser import parse as parse_date

# make gql silent
from gql.transport.requests import log as requests_logger

requests_logger.setLevel(logging.WARNING)

# load the graphql schema
from gfibot import CONFIG
import requests


class GitHubGraphQLClient(object):
    @staticmethod
    def _load_graphql_schema(schema_path: str) -> str or None:
        schema_url = "https://docs.github.com/public/schema.docs.graphql"
        try:
            with open(schema_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logging.info("Could not load schema: %s, getting from GitHub", schema_path)
            try:
                r = requests.get(schema_url)
                if r.status_code == 200:
                    with open(schema_path, "w") as f:
                        f.write(r.text)
                    return r.text
                else:
                    raise Exception(
                        "Could not load schema from GitHub: HTTP %s" % r.status_code
                    )
            except Exception as e:
                logging.error("Could not load schema from GitHub: %s", e)
                return None

    def __init__(
        self,
        github_token: str,
        num_retries: int = 3,
        retry_interval: int = 60,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._token = github_token
        self._num_retries = num_retries

        self._schema = None
        try:
            self._schema = self._load_graphql_schema(
                CONFIG["gfibot"]["github_graphql_schema_path"]
            )
        except KeyError as e:
            self._logger.error("Schema path not found in config: %s", e)
        if not self._schema:
            self._logger.info("Fallback to introspection")

        self._client = Client(
            transport=RequestsHTTPTransport(
                url="https://api.github.com/graphql",
                headers={"Authorization": "Bearer {}".format(github_token)},
                verify=True,
                retries=num_retries,
            ),
            fetch_schema_from_transport=(self._schema is None),
            schema=self._schema,
        )

        self._retry_interval = retry_interval
        self._reset_at = time.time() + self._retry_interval

    def get_one(self, query: str, variables=None, default=None) -> dict or None:
        retries = 1
        while retries <= self._num_retries:
            try:
                result = self._client.execute(gql(query), variable_values=variables)

                # update reset_at
                reset_at: str or None = result.get("rateLimit", {}).get("resetAt")
                if reset_at:
                    self._reset_at = datetime.strptime(
                        reset_at, "%Y-%m-%dT%H:%M:%SZ"
                    ).timestamp()
                else:
                    self._reset_at = time.time() + self._retry_interval

                return result

            # we got an error from GitHub API
            except TransportQueryError as e:
                # hit rate limit
                if e.data and e.data.get("type") == "RATE_LIMITED":
                    sleep_time = max(self._reset_at - time.time() + 1, 1)
                    self._logger.info(
                        "Hit rate limit. Sleeping for %d seconds",
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    self._reset_at = max(
                        self._reset_at, time.time() + self._retry_interval
                    )
                    continue

                # unknown error
                else:
                    self._logger.error(
                        "GitHub API error: %s, variables: %s", e, variables
                    )
                    break

            # token invalid
            except TransportServerError as e:
                if e.code == 401:
                    self._logger.error("Unauthenticated: Invalid token %s", '*' * (len(self._token) - 5) + self._token[-5:])
                    break
                else:
                    self._logger.error("Unexpected HTTP error: %d", e.code)

        return default


class GraphQLQueryComponent(object):
    @staticmethod
    def _wrap_str(s: str or Dict) -> str:
        """Wraps s in quotes if s is not a number, type or variable"""
        # not a str?
        if isinstance(s, dict):
            # don't wrap enums
            return (
                "{"
                + ", ".join(
                    [f"{k}: {GraphQLQueryComponent._wrap_str(v)}" for k, v in s.items()]
                )
                + "}"
            )
        elif not isinstance(s, str):
            s = str(s)
        # is a number?
        if s.isdigit():
            return s
        # is a variable?
        if s[0] == "$":
            return s
        # is a type?
        if s[0].isupper and s.endswith("!"):
            return s
        # is it a enum?
        if s in [
            "ASC",
            "DESC",
            "CREATED_AT",
            "UPDATED_AT",
            "PUSHED_AT",
            "MERGED_AT",
            "CLOSED_AT",
            "FIRST_SEEN_AT",
            "LAST_SEEN_AT",
        ]:
            return s
        return '"' + s + '"'

    @staticmethod
    def _add_indent(s: str) -> str:
        """Adds indent to s"""
        return "\n".join(["  " + x for x in s.split("\n")])

    @staticmethod
    def _format_child(s: str or "GraphQLQueryComponent", indent: bool) -> str:
        """Formats a child"""
        if indent:
            if isinstance(s, GraphQLQueryComponent):
                return s.gen_query(indent=True)
            return s
        else:
            if isinstance(s, GraphQLQueryComponent):
                return s.gen_query(indent=False)
            return " ".join(s.replace("\n", "").split())

    def __init__(
        self,
        name: str,
        args: Dict[str, Any] = None,
        callback: Callable[[Dict[str, Any]], None] or None = None,
        *children: "GraphQLQueryComponent" or str,
    ):
        """
        Initializes a GraphQL query component
        :param name: The name of the query component
        :param args: The arguments of the query component
        :param callback: The callback function to be called on query results (optional)
        :param children: The children of the query component (can be strings or GraphQLQueryComponents)

        >>> q = GraphQLQueryComponent("query", {"first": 10}, None, "user", "repository")
        >>> q.gen_query()
        'query(first: 10) {user {repository}} '
        """
        self.name = name
        self.args = args if args else {}

        self._callback = callback
        self.children = children
        self.finished = False

    def __str__(self):
        """Pretty print attributes"""
        return f"{self.__class__.__name__}({self.name}, {self.args})"

    def _init_state(self) -> None:
        """Initializes state"""
        self.finished = False

    def _next_state(self, res: Dict[str, Any]) -> None:
        """Updates state"""
        self.finished = True

    def _propagate_state(self) -> None:
        """Propagates finished attribute to children"""
        # print("propagate_state", str(self))
        if self.finished:
            self._init_state()
        for c in self.children:
            if not isinstance(c, GraphQLQueryComponent):
                continue
            c._propagate_state()

    def update_state(self, res: Dict[str, Any]) -> None:
        """Updates finished attribute"""
        try:
            # print("update_state", str(self))
            # run callback
            if self._callback:
                self._callback(res)

            # update children's state
            self.finished = True
            for c in self.children:
                if not isinstance(c, GraphQLQueryComponent):
                    continue
                # update EVERY child's state and run callback
                if not c.finished:
                    try:
                        c.update_state(res[c.name])
                    except KeyError as e:
                        logging.error(
                            f"{str(self)}: Expecting {c.name} in {res.keys()}"
                        )
                        raise e
                if not c.finished:
                    self.finished = False

            # update self's state if all children have finished
            if self.finished:
                self._next_state(res)

                # has next state
                if not self.finished:
                    # propagate next state to children
                    for c in self.children:
                        if not isinstance(c, GraphQLQueryComponent):
                            continue
                        c._propagate_state()
        except Exception as e:
            logging.error(f"Error executing callback: {str(self)}")
            raise e

    def gen_query(self, indent: bool = True) -> str:
        """
        Generates the query string
        :param indent: The indent level
        :return: The query string
        """
        if self.finished:
            return ""

        q = self.name
        if self.args:
            q += (
                "("
                + ", ".join([f"{k}: {self._wrap_str(v)}" for k, v in self.args.items()])
                + ")"
            )

        if self.children:
            if indent:
                q += "{\n"
                q += "\n".join(
                    [
                        self._add_indent(self._format_child(c, True))
                        for c in self.children
                    ]
                )
                q += "\n}"
            else:
                q += (
                    " {"
                    + " ".join([self._format_child(c, False) for c in self.children])
                    + "}"
                )
        return q


class GraphQLQueryPagedComponent(GraphQLQueryComponent):
    def __init__(
        self,
        name: str,
        args: Dict[str, Any] = None,
        callback: Callable[[Dict[str, Any]], None] or None = None,
        *children: "GraphQLQueryComponent" or str,
    ):
        """
        Initializes a GraphQL query component with pagination
        :param name: The name of the query component
        :param args: The arguments of the query component
        :param callback: The callback function to be called on query results (optional)
        :param children: The children of the query component (can be strings or GraphQLQueryComponents)

        >>> q = GraphQLQueryPagedComponent("query", {"first": 10}, None, "user", "repository")
        >>> q.gen_query()
        'query(first: 10) {user {repository} pageInfo { hasNextPage  endCursor}}'
        """
        super().__init__(name, args, callback, *children)
        self.children = (*self.children, "pageInfo {\n  hasNextPage\n  endCursor\n}")

    def _init_state(self) -> None:
        """Initializes state"""
        self.finished = False
        if "after" in self.args:
            del self.args["after"]

    def _next_state(self, res: Dict[str, Any]) -> None:
        """Updates state"""
        self.finished = not res["pageInfo"]["hasNextPage"]
        if not self.finished:
            self.args["after"] = res["pageInfo"]["endCursor"]


class GraphQLQueryDateComponent(GraphQLQueryComponent):
    @staticmethod
    def _parse_date_utc(s: str) -> datetime:
        return parse_date(s).replace(tzinfo=datetime.utcnow().tzinfo)

    def __init__(
        self,
        name: str,
        args: Dict[str, Any] = None,
        callback: Callable[[Dict[str, Any]], None] or None = None,
        *children: "GraphQLQueryComponent" or str,
    ):
        """
        Initializes a GraphQL query component with date range
        :param name: The name of the query component
        :param args: The arguments of the query component ('from' is required, 'to' and 'interval_days' are optional)
        :param callback: The callback function to be called on query results (optional)
        :param children: The children of the query component (can be strings or GraphQLQueryComponents)

        >>> GraphQLQueryDateComponent("query", {"from": "2019-01-01", "to": "2022-01-01", "interval_days": 1}, None, "user", "repository").gen_query()
        'query(from: "2019-01-01T00:00:00Z", to: "2019-01-02T00:00:00Z") {user {repository} startedAt endedAt } '
        >>> GraphQLQueryDateComponent("query", {"from": "2019-01-01T00:00:00Z"}, None, "user", "repository").gen_query()
        'query(from: "2019-01-01T00:00:00Z") {user {repository} startedAt endedAt } '
        >>> GraphQLQueryDateComponent("query", {"from": "2019-01-01", "to": "2019-12-31", "interval_days": 400}, None, "user", "repository").gen_query()
        'query(from: "2019-01-01T00:00:00Z", to: "2019-12-31T00:00:00Z") {user {repository} startedAt endedAt } '
        """
        super().__init__(name, args, callback, *children)
        self.children = (*self.children, "startedAt", "endedAt")

        # read from args: 'from' 'to' 'interval'
        # from is required
        self._from_time = self._parse_date_utc(args["from"])
        # to and interval can be infered
        # fix precision
        self._to_time = (
            self._parse_date_utc(args["to"])
            if "to" in args
            else datetime.now().replace(tzinfo=datetime.utcnow().tzinfo, microsecond=0)
        )
        # print(f"{self}: from {self._from_time} to {self._to_time}", file=sys.stderr)
        self._interval = (
            timedelta(days=args["interval_days"]) if "interval_days" in args else None
        )

        # process args
        self.args["from"] = self._from_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        if "interval_days" in self.args:
            del self.args["interval_days"]

        if not self._interval and "to" in self.args:
            del self.args["to"]

        self._init_state()

    def _init_state(self) -> None:
        """Initializes state"""
        self.finished = False
        self.args["from"] = self._from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if self._interval and self._from_time + self._interval < self._to_time:
            self.args["to"] = (self._from_time + self._interval).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

    def _next_state(self, res: Dict[str, Any]) -> None:
        self.finished = self._parse_date_utc(res["endedAt"]) >= self._to_time
        if not self.finished:
            self.args["from"] = res["endedAt"]
            if not self._interval:
                self._interval = self._parse_date_utc(
                    res["endedAt"]
                ) - self._parse_date_utc(res["startedAt"])
            # graphql time
            self.args["to"] = min(
                self._parse_date_utc(res["endedAt"]) + self._interval, self._to_time
            ).strftime("%Y-%m-%dT%H:%M:%SZ")


class UserFetcher(object):
    def __init__(
        self,
        token: str,
        login: str,
        since: datetime,
        callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {},
    ) -> None:
        """
        Initializes a UserFetcher
        :param token: {str} GitHub token
        :param login: {str} github login
        :param since: {datetime} since when to fetch
        :param callbacks: {Dict[str, Callable[[Dict[str, Any]], None]]} callbacks to call on each response

        >>> uf = UserFetcher("token", "login", datetime.now(), {'issues': lambda x: print('issues', x)})
        >>> uf.fetch()
        'issues' {'totalCount': 558, 'nodes': [...]}
        """

        self.gh_gql = GitHubGraphQLClient(token)
        self.per_page = 100
        self.login = login
        self._callbacks = callbacks
        # cast to utc
        self._since_str = since.replace(tzinfo=datetime.utcnow().tzinfo).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        self._logger = logging.getLogger(__name__)

    def _handle_callback(self, name: str):
        return self._callbacks[name] if name in self._callbacks else None

    def fetch(self) -> None:
        """Runs the query"""
        self._logger.debug(f"Fetching metrics for {self.login} since {self._since_str}")

        q = GraphQLQueryComponent(
            "query",
            {},
            self._handle_callback("query"),
            "rateLimit {\n  cost\n  limit\n  remaining\n  resetAt\n}",
            GraphQLQueryComponent(
                "user",
                {"login": self.login},
                self._handle_callback("user"),
                "login",
                "name",
                GraphQLQueryPagedComponent(
                    "issues",
                    {"first": self.per_page, "filterBy": {"since": self._since_str}},
                    self._handle_callback("issues"),
                    "totalCount",
                    "nodes {\n  number\n  state\n  repository {\n    nameWithOwner\n    stargazerCount\n  }\n  createdAt\n}",
                ),
                GraphQLQueryDateComponent(
                    "contributionsCollection",
                    {"from": self._since_str, "interval_days": 365},
                    self._handle_callback("contributionsCollection"),
                    GraphQLQueryComponent(
                        "commitContributionsByRepository",
                        {},
                        self._handle_callback("commitContributionsByRepository"),
                        "contributions (first: %d, orderBy: {field: COMMIT_COUNT, direction: DESC}){\n  nodes {\n    commitCount\n    occurredAt\n  }\n}"
                        % self.per_page,
                        "repository {\n    nameWithOwner\n    stargazerCount\n  }",
                    ),
                    GraphQLQueryPagedComponent(
                        "pullRequestReviewContributions",
                        {"first": self.per_page},
                        self._handle_callback("pullRequestReviewContributions"),
                        "nodes {\n  repository {\n    nameWithOwner\n    stargazerCount\n  }\n  isRestricted\n  pullRequestReview {\n    createdAt\n    state\n   pullRequest{\n  number  \n}  \n }\n}",
                    ),
                    GraphQLQueryPagedComponent(
                        "pullRequestContributions",
                        {"first": self.per_page},
                        self._handle_callback("pullRequestContributions"),
                        "nodes {\n  pullRequest {\n  createdAt\n    number\n   state\n  repository {\n    nameWithOwner\n    stargazerCount\n  }\n  }\n}",
                    ),
                ),
            ),
        )

        while not q.finished:
            s = q.gen_query(False)
            self._logger.debug(f"Running query: {s}")
            r = self.gh_gql.get_one(q.gen_query(False))
            if r is None:
                self._logger.error("Exception while running query")
                raise Exception("Exception while running query")
            self._logger.debug(f"Got response: rateLimit {r['rateLimit']}")
            try:
                q.update_state(r)
            except Exception as e:
                self._logger.error(f"Exception while updating state: {e}")
                self._logger.error(f"Response: {r}")
                raise e
