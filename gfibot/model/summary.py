from datetime import datetime
from typing import Optional
import logging

import pandas as pd
import numpy as np

from gfibot.collections import *
from .base import GFIModel
from .utils import get_x_y, get_binary_classifier_metrics


def _update_training_summary_in_db(name: str, owner: str, threshold: int, **kwargs):
    """
    Update fields in the training summary collection.
    """
    logging.debug("Updating training summary for %s/%s: %s", owner, name, kwargs)
    q = TrainingSummary.objects(name=name, owner=owner, threshold=threshold).first()
    if q is None:
        q = TrainingSummary(
            name=name,
            owner=owner,
            threshold=threshold,
            issues_train=[],
            issues_test=[],
            n_resolved_issues=0,
            n_newcomer_resolved=0,
            batch_accuracy=[],
            batch_auc=[],
            batch_precision=[],
            batch_recall=[],
            batch_f1=[],
            last_updated=datetime.now(),
            n_stars=0,
            issue_close_time=0,
            auc=float(np.nan),
            accuracy=float(np.nan),
            f1=float(np.nan),
            precision=float(np.nan),
            recall=float(np.nan),
        )
    for k, v in kwargs.items():
        setattr(q, k, v)
    q.last_updated = datetime.now()
    q.save()


def update_repo_training_summary(
    newcomer_thres: int,
    df: pd.DataFrame,
    model: GFIModel,
    name: Optional[str] = None,
    owner: Optional[str] = None,
    gfi_thres: float = 0.5,
):
    """
    Update the training summary for a given model and a given repository.
    newcomer_thres: threshold #commits for newcomers
    df: dataset dataframe
    model: the model used for the training
    name: the name of the repository (default: None -> inferred from df, "" -> global)
    owner: the owner of the repository (default: None -> inferred from df, "" -> global)
    gfi_thres: the threshold an issue to be a gfi (default: 0.5)
    """
    if df.empty:
        logging.warning("dataframe is empty: %s/%s", owner, name)
        return

    df_head = df.iloc[0]
    if owner is None:
        owner = df_head["owner"]
    if name is None:
        name = df_head["name"]

    _issue_close_time, _n_stars, _n_resolved_issues = (
        df_head["issue_close_time"]
        if df_head["issue_close_time"] is not None
        else float(np.nan),
        df_head["n_stars"] if df_head["n_stars"] is not None else float(np.nan),
        df_head["n_closed_issues"]
        if df_head["n_closed_issues"] is not None
        else float(np.nan),
    )

    _n_newcomer_resolved = np.sum(df["is_gfi"] == 1)
    _r_newcomer_resolved = (
        _n_newcomer_resolved / _n_resolved_issues if _n_resolved_issues > 0 else 0
    )

    X, y = get_x_y(df)
    y_pred = model.predict(X)

    _n_gfis = np.sum(y_pred > gfi_thres)

    metrics = get_binary_classifier_metrics(y, y_pred, gfi_thres)

    _update_training_summary_in_db(
        name=name,
        owner=owner,
        threshold=newcomer_thres,
        issue_close_time=_issue_close_time,
        n_stars=_n_stars,
        n_resolved_issues=_n_resolved_issues,
        n_newcomer_resolved=_n_newcomer_resolved,
        r_newcomer_resolved=_r_newcomer_resolved,
        n_gfis=_n_gfis,
        **metrics
    )


def update_global_training_summary(
    newcomer_thres: int, df: pd.DataFrame, model: GFIModel, gfi_thres: float = 0.5
):
    """
    Update the global training summary for a given model.
    newcomer_thres: threshold #commits for newcomers
    df: dataset dataframe
    model: the model used for the training
    gfi_thres: the threshold an issue to be a gfi (default: 0.5)
    """
    if df.empty:
        logging.warning("dataframe is empty")
        return

    _n_resolved_issues = np.sum(~df["closed_at"].isna())
    _n_newcomer_resolved = np.sum(df["is_gfi"] == 1)
    _r_newcomer_resolved = (
        _n_newcomer_resolved / _n_resolved_issues if _n_resolved_issues > 0 else 0
    )

    X, y = get_x_y(df)
    y_pred = model.predict(X)
    _n_gfis = np.sum(y_pred > gfi_thres)

    metrics = model.get_metrics()

    _update_training_summary_in_db(
        name="",
        owner="",
        threshold=newcomer_thres,
        n_resolved_issues=_n_resolved_issues,
        n_newcomer_resolved=_n_newcomer_resolved,
        r_newcomer_resolved=_r_newcomer_resolved,
        n_gfis=_n_gfis,
        **metrics
    )


def _update_prediction_in_db(
    name: str, owner: str, number: int, threshold: int, **kwargs
):
    logging.debug(
        "Updating training summary for %s/%s@%d: %s", owner, name, number, kwargs
    )
    Prediction.objects(
        name=name, owner=owner, number=number, threshold=threshold
    ).upsert_one(
        name=name, owner=owner, number=number, last_updated=datetime.now(), **kwargs
    )


def update_repo_prediction(
    newcomer_thres: int,
    df: pd.DataFrame,
    model: GFIModel,
    name: Optional[str] = None,
    owner: Optional[str] = None,
):
    """
    Update the prediction for a given model and a given repository.
    newcomer_thres: threshold #commits for newcomers
    df: dataset dataframe
    model: the model used for the training
    name: the name of the repository (default: None -> inferred from df, "" -> global)
    owner: the owner of the repository (default: None -> inferred from df, "" -> global)
    """
    if df.empty:
        logging.warning("dataframe is empty: %s/%s", owner, name)
        return

    df_head = df.iloc[0]
    if owner is None:
        owner = df_head["owner"]
    if name is None:
        name = df_head["name"]

    X, y = get_x_y(df)
    y_pred = model.predict(X)

    for i, (idx, row) in enumerate(df.iterrows()):
        _update_prediction_in_db(
            name=name,
            owner=owner,
            threshold=newcomer_thres,
            number=row["number"],
            probability=y_pred[i],
        )
