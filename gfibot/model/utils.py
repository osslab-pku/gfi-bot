import pandas as pd
import numpy as np
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
import os
import sys
import math
import xgboost as xgb
from mongoengine.queryset.visitor import Q

current_work_dir = os.path.dirname(__file__)
utpath = os.path.join(current_work_dir, "../..")
sys.path.append(utpath)
from gfibot.collections import *


def cat_comment(comment: list) -> str:
    if comment == []:
        return ""
    else:
        return "".join(comment)


def user_new(cmt_num: int, threshold: int) -> int:
    if cmt_num < threshold:
        return 1
    return 0


def get_ratio(lst: list, threshold: int) -> float:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < threshold for d in lst)
        nnum = len(lst) - pnum
        return pnum / (pnum + nnum)


def get_num(lst: list, threshold: int) -> int:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < threshold for d in lst)
        return pnum


def get_user_average(user_list: List[Dataset.UserFeature], threshold: int):
    user_num = len(user_list)
    commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num = 0, 0, 0, 0, 0
    if user_num != 0:
        for user in user_list:
            commits_num += user.n_commits
            issues_num += user.n_issues
            pulls_num += user.n_pulls
            user_gfi_ratio += get_ratio(user.resolver_commits, threshold)
            user_gfi_num += get_num(user.resolver_commits, threshold)
        commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num = (
            commits_num / user_num,
            issues_num / user_num,
            pulls_num / user_num,
            user_gfi_ratio / user_num,
            user_gfi_num / user_num,
        )
    return commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num


def load_data(threshold: int, batch: List[list]) -> pd.DataFrame:
    issue_list = []
    for issue in batch:
        query = Q(owner=issue[1], name=issue[0], number=issue[2][0], before=issue[2][1])
        one_issue = Dataset.objects(query).first()
        issue_list.append(get_issue_data(one_issue, threshold))
    issue_df = pd.DataFrame(issue_list)
    return issue_df


def get_issue_data(issue: list, threshold: int) -> dict:
    is_gfi = user_new(issue.resolver_commit_num, threshold)

    rpt_is_new = user_new(issue.reporter_feat.n_commits, threshold)
    rpt_gfi_ratio = get_ratio(issue.reporter_feat.resolver_commits, threshold)
    owner_gfi_ratio = get_ratio(issue.owner_feat.resolver_commits, threshold)
    owner_gfi_num = get_num(issue.owner_feat.resolver_commits, threshold)
    pro_gfi_ratio = get_ratio(issue.prev_resolver_commits, threshold)
    pro_gfi_num = get_num(issue.prev_resolver_commits, threshold)

    (
        commenter_commits_num,
        commenter_issues_num,
        commenter_pulls_num,
        commenter_gfi_ratio,
        commenter_gfi_num,
    ) = get_user_average(issue.comment_users, threshold)
    (
        eventer_commits_num,
        eventer_issues_num,
        eventer_pulls_num,
        eventer_gfi_ratio,
        eventer_gfi_num,
    ) = get_user_average(issue.event_users, threshold)
    comment_num = len(issue.comments)
    event_num = len(issue.events)

    one_issue = {
        "owner": issue.owner,
        "name": issue.name,
        "number": issue.number,
        "is_gfi": is_gfi,
        # ---------- Content ----------
        # "title": issue.title,
        # "body": issue.body,
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
        # "comments": comments,
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


def update_model(
    model_path: str, threshold: int, train_add: list, batch_size: int
) -> xgb.core.Booster:
    ith_batch = 0
    while ith_batch < math.ceil(len(train_add) / batch_size):
        train_batch = train_add[ith_batch * batch_size : (ith_batch + 1) * batch_size]
        model_path = train_incremental(threshold, model_path, train_batch)
        ith_batch += 1
    model = model_path
    if ith_batch == 0:
        model = xgb.Booster()
        model.load_model(model_path)
    return model


def train_incremental(
    threshold: int, model_path: str, train_batch: list
) -> xgb.core.Booster:
    params = {"objective": "binary:logistic"}
    data = load_data(threshold, train_batch)
    X_train, y_train = load_train_data(data)
    if len(X_train) == 0:
        return model_path
    else:
        xg_train = xgb.DMatrix(X_train, label=y_train)
        return xgb.train(params, xg_train, xgb_model=model_path)


def load_train_data(data: pd.DataFrame):
    p_train = data[data["is_gfi"] == 1]
    n_train = data[data["is_gfi"] == 0]
    n_train = n_train.sample(
        frac=p_train.shape[0] / n_train.shape[0], replace=True, random_state=0
    )
    data = pd.concat([p_train, n_train], ignore_index=True)
    y_train = data["is_gfi"]
    X_train = data.drop(["is_gfi", "owner", "name", "number"], axis=1)
    return X_train, y_train


def load_test_incremental(test_set: List[int], threshold: int):
    data = load_data(threshold, test_set)
    y_test = data["is_gfi"]
    X_test = data.drop(["is_gfi", "owner", "name"], axis=1)
    return X_test, y_test


def predict_issues(
    test_set: List[int], threshold: int, batch_size: int, model: xgb.core.Booster
):
    ith_batch = 0
    y_test_all, y_prob_all = [], []
    while ith_batch < math.ceil(len(test_set) / batch_size):
        test_batch = test_set[ith_batch * batch_size : (ith_batch + 1) * batch_size]
        X_test, y_test = load_test_incremental(test_batch, threshold)
        del X_test["number"]
        xg_test = xgb.DMatrix(X_test, label=y_test)
        y_prob = model.predict(xg_test)
        y_test_all += list(y_test)
        y_prob_all += list(y_prob)
        ith_batch += 1
    return y_test_all, y_prob_all


def get_all_metrics(y_test: List[int], pred_labels: List[int], y_prob: List[float]):
    fpr, tpr, thresholds_keras = roc_curve(y_test, y_prob)
    auc_ = auc(fpr, tpr)
    precision = precision_score(y_test, pred_labels)
    recall = recall_score(y_test, pred_labels)
    f1 = f1_score(y_test, pred_labels)
    return auc_, precision, recall, f1
