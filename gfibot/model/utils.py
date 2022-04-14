import pandas as pd
import numpy as np
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score
from sklearn.metrics import roc_curve
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import sys

current_work_dir = os.path.dirname(__file__)
utpath = os.path.join(current_work_dir, "../..")
sys.path.append(utpath)
from gfibot.collections import *


def cat_comment(comment: list) -> str:
    if comment == []:
        return ""
    else:
        return "".join(comment)


def get_TFIDF(text: list) -> np.array:
    text_TFIDF = (
        TfidfVectorizer(
            analyzer="word", input="content", stop_words="english", max_features=50
        )
        .fit_transform(text)
        .toarray()
    )
    return text_TFIDF


def user_new(cmt_num: int, new_threshold: int) -> int:
    if cmt_num < new_threshold:
        return 1
    return 0


def get_ratio(lst: list, new_threshold: int) -> float:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < new_threshold for d in lst)
        nnum = len(lst) - pnum
        return pnum / (pnum + nnum)


def get_num(lst: list, new_threshold: int) -> int:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < new_threshold for d in lst)
        return pnum


def get_user_average(user_list: List[Dataset.UserFeature], new_threshold: int):
    user_num = len(user_list)
    commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num = 0, 0, 0, 0, 0
    if user_num != 0:
        for user in user_list:
            commits_num += user.n_commits
            issues_num += user.n_issues
            pulls_num += user.n_pulls
            user_gfi_ratio += get_ratio(user.resolver_commits, new_threshold)
            user_gfi_num += get_num(user.resolver_commits, new_threshold)
        commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num = (
            commits_num / user_num,
            issues_num / user_num,
            pulls_num / user_num,
            user_gfi_ratio / user_num,
            user_gfi_num / user_num,
        )
    return commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num


def load_data(new_threshold: int, owner=None, name=None) -> pd.DataFrame:
    """Retrieve data frome gfibot.dataset for each issue to further build training data set and test data set with def(load_train_test_data) or training data set with def(load_train_data)"""
    issue_list = []
    if owner is None:
        for issue in Dataset.objects():
            issue_list.append(get_issue_data(issue, new_threshold))
    else:
        for issue in Dataset.objects(owner=owner, name=name):
            issue_list.append(get_issue_data(issue, new_threshold))
    issue_df = pd.DataFrame(issue_list)

    # ---------- TFIDF of issue title, body and comments ----------
    title_TFIDF = pd.DataFrame(get_TFIDF(issue_df["title"].values))
    body_TFIDF = pd.DataFrame(get_TFIDF(issue_df["body"].values))
    comments_TFIDF = pd.DataFrame(get_TFIDF(issue_df["comments"].values))
    del issue_df["title"]
    del issue_df["body"]
    del issue_df["comments"]
    column_name = list(issue_df.columns)
    issue_df = pd.concat([issue_df, title_TFIDF, body_TFIDF, comments_TFIDF], axis=1)
    column_name.extend(["TFIDF" + str(i) for i in range(150)])
    issue_df.columns = column_name
    return issue_df


def get_issue_data(issue: Dataset, new_threshold: int) -> dict:
    is_gfi = user_new(issue.resolver_commit_num, new_threshold)

    comments = cat_comment(issue.comments)

    rpt_is_new = user_new(issue.reporter_feat.n_commits, new_threshold)
    rpt_gfi_ratio = get_ratio(issue.reporter_feat.resolver_commits, new_threshold)
    owner_gfi_ratio = get_ratio(issue.owner_feat.resolver_commits, new_threshold)
    owner_gfi_num = get_num(issue.owner_feat.resolver_commits, new_threshold)
    pro_gfi_ratio = get_ratio(issue.prev_resolver_commits, new_threshold)
    pro_gfi_num = get_num(issue.prev_resolver_commits, new_threshold)

    (
        commenter_commits_num,
        commenter_issues_num,
        commenter_pulls_num,
        commenter_gfi_ratio,
        commenter_gfi_num,
    ) = get_user_average(
        issue.comment_users, new_threshold
    )  # 原commentuser
    (
        eventer_commits_num,
        eventer_issues_num,
        eventer_pulls_num,
        eventer_gfi_ratio,
        eventer_gfi_num,
    ) = get_user_average(
        issue.event_users, new_threshold
    )  # eventer
    comment_num = len(issue.comments)
    event_num = len(issue.events)

    one_issue = {
        "owner": issue.owner,
        "name": issue.name,
        "number": issue.number,
        "is_gfi": is_gfi,
        # ---------- Content ----------
        "title": issue.title,
        "body": issue.body,
        "len_title": issue.len_title,
        "len_body": issue.len_body,
        "n_code_snips": issue.n_code_snips,
        "n_urls": issue.n_urls,
        "n_imgs": issue.n_urls,
        "coleman_liau_index": issue.coleman_liau_index,
        "flesch_reading_ease": issue.flesch_reading_ease,
        "flesch_kincaid_grade": issue.flesch_kincaid_grade,
        "automated_readability_index": issue.automated_readability_index,
        "bug_num": issue.label_category.bug,
        "feature_num": issue.label_category.feature,
        "test_num": issue.label_category.test,
        "build_num": issue.label_category.build,
        "doc_num": issue.label_category.doc,
        "coding_num": issue.label_category.coding,
        "enhance_num": issue.label_category.enhance,
        "gfi_num": issue.label_category.gfi,
        "medium_num": issue.label_category.medium,
        "major_num": issue.label_category.major,
        "triaged_num": issue.label_category.triaged,
        "untriaged_num": issue.label_category.untriaged,
        # ---------- Background ----------
        "rpt_is_new": rpt_is_new,
        "rpt_gfi_ratio": rpt_gfi_ratio,
        "owner_gfi_ratio": owner_gfi_ratio,
        "owner_gfi_num": owner_gfi_num,
        "pro_gfi_ratio": pro_gfi_ratio,
        "pro_gfi_num": pro_gfi_num,
        "n_stars": issue.n_stars,
        "n_pulls": issue.n_pulls,
        "n_commits": issue.n_commits,
        "n_contributors": issue.n_contributors,
        "n_closed_issues": issue.n_closed_issues,
        "n_open_issues": issue.n_open_issues,
        "r_open_issues": issue.r_open_issues,
        "issue_close_time": issue.issue_close_time,
        # ---------- Dynamics ----------
        "comments": comments,
        "commenter_commits_num": commenter_commits_num,
        "commenter_issues_num": commenter_issues_num,
        "commenter_pulls_num": commenter_pulls_num,
        "commenter_gfi_ratio": commenter_gfi_ratio,
        "commenter_gfi_num": commenter_gfi_num,
        "eventer_commits_num": eventer_commits_num,
        "eventer_issues_num": eventer_issues_num,
        "eventer_pulls_num": eventer_pulls_num,
        "eventer_gfi_ratio": eventer_gfi_ratio,
        "eventer_gfi_num": eventer_gfi_num,
        "comment_num": comment_num,
        "event_num": event_num,
    }

    return one_issue


def load_train_data(data: pd.DataFrame, settype: str, owner: str, name: str):
    if settype == "one4one":
        train_data = data.loc[(data["owner"] == owner) & (data["name"] == name)]
        test_data = data.loc[(data["owner"] == owner) & (data["name"] == name)]
    else:
        train_data = data
        test_data = data.loc[(data["owner"] == owner) & (data["name"] == name)]

    p_train = train_data[train_data.is_gfi == 1]
    n_train = train_data[train_data.is_gfi == 0]
    n_train = n_train.sample(
        frac=p_train.shape[0] / n_train.shape[0], replace=True, random_state=0
    )

    train_data = pd.concat([p_train, n_train], ignore_index=True)
    train_data = train_data.sample(frac=1, random_state=0)
    y_train = train_data["is_gfi"]

    train_data.drop(["is_gfi", "owner", "name", "number"], axis=1, inplace=True)
    test_data.drop(["is_gfi", "owner", "name"], axis=1, inplace=True)

    X_train = train_data
    X_test = test_data
    return X_train, X_test, y_train


def load_train_test_data(data: pd.DataFrame, settype: str, owner: str, name: str):
    if settype == "one4one":
        pro_data = data.loc[(data["owner"] == owner) & (data["name"] == name)]
        p_train_split = int(0.9 * pro_data.shape[0])
        train_data = pro_data.iloc[:p_train_split]
        test_data = pro_data.iloc[p_train_split + 1 :]
    elif settype == "all4one":
        pro_data = data.loc[(data["owner"] == owner) & (data["name"] == name)]
        pro_data = pro_data.reset_index(drop=True)
        data = data.reset_index(drop=True)

        p_train_split = int(0.9 * pro_data.shape[0])
        test_data = pro_data.iloc[p_train_split + 1 :]
        test_data = test_data.reset_index(drop=True)
        owner = test_data.loc[0, "owner"]
        name = test_data.loc[0, "name"]
        number = test_data.loc[0, "number"]
        ind = data[
            (data["owner"] == owner)
            & (data["name"] == name)
            & (data["number"] == number)
        ].index.tolist()[0]
        train_data = data.iloc[:ind]
    else:
        p_train_split = int(0.9 * data.shape[0])
        train_data = data.iloc[:p_train_split]
        test_data = data.iloc[p_train_split + 1 :]

    p_train = train_data[train_data.is_gfi == 1]
    n_train = train_data[train_data.is_gfi == 0]
    n_train = n_train.sample(
        frac=p_train.shape[0] / n_train.shape[0], replace=True, random_state=0
    )

    train_data = pd.concat([p_train, n_train], ignore_index=True)
    train_data = train_data.sample(frac=1, random_state=0)
    y_train = train_data["is_gfi"]
    y_test = test_data["is_gfi"]

    train_data = train_data.drop(["is_gfi", "owner", "name", "number"], axis=1)
    test_data = test_data.drop(["is_gfi", "owner", "name", "number"], axis=1)
    X_train = train_data
    X_test = test_data
    return X_train, X_test, y_train, y_test


def get_all_metrics(y_test: pd.Series, pred_labels: np.array, y_prob: np.array):
    fpr, tpr, thresholds_keras = roc_curve(y_test, y_prob)
    auc = auc(fpr, tpr)
    precision = precision_score(y_test, pred_labels)
    recall = recall_score(y_test, pred_labels)
    f1 = f1_score(y_test, pred_labels)
    return auc, precision, recall, f1
