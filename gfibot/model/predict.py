import logging
import os
import datetime
from typing import Final, List, Union, Any, Dict, Tuple, Literal, Optional

import numpy as np
import pandas as pd

from gfibot.collections import *
from .utils import split_train_test, reconnect_mongoengine, get_full_path
from .base import GFIModel
from .dataloader import GFIDataLoader
from .update_database import update_repo_training_summary, update_repo_prediction

# where to find models
GFIBOT_MODEL_PATH = "./models"
GFIBOT_CACHE_PATH = "./.cache"
# which model to load
MODEL_NAME_EVALUATION = (
    lambda newcomer_thres: f"xgb_{newcomer_thres}_created_at_0.1_default_lite"
)
MODEL_NAME_PREDICTION = (
    lambda newcomer_thres: f"xgb_{newcomer_thres}_created_at_0_default_lite"
)


class GFIModelLoader(object):
    _models: Dict[str, GFIModel] = {}
    _model_edited_time: Dict[str, float] = {}

    @classmethod
    def load_model(cls, model_name: str) -> GFIModel:
        """
        Cache models based on model_name and mod time of the model file.
        """
        _path = get_full_path(GFIBOT_MODEL_PATH, model_name + ".pkl")
        if not os.path.exists(_path):
            raise FileNotFoundError(f"Model not found: {_path}")

        _update_flag = model_name not in cls._models
        if not _update_flag:
            _modified_time = os.path.getmtime(_path)
            _update_flag = _modified_time > cls._model_edited_time[model_name]

        if not _update_flag:
            return cls._models[model_name]

        _model = GFIModel.from_pickle(_path)
        _modified_time = os.path.getmtime(_path)
        cls._models[model_name] = _model
        cls._model_edited_time[model_name] = _modified_time
        logging.info(
            "Loading %s, modified at %s", _path, datetime.fromtimestamp(_modified_time)
        )
        return _model


def predict_repo(owner: str, name: str, newcomer_thres: int) -> None:
    """
    Updates Prediction and Training Summary of a repo.
    :param name: name of the repo
    :param owner: owner of the repo
    :param newcomer_thres: threshold #commits for newcomers
    """
    # single thread, include open issues
    loader = GFIDataLoader()
    _df = loader.load_dataset(
        [Q(name=name, owner=owner)], newcomer_thres=newcomer_thres, with_workers=False
    )
    # update repo prediction
    _model_pred = GFIModelLoader.load_model(MODEL_NAME_PREDICTION(newcomer_thres))
    update_repo_prediction(df=_df, newcomer_thres=newcomer_thres, model=_model_pred)
    # update training summary
    _df_closed = _df.drop(columns=["closed_at"])  # exclude open issues
    if _df_closed.empty:
        return
    _model_eval = GFIModelLoader.load_model(MODEL_NAME_EVALUATION(newcomer_thres))
    update_repo_training_summary(
        df=_df_closed, newcomer_thres=newcomer_thres, model=_model_eval
    )
