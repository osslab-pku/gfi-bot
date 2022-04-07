import pymongo
import collections
from datetime import datetime
from typing import Dict

from typing import Final

MONGO_URI: Final = "mongodb://localhost:27017/"

db_issue_dataset: Final = "issuedataset"
db_issues: Final = "issues"
db_repos: Final = "repos"
db_repos_commits: Final = "repos.commits"
db_repos_issues: Final = "repos.issues"
db_repos_stars: Final = "repos.stars"

db_client = pymongo.MongoClient(MONGO_URI)
gfi_db = db_client["gfi-bot"]


def generate_update_msg(dict: Dict) -> Dict:
    return {"$set": dict}


def update_repo_info_for_action(
    name: str, collection_name: str, source_key_name: str, target_key_name: str
):

    filter = {"name": name}
    dataset = gfi_db.get_collection(collection_name).find(filter)
    res = {}
    for data in dataset:
        action_time: datetime = data[source_key_name]
        key = datetime(year=action_time.year, month=action_time.month, day=1)
        if key in res:
            res[key] += 1
        else:
            res[key] = 1

    res = collections.OrderedDict(sorted(res.items()))
    montly_target_info = []
    for key in res:
        montly_target_info.append(
            {
                "month": key,
                "count": res[key],
            }
        )

    repo_collection = gfi_db.get_collection(db_repos)
    repo_collection.update_many(
        filter, generate_update_msg({target_key_name: montly_target_info})
    )


def detailed_repo_stars(name: str):

    update_repo_info_for_action(
        name=name,
        collection_name=db_repos_stars,
        source_key_name="starred_at",
        target_key_name="monthly_stars",
    )


def detailed_repo_commits(name: str):

    update_repo_info_for_action(
        name=name,
        collection_name=db_repos_commits,
        source_key_name="committed_at",
        target_key_name="monthly_commits",
    )


def detailed_repo_issues(name: str):

    update_repo_info_for_action(
        name=name,
        collection_name=db_repos_issues,
        source_key_name="created_at",
        target_key_name="monthly_issues",
    )


if __name__ == "__main__":

    repos = gfi_db.get_collection(db_repos)
    for i, temp in enumerate(repos.find()):
        detailed_repo_stars(temp["name"])
        detailed_repo_commits(temp["name"])
        detailed_repo_issues(temp["name"])
