import os
import math
import shutil
import logging
import argparse
import mongoengine
import pandas as pd
import xgboost as xgb

from typing import Tuple
from datetime import datetime
from dateutil.parser import parse as parse_date
from gfibot import CONFIG
from gfibot.model import utils
from gfibot.collections import *
from sklearn.metrics import accuracy_score


logger = logging.getLogger(__name__)
MODEL_ROOT_DIRECTORY = "models"
os.makedirs(MODEL_ROOT_DIRECTORY, exist_ok=True)


def model_90_path(threshold: int) -> str:
    return f"{MODEL_ROOT_DIRECTORY}/model_90_{threshold}.model"


def model_full_path(threshold: int) -> str:
    return f"{MODEL_ROOT_DIRECTORY}/model_full_{threshold}.model"


def get_update_set(
    threshold: int, dataset_batch: List[Dataset]
) -> Tuple[str, str, list]:  # name, owner, number, before
    update_set = []
    for i in dataset_batch:
        if i.resolver_commit_num == -1:
            continue
        query = Q(name=i.name, owner=i.owner, threshold=threshold)
        repo = TrainingSummary.objects(query)
        if repo.count() == 0:
            logger.info("Repo not found in database, creating...")
            repo = TrainingSummary(
                owner=i.owner,
                name=i.name,
                threshold=threshold,
                issues_train=[],
                issues_test=[],
                n_resolved_issues=0,
                n_newcomer_resolved=0,
                batch_accuracy=[],
                batch_auc=[],
                last_updated=datetime.now(),
            )
            repo.save()
        else:
            repo = repo.first()

        train_set = repo.issues_train
        test_set = repo.issues_test
        issue_set = train_set + test_set
        issue_number_set = [iss[0] for iss in issue_set]
        if i.number in issue_number_set:
            logger.info(f"{i.owner}/{i.name}#{i.number}: no need to update")
            continue
        else:
            update_set.append((i.name, i.owner, [i.number, i.before]))
            logger.info(f"{i.owner}/{i.name}#{i.number}: added")
    return update_set


def update_basic_training_summary(
    update_set: Tuple[str, str, list],
    min_test_size: int,
    threshold: int,
) -> List[Tuple[str, str, list]]:
    train_90_add = []
    for i in TrainingSummary.objects(threshold=threshold):
        update_issues = [
            [a[2][0], a[2][1]] for a in update_set if a[0] == i.name and a[1] == i.owner
        ]
        if update_issues == []:
            continue
        else:
            train_set, test_set = i.issues_train, i.issues_test
            prev_len_train, prev_len_test = len(train_set), len(test_set)

            count = 0
            for iss in update_issues:
                if len(test_set) < min_test_size:
                    test_set.append(iss)
                elif len(train_set) < 9 * min_test_size:
                    train_set.append(iss)
                    train_set.append(iss)
                    train_90_add.append((i.name, i.owner, iss))
                else:
                    test_set.append(iss)
                    if count == 9:
                        count = 0
                        continue
                    else:
                        train_set.append(test_set[0])
                        train_90_add.append((i.name, i.owner, test_set[0]))
                        test_set.pop(0)
                        count += 1

                query = Q(owner=i.owner, name=i.name, number=iss[0], before=iss[1])
                issue = Dataset.objects(query).first()
                i.n_resolved_issues += 1
                if issue.resolver_commit_num < threshold:
                    i.n_newcomer_resolved += 1

            i.issues_train = train_set
            i.issues_test = test_set
        i.save()
        logger.info(
            "%s/%s: train_set %d -> %d, test set %d -> %d",
            i.name,
            i.owner,
            prev_len_train,
            len(i.issues_train),
            prev_len_test,
            len(i.issues_test),
        )
    return train_90_add


def update_models(
    update_set: list, train_90_add: list, batch_size: int, threshold: int
) -> xgb.core.Booster:
    model_90 = utils.update_model(
        model_90_path(threshold) if os.path.exists(model_90_path(threshold)) else None,
        threshold,
        train_90_add,
        batch_size,
    )
    model_full = utils.update_model(
        model_full_path(threshold)
        if os.path.exists(model_full_path(threshold))
        else None,
        threshold,
        update_set,
        batch_size,
    )
    model_90.save_model(model_90_path(threshold))
    model_full.save_model(model_full_path(threshold))
    return model_90


def update_peformance_training_summary(
    model_90: xgb.core.Booster, batch_size: int, prob_thres: float, threshold: int
):
    test_set_all = []
    training_set_all = []
    n_resolved_issues_all, n_newcomer_resolved_all = 0, 0
    for i in TrainingSummary.objects(threshold=threshold):
        training_set_all.extend(i.issues_train)
        n_resolved_issues_all += i.n_resolved_issues
        n_newcomer_resolved_all += i.n_newcomer_resolved
        test_set = [[i.name, i.owner, iss] for iss in i.issues_test]
        test_set_all.extend(test_set)

        y_test, y_prob = utils.predict_issues(test_set, threshold, batch_size, model_90)
        y_pred = [int(i > prob_thres) for i in y_prob]

        if all(y == 1 for y in y_pred) or all(y == 0 for y in y_pred):
            logger.info(
                "Performance for %s/%s is undefined because of all-0 or all-1 labels",
                i.name,
                i.owner,
            )
            i.accuracy = i.auc = i.precision = i.recall = i.f1 = float("nan")
        else:
            i.auc, i.precision, i.recall, i.f1 = utils.get_all_metrics(
                y_test, y_pred, y_prob
            )
            i.accuracy = accuracy_score(y_test, y_pred)
        i.last_updated = datetime.utcnow()
        i.save()
        logger.info(
            "Performance for %s/%s (%d test issues): "
            "acc = %.4f, auc = %.4f, prec = %.4f, recall = %.4f, f1 = %.4f",
            i.owner,
            i.name,
            len(test_set),
            i.accuracy,
            i.auc,
            i.precision,
            i.recall,
            i.f1,
        )

    summ = TrainingSummary.objects(name="", owner="", threshold=threshold)
    if summ.count() == 0:
        summ = TrainingSummary(owner="", name="", threshold=threshold)
    else:
        summ = summ.first()

    summ.issues_train = training_set_all
    summ.issues_test = test_set_all
    summ.n_resolved_issues = n_resolved_issues_all
    summ.n_newcomer_resolved = n_newcomer_resolved_all

    y_test, y_prob = utils.predict_issues(test_set_all, threshold, batch_size, model_90)
    y_pred = [int(i > prob_thres) for i in y_prob]

    if all(y == 1 for y in y_pred) or all(y == 0 for y in y_pred):
        logger.info(
            "Performance is undefined because of all-0 or all-1 labels",
        )
        summ.accuracy = summ.auc = summ.precision = summ.recall = summ.f1 = float("nan")
    else:
        summ.auc, summ.precision, summ.recall, summ.f1 = utils.get_all_metrics(
            y_test, y_pred, y_prob
        )
        summ.accuracy = accuracy_score(y_test, y_pred)
    summ.last_updated = datetime.utcnow()
    summ.save()
    logger.info(
        "Overall Performance (%d test issues): "
        "acc = %.4f, auc = %.4f, prec = %.4f, recall = %.4f, f1 = %.4f",
        len(test_set_all),
        summ.accuracy,
        summ.auc,
        summ.precision,
        summ.recall,
        summ.f1,
    )


def update_patch_performance(
    ith_batch: int, model_90: xgb.core.Booster, batch_size: int, prob_thres: float, threshold: int
):
    test_set_all = []
    training_set_all = []
    n_resolved_issues_all, n_newcomer_resolved_all = 0, 0
    for i in TrainingSummary.objects(threshold=threshold):
        training_set_all.extend(i.issues_train)
        n_resolved_issues_all += i.n_resolved_issues
        n_newcomer_resolved_all += i.n_newcomer_resolved
        test_set = [[i.name, i.owner, iss] for iss in i.issues_test]
        test_set_all.extend(test_set)

        y_test, y_prob = utils.predict_issues(test_set, threshold, batch_size, model_90)
        y_pred = [int(i > prob_thres) for i in y_prob]

        if all(y == 1 for y in y_pred) or all(y == 0 for y in y_pred):
            logger.info(
                "Performance for %d th_batch of %s/%s is undefined because of all-0 or all-1 labels",
                ith_batch,
                i.name,
                i.owner,
            )
            accuracy = auc = precision = recall = f1 = float("nan")
        else:
            auc, precision, recall, f1 = utils.get_all_metrics(
                y_test, y_pred, y_prob
            )
            accuracy = accuracy_score(y_test, y_pred)

        batch_accuracy_list = i.batch_accuracy
        batch_auc_list = i.batch_auc
        batch_precision_list = i.batch_precision
        batch_recall_list = i.batch_recall
        batch_f1_list = i.batch_f1
        batch_accuracy_list.append(str(ith_batch)+ "th_batch: " +str(accuracy))
        batch_auc_list.append(str(ith_batch)+ "th_batch: " +str(auc))
        batch_precision_list.append(str(ith_batch)+ "th_batch: " +str(precision))
        batch_recall_list.append(str(ith_batch)+ "th_batch: " +str(recall))
        batch_f1_list.append(str(ith_batch)+ "th_batch: " +str(f1))
        i.batch_accuracy = batch_accuracy_list
        i.batch_auc = batch_auc_list
        i.batch_precision = batch_precision_list
        i.batch_recall = batch_recall_list
        i.batch_f1 = batch_f1_list
        i.last_updated = datetime.utcnow()
        i.save()
        logger.info(
            "Performance for %d th_batch of %s/%s (%d test issues): "
            "acc = %.4f, auc = %.4f, prec = %.4f, recall = %.4f, f1 = %.4f",
            ith_batch,
            i.owner,
            i.name,
            len(test_set),
            i.batch_accuracy,
            i.batch_auc,
            i.batch_precision,
            i.batch_recall,
            i.batch_f1,
        )

        
def update_training_summary(
    threshold: int,
    min_test_size=1,
    dataset_size=5000,
    batch_size=2500,
    prob_thres=0.5,
):
    """
    Under the condition that there are at least min_test_size test points for a repository, the ratio of training points and test points of the repository is maintained at 9:1.
    If the number of resolved issues of a repository is less than min_test_size, all issues in the repository are used as test samples.
    dataset_size:  How many issues are read from Dataset in one iteration
    batch_size: the maximum number of training points allowed to be added in one-step update of models.
    prob_thres: threshold to distinguish two classes.
    """
    dataset = Dataset.objects().order_by("before")
    ith_batch = 0
    need_update = False
    while ith_batch < math.ceil(dataset.count() / dataset_size):
        dataset_batch = dataset[
            ith_batch * dataset_size : (ith_batch + 1) * dataset_size
        ]
        update_set = get_update_set(threshold, dataset_batch)
        logger.info(
            str((ith_batch + 1) * dataset_size)
            + " issues in Dataset have been checked."
        )
        if update_set != []:
            train_90_add = update_basic_training_summary(
                update_set, min_test_size, threshold
            )
            model_90 = update_models(update_set, train_90_add, batch_size, threshold)
            need_update = True
            update_patch_performance(
                ith_batch, model_90, batch_size, prob_thres, threshold
            )
        ith_batch += 1
        logger.info("Model updated.")

        if need_update and model_90 is not None:
            update_peformance_training_summary(
                model_90, batch_size, prob_thres, threshold
            )
            logger.info("Performance on each project is updated.")
        else:
            logger.info("No need to update performance.")


def update_prediction_for_issue(issue: Dataset, threshold: int):
    model_full = xgb.Booster()
    model_full.load_model(model_full_path(threshold))
    issue_df = pd.DataFrame(utils.get_issue_data(issue, threshold), index=[0])
    y_test = issue_df["is_gfi"]
    X_test = issue_df.drop(["is_gfi", "owner", "name", "number"], axis=1)
    xg_test = xgb.DMatrix(X_test, label=y_test)
    y_prob = model_full.predict(xg_test)
    # print(xg_test)
    # print(y_prob)
    Prediction.objects(
        owner=issue.owner, name=issue.name, number=issue.number
    ).upsert_one(
        owner=issue.owner,
        name=issue.name,
        number=issue.number,
        threshold=threshold,
        probability=y_prob,
        last_updated=datetime.now(),
    )


def update_repo_prediction(owner: str, name: str):
    for threshold in [1, 2, 3, 4, 5]:
        for i in list(Dataset.objects(owner=owner, name=name, resolver_commit_num=-1)):
            update_prediction_for_issue(i, threshold)


def update_prediction(threshold: int):
    repos = [(r.owner, r.name) for r in Repo.objects()]
    for owner, name in repos:
        for i in list(Dataset.objects(owner=owner, name=name, resolver_commit_num=-1)):
            logger.info("Update prediction: %s/%s#%d", owner, name, i.number)
            update_prediction_for_issue(i, threshold)
    logger.info(
        "Get predictions for open issues under threshol Model updated"
        + str(threshold)
        + "."
    )


def update(cleanup=False):
    if cleanup:
        TrainingSummary.drop_collection()
        Prediction.drop_collection()
        shutil.rmtree(MODEL_ROOT_DIRECTORY)
        os.makedirs(MODEL_ROOT_DIRECTORY, exist_ok=True)
    for threshold in [1, 2, 3, 4, 5]:
        logger.info(
            "Update TrainingSummary and Prediction for threshold "
            + str(threshold)
            + "."
        )
        update_training_summary(threshold)
        update_prediction(threshold)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()

    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
    )

    update(args.cleanup)

    logger.info("Done!")
