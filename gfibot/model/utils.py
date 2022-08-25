from typing import Dict, Protocol, runtime_checkable, Tuple, Literal, List, Union
import os

import mongoengine
from pymongo import MongoClient
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_curve,
    auc,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
)
from sklearn.model_selection import train_test_split

from gfibot import CONFIG


def reconnect_mongoengine() -> MongoClient:
    """Disconnect all pymongo clients (call before fork)"""
    mongoengine.disconnect_all()
    return mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
        connect=False,
    )


def downcast_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downcast the dataframe to reduce memory usage.
    credit: https://www.kaggle.com/code/anshuls235/time-series-forecasting-eda-fe-modelling
    """
    cols = df.dtypes.index.tolist()
    types = df.dtypes.values.tolist()
    for i, t in enumerate(types):
        if "int" in str(t):
            if (
                df[cols[i]].min() > np.iinfo(np.int8).min
                and df[cols[i]].max() < np.iinfo(np.int8).max
            ):
                df[cols[i]] = df[cols[i]].astype(np.int8)
            elif (
                df[cols[i]].min() > np.iinfo(np.int16).min
                and df[cols[i]].max() < np.iinfo(np.int16).max
            ):
                df[cols[i]] = df[cols[i]].astype(np.int16)
            elif (
                df[cols[i]].min() > np.iinfo(np.int32).min
                and df[cols[i]].max() < np.iinfo(np.int32).max
            ):
                df[cols[i]] = df[cols[i]].astype(np.int32)
            else:
                df[cols[i]] = df[cols[i]].astype(np.int64)
        elif "float" in str(t):
            if (
                df[cols[i]].min() > np.finfo(np.float16).min
                and df[cols[i]].max() < np.finfo(np.float16).max
            ):
                df[cols[i]] = df[cols[i]].astype(np.float16)
            elif (
                df[cols[i]].min() > np.finfo(np.float32).min
                and df[cols[i]].max() < np.finfo(np.float32).max
            ):
                df[cols[i]] = df[cols[i]].astype(np.float32)
            else:
                df[cols[i]] = df[cols[i]].astype(np.float64)
        elif t == object:
            if "date" in cols[i] or "time" in cols[i]:
                df[cols[i]] = pd.to_datetime(df[cols[i]])
            elif "timedelta" in cols[i]:
                df[cols[i]] = pd.to_timedelta(df[cols[i]])
            else:
                df[cols[i]] = df[cols[i]].astype("category")
    return df


def get_binary_classifier_metrics(
    y_test: np.ndarray, y_pred: np.ndarray, threshold: float = 0.5
) -> Dict[str, float]:
    """
    Compute precision, recall, f1, and AUC for a binary classifier prediction.
    :param y_test: true labels; (bool)
    :param y_pred: predicted labels; (float)
    :param threshold: threshold for binary classifier prediction; (default:0.5, float)
    :return: precision, recall, f1, and AUC for a binary classifier prediction; (dict)
    """
    pred_labels = y_pred > threshold
    fpr, tpr, thresholds_keras = roc_curve(y_test, y_pred)
    _auc = auc(fpr, tpr)
    precision = precision_score(y_test, pred_labels)
    recall = recall_score(y_test, pred_labels)
    f1 = f1_score(y_test, pred_labels)
    accuracy = accuracy_score(y_test, pred_labels)
    return {
        "auc": _auc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


@runtime_checkable
class SklearnRFCompatibleClassifier(Protocol):
    """
    Classifiers that expose the same APIs as RandomForestClassifier.
    """

    def __init__(self, *args, **kwargs):
        ...

    def fit(self, X, y, *args, **kwargs):
        ...

    def predict(self, X, *args, **kwargs) -> np.ndarray:
        ...

    def score(self, X, y, *args, **kwargs) -> float:
        ...

    @property
    def feature_importances_(self) -> np.ndarray:
        ...


def get_x_y(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    # drop only if exists
    df_x = df.drop(
        columns=df.filter(
            ["owner", "name", "number", "is_gfi", "created_at", "closed_at"]
        )
    )
    s_y = df["is_gfi"]
    return df_x, s_y


def split_train_test(
    df_data: pd.DataFrame,
    by: Literal["random", "created_at", "closed_at"] = "random",
    random_seed: int = 0,
    test_size: Union[float, int] = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split dataframe into train and test sets.
    :param df_data: dataframe to split; (pd.DataFrame)
    :param by: split by; (default: "random", Literal["random", "created_at", "closed_at"])
    :param random_seed: random seed; (default: 0, int)
    :param test_size: test size; (default: 0.2, float for % of examples; use positive int for # of samples)
    :return: train, test, y_train, y_test
    """
    if test_size == 0:
        test_size = 1
    if by == "random":
        X, y = get_x_y(df_data)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_seed
        )
    else:
        # use earlier created/closed issues as training data (null -> latest)
        if by == "created_at":
            _df_sorted = df_data.sort_values("created_at")
        elif by == "closed_at":
            _df_sorted = df_data.sort_values("closed_at")
        else:
            raise ValueError(
                f"invalid by: {by}, expected: random, created_at, closed_at"
            )
        if test_size >= 1:  # mocks train_test_split
            _train_len = len(_df_sorted) - test_size
        elif 0 < test_size < 1:
            _train_len = int(len(_df_sorted) * (1 - test_size))
        else:
            raise ValueError(f"invalid test_size: {test_size}, only accept >= 0")
        X_train, y_train = get_x_y(_df_sorted.iloc[:_train_len])
        X_test, y_test = get_x_y(_df_sorted.iloc[_train_len:])

    return X_train, X_test, y_train, y_test


def get_full_path(*args: str):
    _path = os.path.expanduser(os.path.abspath(os.path.join(*args)))
    if not os.path.exists(os.path.dirname(_path)) and not os.path.isdir(
        os.path.dirname(_path)
    ):
        os.makedirs(os.path.dirname(_path))
    return _path


def get_model_path(model_name: str) -> str:
    return get_full_path(f"models", f"{model_name}.pkl")
