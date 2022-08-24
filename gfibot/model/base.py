from typing import Tuple, Union, Dict, Literal, Optional
import logging
import pickle
import os

import pandas as pd
import numpy as np

from .utils import SklearnRFCompatibleClassifier, get_binary_classifier_metrics


class GFIModel(object):
    def __init__(
        self, classifier: SklearnRFCompatibleClassifier, log_level: int = logging.INFO
    ):
        self._clf = classifier
        self._X_train, self._X_test, self._y_train, self._y_test = [None] * 4

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)

    def load_dataset(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
    ):
        self._X_train = X_train
        self._y_train = y_train
        self._X_test = X_test
        self._y_test = y_test
        self._logger.info(
            "dataset loaded: %d train, %d test", len(self._X_train), len(self._X_test)
        )

    def fit(self, *args, **kwargs):
        if self._X_train is None:
            raise ValueError("Dataset not loaded: call load_dataset first")
        self._clf.fit(self._X_train, self._y_train, *args, **kwargs)

    def predict(self, X: pd.DataFrame, *args, **kwargs) -> pd.Series:
        return self._clf.predict(X, *args, **kwargs)

    def get_metrics(self, gfi_thres: int = 0.5):
        if self._X_test is None:
            raise ValueError("Dataset not loaded: call load_dataset first")
        y_pred = self._clf.predict(self._X_test)
        return get_binary_classifier_metrics(self._y_test, y_pred, gfi_thres)

    def get_feature_importances(self, X: Optional[pd.DataFrame] = None) -> pd.Series:
        if X is None:
            if self._X_test is None:
                raise ValueError("Dataset not loaded: call load_dataset first")
            X = self._X_test
        _imp = self._clf.feature_importances_
        _names = X.columns
        return pd.Series(_imp, index=_names).sort_values(ascending=False)

    @classmethod
    def from_pickle(cls, path: str, *args, **kwargs) -> "GFIModel":
        with open(path, "rb") as f:
            clf = pickle.load(f)
        return cls(clf, *args, **kwargs)

    def to_pickle(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self._clf, f)

    def to_portable_format(self, path: str):
        if hasattr(self._clf, "_Booster") and hasattr(self._clf._Booster, "save_model"):
            self._clf._Booster.save_model(path)
        else:
            raise NotImplementedError("Only supports XGBClassifier and LGBMClassifier")
