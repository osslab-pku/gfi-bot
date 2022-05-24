from flask import Flask, redirect, request, abort
from flask_cors import CORS
import requests
import logging

import json
from bson import ObjectId
from datetime import datetime, date
from urllib import parse
import numpy as np

from typing import Dict, Final

import urllib.parse

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import cmp_to_key

from gfibot.collections import *
from gfibot.data.update import update_repo
from gfibot.backend.daemon import start_scheduler, update_gfi_update_job
from gfibot.backend.utils import (
    delete_repo_from_query,
    update_repos,
    get_repo_stars,
    get_repo_gfi_num,
    get_newcomer_resolved_issue_rate,
    get_repo_info_detailed,
)

app = Flask(__name__)

executor = ThreadPoolExecutor(max_workers=10)

WEB_APP_NAME = "gfibot-webapp"
GITHUB_APP_NAME = "gfibot-githubapp"

logger = logging.getLogger(__name__)

daemon_scheduler = start_scheduler()


def generate_repo_update_task_id(owner, name):
    return f"{owner}-{name}-update"


@app.route("/api/repos/num")
def get_repo_num():
    """Get number of repos by filter"""
    language = request.args.get("lang")
    filter = request.args.get("filter")
    repos = Repo.objects()
    res = 0
    if language != None:
        res = len(Repo.objects(language=language))
    else:
        res = len(repos)
    return {"code": 200, "result": res}


@app.route("/api/repos/info")
def get_repo_info():
    repo_name = request.args.get("name")
    repo_owner = request.args.get("owner")
    if repo_name != None and repo_owner != None:
        repos = Repo.objects(Q(name=repo_name) & Q(owner=repo_owner)).first()
        return {
            "code": 200,
            "result": {
                "name": repos.name,
                "owner": repos.owner,
                "description": repos.description,
                "language": repos.language,
                "topics": repos.topics,
            },
        }
    else:
        return {"code": 400, "result": "invalid params"}


@app.route("/api/repos/info/detail")
def get_repo_detailed_info():
    """Get repo info by name/owner"""
    repo_name = request.args.get("name")
    repo_owner = request.args.get("owner")
    repo = Repo.objects(Q(name=repo_name) & Q(owner=repo_owner)).first()
    if repo:
        return {"code": 200, "result": get_repo_info_detailed(repo)}
    return {"code": 404, "result": "repo not found"}


REPO_FILTER_TYPES = [
    "popularity",
    "median_issue_resolve_time",
    "newcomer_friendly",
    "gfis",
]


def repo_stars_comp(repo_x, repo_y):
    delta = get_repo_stars(repo_x.owner, repo_x.name) - get_repo_stars(
        repo_y.owner, repo_y.name
    )
    if delta < 0:
        return 1
    elif delta > 0:
        return -1
    return 0


def repo_issue_close_time_comp(repo_x: Repo, repo_y: Repo):
    median_close_time_x = repo_x.median_issue_close_time
    if repo_x.median_issue_close_time == None:
        median_close_time_x = float("inf")
    median_close_time_y = repo_y.median_issue_close_time
    if repo_y.median_issue_close_time == None:
        median_close_time_y = float("inf")
    delta = median_close_time_x - median_close_time_y
    if delta < 0:
        return -1
    elif delta > 0:
        return 1
    return repo_stars_comp(repo_x, repo_y)


def repo_gfi_num_camp(repo_x, repo_y):
    gfi_num_x = get_repo_gfi_num(repo_x.owner, repo_x.name)
    gfi_num_y = get_repo_gfi_num(repo_y.owner, repo_y.name)
    delta = gfi_num_x - gfi_num_y
    if delta < 0:
        return 1
    elif delta > 0:
        return -1
    return repo_stars_comp(repo_x, repo_y)


def repo_newcomer_resolved_camp(repo_x, repo_y):
    new_comer_res_x = get_newcomer_resolved_issue_rate(repo_x.owner, repo_x.name)
    new_comer_res_y = get_newcomer_resolved_issue_rate(repo_y.owner, repo_y.name)
    delta = new_comer_res_x - new_comer_res_y
    if delta < 0:
        return 1
    elif delta > 0:
        return -1
    return repo_stars_comp(repo_x, repo_y)


@app.route("/api/repos/info/")
def get_paged_repo_detailed_info():
    start_idx = request.args.get("start")
    req_size = request.args.get("length")
    lang = request.args.get("lang")
    filter = request.args.get("filter")
    if start_idx != None and req_size != None:
        start_idx = int(start_idx)
        req_size = int(req_size)

        repos_query = []
        count = 0
        if lang != None and lang != "":
            repos_query = [
                repo for repo in Repo.objects(language=lang).order_by("name")
            ]
            count = len(repos_query)
        else:
            repos_query = [repo for repo in Repo.objects().order_by("name")]
            count = len(repos_query)

        if filter != None and filter in REPO_FILTER_TYPES:
            if filter == "popularity":
                repos_query.sort(key=cmp_to_key(repo_stars_comp))
            elif filter == "median_issue_resolve_time":
                repos_query.sort(key=cmp_to_key(repo_issue_close_time_comp))
            elif filter == "newcomer_friendly":
                repos_query.sort(key=cmp_to_key(repo_newcomer_resolved_camp))
            elif filter == "gfis":
                repos_query.sort(key=cmp_to_key(repo_gfi_num_camp))

        start_idx = max(0, start_idx)
        req_size = min(req_size, count)
        res = []
        if start_idx < count:
            for i, repo in enumerate(repos_query):
                if i >= start_idx and i - start_idx < req_size:
                    res.append(get_repo_info_detailed(repo))
        return {
            "code": 200,
            "result": res,
        }
    else:
        abort(400)


@app.route("/api/repos/info/search")
def search_repo_info_by_name_or_url():
    repo_name = request.args.get("repo")
    repo_url = request.args.get("url")
    if repo_url:
        repo_url = parse.unquote(repo_url)
    app.logger.info(repo_url)
    user_name = request.args.get("user")

    if repo_url:
        repo_name = repo_url.split(".git")[0].split("/")[-1]

    app.logger.info(
        "repo_name: {}, repo_url: {}, user_name: {}".format(
            repo_name, repo_url, user_name
        )
    )

    if repo_name:
        repos_query = Repo.objects(name=repo_name)
        if len(repos_query) > 0:
            if user_name:
                date_time = datetime.now(timezone.utc)
                user = GfiUsers.objects(github_login=user_name).first()
                if user:
                    [
                        user.update(
                            push__user_searches={
                                "repo": repo.name,
                                "owner": repo.owner,
                                "created_at": datetime.utcnow(),
                                "increment": len(user.user_searches) + 1,
                            }
                        )
                        for repo in repos_query
                    ]
            return {
                "code": 200,
                "result": [get_repo_info_detailed(repo) for repo in repos_query],
            }
        elif repo_url == "":
            return {"code": 404, "result": "Repo not found"}

    else:
        abort(400)


@app.route("/api/repos/add", methods=["POST"])
def add_repo_to_bot():
    content_type = request.headers.get("Content-Type")
    app.logger.info("content_type: {}".format(content_type))
    if content_type == "application/json":
        data = request.get_json()
        user_name = data["user"]
        repo_name = data["repo"]
        repo_owner = data["owner"]
        user_token = (
            GfiUsers.objects(github_login=user_name).first().github_access_token
        )
        if user_token == None:
            return {"code": 400, "result": "user not found"}
        if user_name != None and repo_name != None and repo_owner != None:
            app.logger.info(
                "adding repo to bot, {}, {}, {}".format(
                    repo_name, repo_owner, user_name
                )
            )
            if len(GfiUsers.objects(github_login=user_name)):
                user = GfiUsers.objects(github_login=user_name).first()
                repo_info = {
                    "name": repo_name,
                    "owner": repo_owner,
                }
                queries = [
                    {
                        "name": query.repo,
                        "owner": query.owner,
                    }
                    for query in user.user_queries
                ]

                if len(GfiQueries.objects(**repo_info)) == 0:
                    GfiQueries(
                        name=repo_name,
                        owner=repo_owner,
                        is_pending=True,
                        is_finished=False,
                        _created_at=datetime.utcnow(),
                    ).save()
                    executor.submit(update_repo, user_token, repo_owner, repo_name)

                if repo_info not in queries:
                    user.update(
                        push__user_queries={
                            "repo": repo_name,
                            "owner": repo_owner,
                            "increment": len(user.user_queries) + 1,
                            "created_at": datetime.utcnow(),
                        }
                    )
                    return {"code": 200, "result": "is being processed by GFI-Bot"}
                else:
                    return {"code": 200, "result": "already exists"}
        return {"code": 400, "result": "Bad request"}
    else:
        return {"code": 404, "result": "user not found"}


@app.route("/api/repos/recommend")
def get_recommend_repo():
    """
    get recommened repo name (currently using random)
    """
    repos = Repo.objects()
    res = np.random.choice(repos, size=1).tolist()[0]
    return {"code": 200, "result": get_repo_info_detailed(res)}


@app.route("/api/repos/language")
def get_deduped_repo_languages():
    languages = list(
        filter(
            lambda l: l != None,
            [lang for lang in Repo.objects().distinct(field="language")],
        )
    )
    return {"code": 200, "result": list(languages)}


@app.route("/api/repos/update/config")
def get_repo_query_config():
    repo_name = request.args.get("name")
    repo_owner = request.args.get("owner")
    if repo_name != None and repo_owner != None:
        repo_query = GfiQueries.objects(Q(name=repo_name) & Q(owner=repo_owner)).first()
        if repo_query:
            return {
                "code": 200,
                "result": {
                    "update_config": repo_query.update_config,
                    "repo_config": repo_query.repo_config,
                },
            }
        else:
            return {
                "code": 404,
                "result": "repo not found",
            }
    abort(400)


@app.route("/api/repos/update/", methods=["PUT"])
def update_repo_info():
    body = request.get_json()
    name = body["name"]
    owner = body["owner"]
    github_login = body["github_login"]
    user = GfiUsers.objects(github_login=github_login).first()
    if name != None and owner != None and user != None:
        query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
        if query != None and query.is_updating != True:
            query.update(
                is_updating=True,
                is_finished=False,
            )
            update_config = query.update_config
            if update_config != None:
                task_id = update_config.task_id
                interval = update_config.interval
            else:
                task_id = generate_repo_update_task_id(owner, name)
                interval = 24 * 3600
                query.update(
                    update_config={
                        "task_id": task_id,
                        "interval": interval,
                    }
                )
            update_repository_gfi_info(task_id=task_id, repo=name, owner=owner)
            return {"code": 200, "result": "query updating"}
        else:
            return {"code": 404, "result": "repo not found"}
    else:
        abort(400)


GITHUB_LOGIN_URL: Final = "https://github.com/login/oauth/authorize"


def get_predicted_info_from_engine(predict_list):
    return [
        {
            "name": item.name,
            "owner": item.owner,
            "number": item.number,
            "threshold": item.threshold,
            "probability": item.probability,
            "last_updated": item.last_updated,
        }
        for item in predict_list
    ]


@app.route("/api/issue/num")
def get_issue_num():
    issues = OpenIssue.objects()
    return {"code": 200, "result": len(issues)}


@app.route("/api/issue/gfi")
def get_gfi_info():
    """
    get GFIs by repo name
    """
    repo_name = request.args.get("repo")
    repo_owner = request.args.get("owner")
    app.logger.info
    if repo_name != None and repo_owner != None:
        gfi_list = Prediction.objects(
            Q(name=repo_name) & Q(owner=repo_owner) & Q(probability__gte=0.5)
        ).order_by("-probability")
        res = get_predicted_info_from_engine(gfi_list)
        if len(gfi_list):
            return {
                "code": 200,
                "result": res,
            }
        else:
            return {"code": 404, "result": "no gfi found"}
    else:
        abort(400)


@app.route("/api/issue/gfi/num")
def get_gfi_num():
    """
    Get num of GFIs by repo name
    """
    repo_name = request.args.get("repo")
    repo_owner = request.args.get("owner")
    if repo_name != None and repo_owner != None:
        gfi_list = Prediction.objects(
            Q(name=repo_name) & Q(owner=repo_owner) & Q(probability__gte=0.5)
        )
    else:
        gfi_list = Prediction.objects(Q(probability__gte=0.5))
    return {
        "code": 200,
        "result": len(gfi_list),
    }


@app.route("/api/user/github/login")
def github_login():
    """
    Process Github OAuth login procedure
    """
    client_id = GithubTokens.objects().first().client_id
    return {"code": 200, "result": GITHUB_LOGIN_URL + "?client_id=" + client_id}


def github_login_redirect(name: str, code: str):
    """
    Process Github OAuth login redirect
    """
    client_id = GithubTokens.objects(app_name=name).first().client_id
    client_secret = GithubTokens.objects(app_name=name).first().client_secret

    if name == WEB_APP_NAME:
        is_github_app = False
    elif name == GITHUB_APP_NAME:
        is_github_app = True
    else:
        abort(400)

    if client_id == None or client_secret == None:
        abort(500)

    if code != None:
        r = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            },
        )
        if r.status_code == 200:
            res_dict = dict(urllib.parse.parse_qsl(r.text))
            app.logger.info(res_dict)
            access_token = res_dict["access_token"]
            if access_token != None:
                r = requests.get(
                    "https://api.github.com/user",
                    headers={"Authorization": "token " + access_token},
                )
                if r.status_code == 200:
                    user_res = json.loads(r.text)
                    if not is_github_app:
                        GfiUsers.objects(github_id=user_res["id"]).upsert_one(
                            github_id=user_res["id"],
                            github_login=user_res["login"],
                            github_name=user_res["name"],
                            github_avatar_url=user_res["avatar_url"],
                            github_access_token=access_token,
                            github_email=user_res["email"],
                            github_url=user_res["url"],
                            twitter_user_name=user_res["twitter_username"],
                        )
                    else:
                        GfiUsers.objects(github_id=user_res["id"]).upsert_one(
                            github_id=user_res["id"],
                            github_login=user_res["login"],
                            github_name=user_res["name"],
                            github_avatar_url=user_res["avatar_url"],
                            github_app_token=access_token,
                            github_email=user_res["email"],
                            github_url=user_res["url"],
                            twitter_user_name=user_res["twitter_username"],
                        )
                    return redirect(
                        "/login/redirect?github_login={}&github_name={}&github_id={}&github_token={}&github_avatar_url={}".format(
                            user_res["login"],
                            user_res["name"],
                            user_res["id"],
                            access_token,
                            user_res["avatar_url"],
                        ),
                        code=302,
                    )
                return {"code": r.status_code, "result": r.text}
            else:
                return {
                    "code": 400,
                    "result": "access_token is None",
                }
        else:
            return {
                "code": r.status_code,
                "result": "Github login failed",
            }
    else:
        return {
            "code": 400,
            "result": "No code provided",
        }


@app.route("/api/model/training/result")
def get_training_result():
    """
    get training result
    """

    name = request.args.get("name")
    owner = request.args.get("owner")
    if name != None and owner != None:
        query = TrainingSummary.objects(Q(name=name) & Q(owner=owner)).order_by(
            "-threshold"
        )
        training_result = []
        if len(query):
            training_result = [query[0]]
    else:
        training_result = []
        for repo in Repo.objects():
            query = TrainingSummary.objects(
                Q(name=repo.name) & Q(owner=repo.owner)
            ).order_by("-threshold")
            if len(query):
                training_result.append(query[0])

    if training_result != None:
        return {
            "code": 200,
            "result": [
                {
                    "owner": result.owner,
                    "name": result.name,
                    "issues_train": len(result.issues_train),
                    "issues_test": len(result.issues_test),
                    "n_resolved_issues": result.n_resolved_issues,
                    "n_newcomer_resolved": result.n_newcomer_resolved,
                    "accuracy": result.accuracy,
                    "auc": result.auc,
                    "last_updated": result.last_updated,
                }
                for result in training_result
            ],
        }
    else:
        return {"code": 404, "result": "no training result found"}


@app.route("/api/user/github/callback")
def github_login_redirect_web():
    code = request.args.get("code")
    return github_login_redirect(name=WEB_APP_NAME, code=code)


@app.route("/api/user/queries", methods=["GET", "DELETE"])
def get_user_queries():
    method = request.method

    def get_user_query(queries):
        return [
            {
                "name": query.name,
                "owner": query.owner,
                "is_pending": query.is_pending,
                "is_finished": query.is_finished,
                "created_at": query._created_at,
                "finished_at": query._finished_at,
            }
            for query in queries
        ]

    def query_median_issue_resolve_time_comp(query_x, query_y):
        repo_x = Repo.objects(name=query_x.name, owner=query_x.owner).first()
        repo_y = Repo.objects(name=query_y.name, owner=query_y.owner).first()
        return repo_issue_close_time_comp(repo_x, repo_y)

    user_name = request.args.get("user")
    if user_name != None:
        if method == "GET":
            user_queries = GfiUsers.objects(github_login=user_name).first().user_queries
            actual_queries = []
            query_filter = request.args.get("filter")
            for query in user_queries:
                actual_query = GfiQueries.objects(
                    Q(name=query.repo) & Q(owner=query.owner)
                ).first()
                if actual_query:
                    actual_queries.append(actual_query)
            pending_queries = list(
                filter(lambda query: query.is_pending, [q for q in actual_queries])
            )
            finished_queries = list(
                filter(lambda query: query.is_finished, [q for q in actual_queries])
            )

            if query_filter != None and query_filter in REPO_FILTER_TYPES:
                if query_filter == "popularity":
                    finished_queries.sort(key=cmp_to_key(repo_stars_comp))
                elif query_filter == "median_issue_resolve_time":
                    finished_queries.sort(
                        key=cmp_to_key(query_median_issue_resolve_time_comp)
                    )
                elif query_filter == "newcomer_friendly":
                    finished_queries.sort(key=cmp_to_key(repo_newcomer_resolved_camp))
                elif query_filter == "gfis":
                    finished_queries.sort(key=cmp_to_key(repo_gfi_num_camp))

            return {
                "code": 200,
                "result": {
                    "nums": len(pending_queries) + len(finished_queries),
                    "queries": get_user_query(pending_queries),
                    "finished_queries": get_user_query(finished_queries),
                },
            }
        elif method == "DELETE":
            name = request.args.get("name")
            owner = request.args.get("owner")
            user_queries = GfiUsers.objects(github_login=user_name).first().user_queries
            if name != None and owner != None:
                for query in user_queries:
                    if query.repo == name and query.owner == owner:
                        user_queries.remove(query)
                        GfiUsers.objects(github_login=user_name).update(
                            user_queries=user_queries
                        )
                        return {"code": 200, "result": "success"}
                return {"code": 200, "result": "delete query successfully"}
            else:
                return {"code": 400, "result": "no query name or owner provided"}
    return {"code": 404, "result": "user not found"}


@app.route("/api/user/searches", methods=["GET", "DELETE"])
def get_user_searches():
    method = request.method
    github_login = request.args.get("user")
    user_searches = GfiUsers.objects(github_login=github_login).first().user_searches

    def get_search_result(searches):
        return [
            {
                "name": search.repo,
                "owner": search.owner,
                "created_at": search.created_at,
                "increment": search.increment,
            }
            for search in searches
        ]

    if user_searches != None:
        if method == "GET":
            return {"code": 200, "result": get_search_result(user_searches)}
        elif method == "DELETE":
            id = request.args.get("id")
            if id != None:
                """delete user search with increment = id"""
                GfiUsers.objects(github_login=github_login).update_one(
                    pull__user_searches__increment=int(id)
                )
                user_searches = (
                    GfiUsers.objects(github_login=github_login).first().user_searches
                )
                return {"code": 200, "result": get_search_result(user_searches)}
            else:
                return {"code": 404, "result": "id not found"}
    else:
        return {"code": 404, "result": "user not found"}


@app.route("/api/github/app/installation")
def github_app_install():
    code = request.args.get("code")
    return github_login_redirect(name=GITHUB_APP_NAME, code=code)


def update_repository_gfi_info(task_id: str, owner: str, repo: str):
    update_gfi_update_job(daemon_scheduler, task_id, repo, owner)


def get_owner_and_name_form_github_request(repository: Dict):
    repo_full_name = repository["full_name"]
    repo_name = repository["name"]
    last_idx = repo_full_name.rfind("/")
    owner = repo_full_name[:last_idx]
    return owner, repo_name


def add_repo_from_github_app(user_collection, repositories):
    repo_info = []
    for repo in repositories:
        owner, repo_name = get_owner_and_name_form_github_request(repo)
        repo_info.append(
            {
                "name": repo_name,
                "owner": owner,
            }
        )

        queries = [[q.repo, q.owner] for q in user_collection.user_queries]
        if [repo_name, owner] not in queries:
            user_collection.update(
                push__user_queries={
                    "repo": repo_name,
                    "owner": owner,
                    "created_at": datetime.utcnow(),
                }
            )

        if len(GfiQueries.objects(Q(name=repo_name) & Q(owner=owner))) == 0:
            GfiQueries(
                name=repo_name,
                owner=owner,
                is_pending=True,
                is_finished=False,
                is_updating=False,
                _created_at=datetime.utcnow(),
            ).save()
    user_token = user_collection.github_app_token
    if user_token:
        executor.submit(update_repos, user_token, repo_info)


def delete_repo_from_github_app(repositories):
    for repo in repositories:
        owner, repo_name = get_owner_and_name_form_github_request(repo)
        delete_repo_from_query(owner, repo_name)


@app.route("/api/github/actions/webhook", methods=["POST"])
def github_app_webhook_process():
    """
    Process Github App webhook
    """
    event = request.headers.get("X-Github-Event")
    data = request.get_json()

    sender_id = data["sender"]["id"]
    user_collection = GfiUsers.objects(github_id=sender_id).first()

    if user_collection:
        if event == "installation":
            action = data["action"]
            if action == "created":
                repositories = data["repositories"]
                add_repo_from_github_app(user_collection, repositories)
            elif action == "deleted":
                repositories = data["repositories"]
                delete_repo_from_github_app(repositories)
            elif action == "suspend":
                repositories = data["repositories"]
                delete_repo_from_github_app(repositories)
            elif action == "unsuspend":
                add_repo_from_github_app(user_collection, repositories)
        elif event == "installation_repositories":
            action = data["action"]
            if action == "added":
                repositories = data["repositories_added"]
                add_repo_from_github_app(user_collection, repositories)
            elif action == "removed":
                repositories = data["repositories_removed"]
                delete_repo_from_github_app(repositories)
        elif event == "issues":
            action = data["action"]
        return {"code": 200, "result": "callback succeed for event {}".format(event)}
    else:
        return {"code": 404, "result": "user not found"}


@app.route("/api/repo/badge")
def get_repo_badge():
    """
    Generate GitHub README badge for certain repository
    """
    owner = request.args.get("owner")
    name = request.args.get("name")
    if owner != None and name != None:
        query = Repo.objects(Q(name=name) & Q(owner=owner))
        if len(query):
            gfi_num = Prediction.objects(
                Q(name=name) & Q(owner=owner) & Q(probability__gte=0.5)
            ).count()
            img_src = "https://img.shields.io/badge/{}-{}-{}".format(
                "good first issues", gfi_num, "success"
            )
            svg = requests.get(img_src).content
            return app.response_class(svg, mimetype="image/svg+xml")
        else:
            abort(404)
    else:
        abort(400)
