from typing import Tuple, Union, Dict, Literal, Optional
import pickle
import os

import pandas as pd
import numpy as np

from gfibot import CONFIG
from .utils import SklearnCompatibleClassifier, get_binary_classifier_metrics

# where to find models
try:
    GFIBOT_MODEL_PATH = CONFIG["gfibot"]["model_path"]
except KeyError:
    GFIBOT_MODEL_PATH = "./models"

# where to find cache
try:
    GFIBOT_CACHE_PATH = CONFIG["gfibot"]["cache_path"]
except KeyError:
    GFIBOT_CACHE_PATH = "./.cache"


class GFIModel(object):
    def __init__(
        self,
        classifier: SklearnCompatibleClassifier,
    ):
        self._clf = classifier
        self._X_train, self._X_test, self._y_train, self._y_test = [None] * 4

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

    def fit(self, *args, **kwargs):
        if self._X_train is None:
            raise ValueError("Dataset not loaded: call load_dataset first")
        self._clf.fit(self._X_train, self._y_train, *args, **kwargs)

    def predict(self, X: pd.DataFrame, *args, **kwargs) -> np.ndarray:
        _r = self._clf.predict_proba(X, *args, **kwargs)[:, 1]
        return _r

    def get_metrics(self, gfi_thres: int = 0.5):
        if self._X_test is None:
            raise ValueError("Dataset not loaded: call load_dataset first")
        y_pred = self.predict(self._X_test)
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
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "wb") as f:
            pickle.dump(self._clf, f)

    def to_portable_format(self, path: str):
        if hasattr(self._clf, "_Booster") and hasattr(self._clf._Booster, "save_model"):
            self._clf._Booster.save_model(path)
        else:
            raise NotImplementedError("Only supports XGBClassifier and LGBMClassifier")
