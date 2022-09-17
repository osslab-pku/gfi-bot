import logging
import os
import datetime
from typing import Final, List, Union, Any, Dict, Tuple, Literal, Optional

import numpy as np
import pandas as pd

from gfibot.collections import *
from .utils import split_train_test, reconnect_mongoengine, get_full_path
from .base import GFIModel, GFIBOT_MODEL_PATH, GFIBOT_CACHE_PATH
from .dataloader import GFIDataLoader
from .update_database import update_repo_training_summary, update_repo_prediction

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
    _df_closed = _df.dropna(subset=["closed_at"])  # exclude open issues
    if _df_closed.empty:
        return
    _model_eval = GFIModelLoader.load_model(MODEL_NAME_EVALUATION(newcomer_thres))
    update_repo_training_summary(
        df=_df_closed, newcomer_thres=newcomer_thres, model=_model_eval
    )


if __name__ == "__main__":
    import logging
    from argparse import ArgumentParser
    from tqdm.auto import tqdm
    from .update_database import update_global_training_summary
    from .train import load_full_dataset
    from .utils import split_train_test, reconnect_mongoengine

    DEFAULT_MODEL_ARGS = {"text_features": False, "drop_insignificant_features": True}
    DEFAULT_SPLIT_ARGS = {"test_size": 0.1, "by": "created_at"}

    parser = ArgumentParser("Manually update prediction and training summary")
    parser.add_argument(
        "--newcomer-thresholds",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4, 5],
        help="iteration newcomer thresholds. (default: [1, 2, 3, 4, 5])",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Cache dataset to disk for faster loading.",
    )
    args = parser.parse_args()

    reconnect_mongoengine()

    for newcomer_thres in args.newcomer_thresholds:
        text_features = DEFAULT_MODEL_ARGS["text_features"]
        drop_insignificant_features = DEFAULT_MODEL_ARGS["drop_insignificant_features"]
        cache_path = get_full_path(
            GFIBOT_CACHE_PATH,
            f'dataset_{newcomer_thres}{"" if text_features is False else "_text"}{"_lite" if drop_insignificant_features else ""}.csv',
        )

        if args.use_cache and os.path.exists(cache_path):
            _df = pd.read_csv(cache_path, low_memory=False)
            _df["created_at"] = pd.to_datetime(_df["created_at"])
        else:
            _df = load_full_dataset(
                newcomer_thres=newcomer_thres,
                **DEFAULT_MODEL_ARGS,
            )
            _df.to_csv(cache_path, index=False)

        logging.info("Loaded dataset with %d issues", len(_df))

        _groupby = _df.groupby(["owner", "name"])

        _model_pred = GFIModelLoader.load_model(MODEL_NAME_PREDICTION(newcomer_thres))
        # update issue prediction
        logging.info(
            "Full model %s, saving prediction", MODEL_NAME_PREDICTION(newcomer_thres)
        )
        for _, df in tqdm(_groupby):
            update_repo_prediction(
                newcomer_thres=newcomer_thres, df=df, model=_model_pred
            )

        _df = _df.dropna(subset=["closed_at"])  # exclude open issues
        _groupby = _df.groupby(["owner", "name"])
        logging.info("Loaded dataset with %d closed issues", len(_df))

        train_x, test_x, train_y, test_y = split_train_test(_df, **DEFAULT_SPLIT_ARGS)
        _model_eval = GFIModelLoader.load_model(MODEL_NAME_EVALUATION(newcomer_thres))
        _model_eval.load_dataset(train_x, test_x, train_y, test_y)
        logging.info(
            "Eval model %s, saving global training summary",
            MODEL_NAME_EVALUATION(newcomer_thres),
        )
        # update global training summary
        update_global_training_summary(
            df=_df,
            model=_model_eval,
            newcomer_thres=newcomer_thres,
        )
        logging.info(
            "Eval model %s, saving repo training summary",
            MODEL_NAME_EVALUATION(newcomer_thres),
        )
        # update repo training summary
        for _, df in tqdm(_groupby):
            update_repo_training_summary(
                newcomer_thres=newcomer_thres, df=df, model=_model_eval
            )
