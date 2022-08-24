import logging
import os
import time
from typing import Final, List, Union, Any, Dict, Tuple, Literal, Optional

import numpy as np
import pandas as pd

from gfibot.collections import *
from .utils import split_train_test, reconnect_mongoengine, get_model_path
from .base import GFIModel
from .dataloader import GFIDataLoader
from .summary import update_repo_training_summary, update_global_training_summary
from .parallel import parallel


# tuned by optuna: check https://github.com/optuna/optuna-examples
OPTIMAL_XGB_PARAMS: Final = {
    "reg_lambda": 0.0081576574992808,
    "reg_alpha": 0.0006758832348175984,
    "max_depth": 8,
    "learning_rate": 0.13317566604612333,
    "gamma": 7.512488389092191e-08,
}

# tuned by optuna: check https://github.com/optuna/optuna-examples
OPTIMAL_LGB_PARAMS: Final = {
    "reg_alpha": 1.4944893050555439e-06,
    "reg_lambda": 0.010495719629428569,
    "num_leaves": 19,
    "feature_fraction": 0.8258648989032306,
    "bagging_fraction": 0.851602064274477,
    "bagging_freq": 4,
    "min_child_samples": 82,
}


def train_model(
    df: pd.DataFrame,
    split_by: Literal["random", "closed_at", "created_at"] = "created_at",
    test_size: float = 0.1,
    random_seed: int = 19260817,
    model_type: Literal["xgb", "lgb"] = "xgb",
    model_name: Optional[str] = None,
    model_params: Optional[Dict[str, Union[str, float, int]]] = None,
    fit_params: Optional[Dict[str, Any]] = None,
) -> GFIModel:
    """
    Train a model from a dataframe and save it to disk.
    """
    if fit_params is None:
        fit_params = {}
    if model_params is None:
        model_params = {}
    if not model_name:
        model_name = f"{model_type}_{split_by}_{test_size}"
    if test_size == 0.0 and split_by == "random":  # empty test set
        test_size = 1
    logging.debug(locals())

    train_x, test_x, train_y, test_y = split_train_test(
        df, by=split_by, test_size=test_size, random_seed=random_seed
    )
    logging.info(f"Train size: {len(train_x)}, test size: {len(test_x)}")

    if model_type == "xgb":
        import xgboost as xgb

        clf = xgb.XGBClassifier(
            objective="binary:logistic", random_state=random_seed, **model_params
        )
    elif model_type == "lgb":
        import lightgbm as lgb

        clf = lgb.LGBMClassifier(
            objective="binary",
            importance_type="gain",
            random_state=random_seed,
            **model_params,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    _start_time = time.time()
    _model = GFIModel(clf)
    _model.load_dataset(train_x, test_x, train_y, test_y)
    _model.fit(**fit_params)
    logging.info(
        "Model %s training finished in %.2f seconds",
        model_name,
        time.time() - _start_time,
    )

    # get feature importance
    logging.info(
        "Most important features: %s",
        (f"{x[0]}:{x[1]}" for x in _model.get_feature_importances().head(n=10).items()),
    )

    # get metrics
    logging.info("Model %s metrics: %s", model_name, _model.get_metrics())

    # save model
    _path = get_model_path(model_name)
    _model.to_pickle(_path)
    logging.info("Model %s saved to %s", model_name, _path)

    return _model


def load_full_dataset(
    newcomer_thres: int,
    random_seed: int = 19260817,
    # load
    text_features: Union[None, bool, dict] = False,
):
    """
    Load closed issues for all repos.
    """
    # get repo list
    _repos: List[Repo] = Repo.objects().only("name", "owner")
    _queries = [Q(name=x.name, owner=x.owner) for x in _repos]
    logging.info(
        "Loading dataset from %d repos, newcomer_thres=%d",
        len(_queries),
        newcomer_thres,
    )
    _start_time = time.time()

    # load data
    _level = logging.getLogger().getEffectiveLevel()
    _loader = GFIDataLoader(
        log_level=_level,
        random_seed=random_seed,
        text_features=text_features,
        drop_open_issues=True,  # don't need open issues
    )
    _df = _loader.load_dataset(
        queries=_queries,
        newcomer_thres=newcomer_thres,
    )
    logging.info("Dataset loaded in %.2f seconds", time.time() - _start_time)
    return _df


def train_all(
    # it
    newcomer_thresholds: Optional[List[int]] = None,
    test_sizes: Optional[List[float]] = None,
    # load
    random_seed: int = 19260817,
    text_features: Union[None, bool, dict] = False,
    # split
    split_by: Literal["random", "closed_at", "created_at"] = "created_at",
    # train
    model_type: Literal["xgb", "lgb"] = "xgb",
    model_names: Optional[List[str]] = None,
    model_params: Optional[Dict[str, Union[str, float, int]]] = OPTIMAL_XGB_PARAMS,
    fit_params: Optional[Dict[str, Any]] = None,
):
    if not newcomer_thresholds:
        newcomer_thresholds = [1, 2, 3, 4, 5]
    if not test_sizes:
        test_sizes = [0.1, 0]

    _counter = 0
    _total = len(newcomer_thresholds) * len(test_sizes)
    for newcomer_thres in newcomer_thresholds:
        _df = load_full_dataset(
            newcomer_thres=newcomer_thres,
            random_seed=random_seed,
            text_features=text_features,
        )
        _groupby = _df.groupby(["name", "owner"])
        for test_size in test_sizes:
            if not model_names:
                model_name = f'{model_type}_{newcomer_thres}_{"" if text_features is False else "text_"}{split_by}_{test_size}'
            else:
                model_name = model_names[_counter]

            logging.info(
                "(%d/%d) Model %s training started: newcomer_thres=%d split_by=%s test_size=%f model_type=%s model_params=%s",
                _counter,
                _total,
                model_name,
                newcomer_thres,
                split_by,
                test_size,
                model_type,
                model_params,
            )

            _model = train_model(
                _df,
                split_by=split_by,
                test_size=test_size,
                random_seed=random_seed,
                model_type=model_type,
                model_name=model_name,
                model_params=model_params,
                fit_params=fit_params,
            )

            if 0 < test_size < 1:
                # update global training summary
                update_global_training_summary(
                    df=_df,
                    model=_model,
                    newcomer_thres=newcomer_thres,
                )

                # update repo training summary
                df_l = [x[1] for x in _groupby]

                def update_summary_wrapper(df: pd.DataFrame) -> None:
                    update_repo_training_summary(
                        newcomer_thres=newcomer_thres, df=df, model=_model
                    )

                parallel(update_summary_wrapper, df_l)

            _counter += 1


if __name__ == "__main__":
    reconnect_mongoengine()
    logging.basicConfig(level=logging.DEBUG)
    train_all(
        newcomer_thresholds=[3],
        test_sizes=[0, 0.1],
    )
