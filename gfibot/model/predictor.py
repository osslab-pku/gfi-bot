import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
import os
import math
import logging
from datetime import datetime
from gfibot.model import utils
from gfibot.collections import *

logger = logging.getLogger(__name__)


def get_update_set(threshold: int, dataset_batch: List[Dataset]) -> list:
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
                model_90_file="",
                model_full_file="",
                issues_train=[],
                issues_test=[],
                n_resolved_issues=0,
                n_newcomer_resolved=0,
                accuracy=0,
                auc=0,
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
            logger.info(f"{i.owner}/{i.name}#{i.number}): no need to update")
            continue
        else:
            update_set.append([i.name, i.owner, [i.number, i.before]])
    return update_set


def update_basic_training_summary(
    update_set: list, min_test_size: int, threshold: int
) -> list:
    train_90_add = []
    for i in TrainingSummary.objects(threshold=threshold):
        update_issues = [
            [a[2][0], a[2][1]] for a in update_set if a[0] == i.name and a[1] == i.owner
        ]
        if update_issues == []:
            continue
        else:
            train_set = i.issues_train
            test_set = i.issues_test

            count = 0
            for iss in update_issues:
                if len(test_set) < min_test_size:
                    test_set.append(iss)
                elif len(train_set) < 9 * min_test_size:
                    train_set.append(iss)
                    train_set.append(iss)
                    train_90_add.append([i.name, i.owner, iss])
                else:
                    test_set.append(iss)
                    if count == 9:
                        count = 0
                        continue
                    else:
                        train_set.append(test_set[0])
                        train_90_add.append([i.name, i.owner, test_set[0]])
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
    return train_90_add


def update_models(
    update_set: list, train_90_add: list, batch_size: int, threshold: int
) -> xgb.core.Booster:
    model_90_path = TrainingSummary.objects(threshold=threshold)[0].model_90_file
    if model_90_path == "":
        model_90_path = None
    model_90 = utils.update_model(model_90_path, threshold, train_90_add, batch_size)
    model_full_path = TrainingSummary.objects(threshold=threshold)[0].model_full_file
    if model_full_path == "":
        model_full_path = None
    model_full = utils.update_model(model_full_path, threshold, update_set, batch_size)
    if model_90 is not None:
        if 1 - os.path.exists("gfi-bot/model"):
            os.makedirs("gfi-bot/model")
        model_90.save_model("gfi-bot/model/model_90_" + str(threshold) + ".model")
    if model_full is not None:
        if 1 - os.path.exists("gfi-bot/model"):
            os.makedirs("gfi-bot/model")
        model_full.save_model("gfi-bot/model/model_full_" + str(threshold) + ".model")
    return model_90


def update_peformance_training_summary(
    model_90: xgb.core.Booster, batch_size: int, prob_thres: float, threshold: int
):
    for i in TrainingSummary.objects(threshold=threshold):
        test_set = i.issues_test
        test_set = [[i.name, i.owner, iss] for iss in test_set]
        y_test, y_prob = utils.predict_issues(test_set, threshold, batch_size, model_90)
        y_pred = [int(i > prob_thres) for i in y_prob]

        auc, precision, recall, f1 = utils.get_all_metrics(y_test, y_pred, y_prob)
        acc = accuracy_score(y_test, y_pred)
        if math.isnan(auc):
            auc = 0.0

        i.model_90_file = "gfi-bot/model/model_90_" + str(threshold) + ".model"
        i.model_full_file = "gfi-bot/model/model_full_" + str(threshold) + ".model"
        i.accuracy = accuracy_score(y_test, y_pred)
        i.auc = auc
        i.last_updated = datetime.now()
        i.save()


def update_training_summary(
    threshold: int,
    min_test_size=1,
    dataset_size=20000,
    batch_size=10000,
    prob_thres=0.5,
):
    """
    Under the condition that there are at least min_test_size test points for a repository, the ratio of training points and test points of the repository is maintained at 9:1.
    If the number of resolved issues of a repository is less than min_test_size, all issues in the repository are used as test samples.
    dataset_size:  How many issues are read from Dataset in one iteration
    batch_size: the maximum number of training points allowed to be added in one-step update of models.
    prob_thres: threshold to distinguish two classes.
    """
    dataset = Dataset.objects()
    ith_batch = 0
    need_update = 0
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
            need_update = 1
        ith_batch += 1
        logger.info("Model updated.")
    if need_update == 1 and model_90 is not None:
        update_peformance_training_summary(model_90, batch_size, prob_thres, threshold)
        logger.info("Performance on each project is updated.")
    else:
        logger.info("No need to update performance.")


def update_prediction(threshold: int):
    model_full_path = TrainingSummary.objects(threshold=threshold)[0].model_full_file
    model_full = xgb.Booster()
    model_full.load_model(model_full_path)
    for i in OpenIssue.objects():
        query = Q(name=i.name, owner=i.owner, number=i.number)
        iss = Dataset.objects(query)
        iss = iss.first()
        issue = utils.get_issue_data(iss, threshold)
        issue_df = pd.DataFrame(issue, index=[0])
        y_test = issue_df["is_gfi"]
        X_test = issue_df.drop(["is_gfi", "owner", "name", "number"], axis=1)
        xg_test = xgb.DMatrix(X_test, label=y_test)
        y_prob = model_full.predict(xg_test)
        # print(xg_test)
        # print(y_prob)
        Prediction.objects(
            Q(owner=iss.owner) & Q(name=iss.name) & Q(number=iss.number)
        ).upsert_one(
            owner=iss.owner,
            name=iss.name,
            number=iss.number,
            threshold=threshold,
            probability=y_prob,
            last_updated=datetime.now(),
        )
    logger.info(
        "Get predictions for open issues under threshold " + str(threshold) + "."
    )


if __name__ == "__main__":
    for threshold in [1, 2, 3, 4, 5]:
        logger.info(
            "Update TrainingSummary and Prediction for threshold "
            + str(threshold)
            + "."
        )
        update_training_summary(threshold)
        update_prediction(threshold)
    logger.info("Done!")
