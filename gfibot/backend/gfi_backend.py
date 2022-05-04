from flask import Flask, redirect, request, abort
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests

import pymongo
import json
from bson import ObjectId
from datetime import datetime, date
from urllib import parse
import numpy as np

from typing import Dict, Final

import urllib.parse

import yagmail

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from gfibot.collections import *
from gfibot.data.update import update_repo

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

executor = ThreadPoolExecutor(max_workers=10)

if app.debug:
    app.logger.info("enable CORS")
    CORS(app, supports_credentials=True)

MONGO_URI: Final = "mongodb://localhost:27017/"
db_client = pymongo.MongoClient(MONGO_URI)
gfi_db = db_client["gfibot"]
db_gfi_email: Final = "gmail-email"


def generate_update_msg(dict: Dict) -> Dict:
    return {"$set": dict}


class JSONEncoder(json.JSONEncoder):
    """
    A Modified JSON Encoder
    Deal with datatypes that can't be encoded by default
    """

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


@app.route("/api/repos/num")
def get_repo_num():
    language = request.args.get("lang")
    repos = Repo.objects()
    res = 0
    if language != None:
        res = len(Repo.objects(language=language))
    else:
        res = len(repos)
    return {"code": 200, "result": res}


def get_month_count(mounth_counts):
    return [
        {
            "month": item.month,
            "count": item.count,
        }
        for item in mounth_counts
    ]


def get_repo_info_from_engine(repo):
    return {
        "name": repo.name,
        "owner": repo.owner,
        "description": repo.description,
        "language": repo.language,
        "topics": repo.topics,
        "monthly_stars": get_month_count(repo.monthly_stars),
        "monthly_commits": get_month_count(repo.monthly_commits),
        "monthly_issues": get_month_count(repo.monthly_issues),
        "monthly_pulls": get_month_count(repo.monthly_pulls),
    }


@app.route("/api/repos/detail_info_name")
def get_repo_detail_info_by_name():

    repo_name = request.args.get("name")
    repo_owner = request.args.get("owner")
    repos = Repo.objects(Q(name=repo_name) & Q(owner=repo_owner))
    if len(repos):
        repo = repos[0]
        return {"code": 200, "result": get_repo_info_from_engine(repo)}
    return {"code": 404, "result": "repo not found"}


REPO_FILTER_TYPES = ["None", "Popularity", "Activity", "Recommended", "Time"]


@app.route("/api/repos/detailed_info")
def get_repo_detailed_info():
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
            repos_query = Repo.objects(language=lang)
            count = len(repos_query)
        else:
            repos_query = Repo.objects()
            count = len(repos_query)

        start_idx = max(0, start_idx)
        req_size = min(req_size, count)
        res = []
        if start_idx < count:
            for i, repo in enumerate(repos_query):
                if i >= start_idx and i - start_idx < req_size:
                    res.append(get_repo_info_from_engine(repo))
        return {
            "code": 200,
            "result": res,
        }
    else:
        abort(400)


@app.route("/api/repos/info")
def get_repo_info_by_name_or_url():
    repo_name = request.args.get("repo")
    repo_url = parse.unquote(request.args.get("url"))
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
            repo = repos_query[0]
            return {"code": 200, "result": get_repo_info_from_engine(repo)}
        elif repo_url == "":
            return {"code": 404, "result": "Repo not found"}

    else:
        abort(400)


@app.route("/api/repos/language")
def get_deduped_repo_languages():
    languages = Repo.objects().distinct(field="language")
    return {"code": 200, "result": languages}


GITHUB_LOGIN_URL: Final = "https://github.com/login/oauth/authorize"


@app.route("/api/user/github/login")
def github_login():
    """
    Process Github OAuth login procedure
    """
    client_id = GithubTokens.objects().first().client_id
    return {"code": 200, "result": GITHUB_LOGIN_URL + "?client_id=" + client_id}


@app.route("/api/repos/recommend")
def get_recommend_repo():
    """
    get recommened repo name (currently using random)
    """
    repos = Repo.objects()
    res = np.random.choice(repos, size=1).tolist()[0]
    return {"code": 200, "result": get_repo_info_from_engine(res)}


@app.route("/api/issue/num")
def get_issue_num():
    issues = OpenIssue.objects()
    return {"code": 200, "result": len(issues)}


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


@app.route("/api/issue/gfi")
def get_issue_info():
    """
    get random issues by repo name
    """
    repo_name = request.args.get("repo")
    repo_owner = request.args.get("owner")
    if repo_name != None and repo_owner != None:
        gfi_list = Prediction.objects(Q(name=repo_name) & Q(owner=repo_owner)).order_by(
            "-probability"
        )
        res = get_predicted_info_from_engine(gfi_list)[0 : min(5, len(gfi_list))]
        if len(gfi_list):
            return {
                "code": 200,
                "result": res,
            }
        else:
            return {"code": 404, "result": "repo not found"}
    else:
        abort(400)


@app.route("/api/user/github/callback")
def github_login_redirect():
    """
    Process Github OAuth callback procedure
    """
    code = request.args.get("code")

    client_id = GithubTokens.objects().first().client_id
    client_secret = GithubTokens.objects().first().client_secret

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
            access_token = res_dict["access_token"]
            if access_token != None:
                r = requests.get(
                    "https://api.github.com/user",
                    headers={"Authorization": "token " + access_token},
                )
                if r.status_code == 200:
                    user_res = json.loads(r.text)
                    if len(GfiUsers.objects(github_id=user_res["id"])) == 0:
                        new_user_data = GfiUsers(
                            github_id=user_res["id"],
                            github_login=user_res["login"],
                            github_name=user_res["name"],
                            github_avatar_url=user_res["avatar_url"],
                            github_access_token=access_token,
                            github_email=user_res["email"],
                            github_url=user_res["url"],
                            twitter_user_name=user_res["twitter_username"],
                        )
                        new_user_data.save()
                    else:
                        GfiUsers.objects(github_id=user_res["id"]).update_one(
                            set__github_access_token=access_token,
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
                repo_info = {
                    "name": repo_name,
                    "owner": repo_owner,
                }
                queries = [
                    {
                        "name": query.name,
                        "owner": query.owner,
                    }
                    for query in GfiQueries.objects()
                ]
                if repo_info not in queries:
                    new_query = GfiQueries(
                        name=repo_name,
                        owner=repo_owner,
                        user_github_login=user_name,
                        is_pending=True,
                        is_finished=False,
                        _created_at=datetime.utcnow(),
                    )
                    new_query.save()
                    executor.submit(update_repo, user_token, repo_owner, repo_name)
                    return {"code": 200, "result": "is being processed by GFI-Bot"}
                else:
                    return {"code": 200, "result": "already exists"}
        return {"code": 400, "result": "Bad request"}
    else:
        return {"code": 404, "result": "user not found"}


@app.route("/api/user/queries")
def get_user_queries():
    def get_user_query(queries):
        return [
            {
                "name": query.name,
                "owner": query.owner,
                "user_github_login": query.user_github_login,
                "is_pending": query.is_pending,
                "is_finished": query.is_finished,
                "created_at": query._created_at,
                "finished_at": query._finished_at,
            }
            for query in queries
        ]

    user_name = request.args.get("user")
    if user_name != None:
        queries = GfiQueries.objects(user_github_login=user_name)
        pending_queries = list(
            filter(lambda query: query.is_pending, [q for q in queries])
        )
        finished_queries = list(
            filter(lambda query: query.is_finished, [q for q in queries])
        )
        return {
            "code": 200,
            "result": {
                "nums": len(pending_queries) + len(finished_queries),
                "queries": get_user_query(pending_queries),
                "finished_queries": get_user_query(finished_queries),
            },
        }
    return {"code": 404, "result": "user not found"}


def fetch_repo_gfi(repo_url, github_name):
    ### TODO: To Be Completed
    None


def send_email(user_github_id, subject, body):
    """
    Send email to user
    """

    app.logger.info("send email to user {}".format(user_github_id))

    user_email = GfiUsers.objects(github_id=user_github_id).first().github_email

    email = gfi_db.get_collection(db_gfi_email).find_one({})["email"]
    password = gfi_db.get_collection(db_gfi_email).find_one({})["password"]

    app.logger.info("Sending email to {} using {}".format(user_email, email))

    if user_email != None:
        yag = yagmail.SMTP(email, password)
        yag.send(user_email, subject, body)
        yag.close()


# using websocket to handle user query


@socketio.on("connect", namespace="/gfi_process")
def connect_gfi_process():
    """
    Process socketio connection
    """
    app.logger.info("gfi_process connected")
    emit("socket_connected", {"data": "Connected"})


@socketio.on("disconnect", namespace="/gfi_process")
def disconnect_gfi_process():
    """
    Process socketio disconnection
    """
    app.logger.info("gfi_process disconnected")


if __name__ == "__main__":
    socketio.run(app, debug=True)
