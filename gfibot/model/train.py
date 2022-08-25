import logging
import os
import time
import json
from typing import Final, List, Union, Any, Dict, Tuple, Literal, Optional

import numpy as np
import pandas as pd

from gfibot.collections import *
from .utils import split_train_test, reconnect_mongoengine, get_full_path, get_x_y
from .base import GFIModel
from .dataloader import GFIDataLoader
from .update_database import (
    update_repo_training_summary,
    update_global_training_summary,
    update_repo_prediction,
)
from .parallel import parallel


GFIBOT_MODEL_PATH = "./models"
GFIBOT_CACHE_PATH = "./.cache"


# tuned by optuna: check https://github.com/optuna/optuna-examples
OPTIMAL_XGB_PARAMS: Final = {
    "booster": "gbtree",
    "reg_lambda": 0.0081576574992808,
    "reg_alpha": 0.0006758832348175984,
    "max_depth": 8,
    "learning_rate": 0.13317566604612333,
    "gamma": 7.512488389092191e-08,
}

OPTIMAL_XGB_FIT_PARAMS: Final = {
    "eval_metric": "auc",
}

# tuned by optuna: check https://github.com/optuna/optuna-examples
OPTIMAL_LGB_PARAMS: Final = {
    "boosting_type": "gbdt",
    "reg_alpha": 1.4944893050555439e-06,
    "reg_lambda": 0.010495719629428569,
    "num_leaves": 19,
    "feature_fraction": 0.8258648989032306,
    "bagging_fraction": 0.851602064274477,
    "bagging_freq": 4,
    "min_child_samples": 82,
}

OPTIMAL_LGB_FIT_PARAMS: Final = {
    "eval_metric": "auc",
}


def train_model(
    df: pd.DataFrame,
    split_by: Literal["random", "closed_at", "created_at"] = "created_at",
    test_size: float = 0.1,
    random_seed: int = 0,
    model_type: Literal["xgb", "lgb"] = "xgb",
    model_name: Optional[str] = None,
    model_params: Optional[Dict[str, Union[str, float, int]]] = None,
    fit_params: Optional[Dict[str, Any]] = None,
    save_model: bool = True,
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
            use_label_encoder=False,
            objective="binary:logistic",
            random_state=random_seed,
            **model_params,
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
    _imp = _model.get_feature_importances()
    logging.info(
        "Most important features: %s",
        [f"{x[0]}:{x[1]}" for x in _imp.head(n=10).items()],
    )

    # get metrics
    _metrics = _model.get_metrics()
    logging.info("Model %s metrics: %s", model_name, _metrics)

    if save_model:
        _imp_path = get_full_path(GFIBOT_MODEL_PATH, f"{model_name}.importance.json")
        _imp.to_json(_imp_path, indent=2)

        _metrics_path = get_full_path(GFIBOT_MODEL_PATH, f"{model_name}.metrics.json")
        with open(_metrics_path, "w") as f:
            json.dump(_metrics, f, indent=2)

        _args_path = get_full_path(GFIBOT_MODEL_PATH, f"{model_name}.args.json")
        with open(_args_path, "w") as f:
            _args = {
                "split_by": split_by,
                "test_size": test_size,
                "random_seed": random_seed,
                "model_params": model_params,
                "fit_params": fit_params,
            }
            json.dump(_args, f, indent=2)

        _path = get_full_path(GFIBOT_MODEL_PATH, f"{model_name}.pkl")
        _model.to_pickle(_path)
        logging.info("Model %s saved to %s", model_name, _path)

    return _model


def load_full_dataset(
    newcomer_thres: int,
    random_seed: int = 0,
    # load
    text_features: Union[None, bool, dict] = False,
    drop_insignificant_features: bool = True,
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
        drop_insignificant_features=drop_insignificant_features,
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
    cache_dataset: bool = False,
    random_seed: int = 0,
    text_features: Union[None, bool, dict] = False,
    drop_insignificant_features: bool = True,
    # split
    split_by: Literal["random", "closed_at", "created_at"] = "created_at",
    # train
    model_type: Literal["xgb", "lgb"] = "xgb",
    model_names: Optional[List[str]] = None,
    model_params: Optional[Dict[str, Union[str, float, int]]] = None,
    fit_params: Optional[Dict[str, Any]] = None,
    # # update database
    # update_db_with_workers: bool = False,
    update_database: bool = False,
):
    """
    Train all models from full dataset and save to disk.
    :param newcomer_thresholds: List of newcomer thresholds. (default: [1, 2, 3, 4, 5])
    :param test_sizes: List of test sizes. (default: [0.1, 0])
    :param cache_dataset: Whether to cache the dataset. (default: False)
    :param random_seed: Random seed. (default: 0)
    :param text_features: Whether to use text features. (default: False)
    :param drop_insignificant_features: Whether to drop insignificant features. (default: True)
    :param split_by: Split train and test by [random, closed_at, created_at] (default: created_at).
    :param model_type: Model type [xgb, lgb] (default: xgb).
    :param model_names: List of model names. (default: None)
    :param model_params: Model parameters. (default: None)
    :param fit_params: Fit parameters. (default: None)
    :param dry_run: if True, do not write to database. (default: False)
    """
    if not newcomer_thresholds:
        newcomer_thresholds = [1, 2, 3, 4, 5]
    if not test_sizes:
        test_sizes = [0.1, 0]

    _counter = 0
    _total = len(newcomer_thresholds) * len(test_sizes)
    for newcomer_thres in newcomer_thresholds:
        # load df
        cache_path = get_full_path(
            GFIBOT_CACHE_PATH,
            f'dataset_{newcomer_thres}{"" if text_features is False else "_text"}{"_lite" if drop_insignificant_features else ""}.csv',
        )
        if cache_dataset and os.path.exists(cache_path):
            logging.info("Found dataset in cache %s", cache_path)
            _df = pd.read_csv(cache_path, low_memory=False)
        else:
            _df = load_full_dataset(
                newcomer_thres=newcomer_thres,
                random_seed=random_seed,
                text_features=text_features,
                drop_insignificant_features=drop_insignificant_features,
            )
            _df.to_csv(cache_path, index=False)
        # groupby
        _groupby = _df.groupby(["name", "owner"])

        for test_size in test_sizes:
            if not model_names:
                model_name = (
                    f'{model_type}_{newcomer_thres}{"" if text_features is False else "_text"}_{split_by}'
                    f'_{test_size}_{"default" if not model_params else "custom"}{"_lite" if drop_insignificant_features else ""}'
                )
            else:
                model_name = model_names[_counter]

            logging.info(
                "(%d/%d) Model %s training started: newcomer_thres=%d split_by=%s test_size=%f model_type=%s model_params=%s fit_params=%s",
                _counter,
                _total,
                model_name,
                newcomer_thres,
                split_by,
                test_size,
                model_type,
                model_params,
                fit_params,
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
                save_model=True,
            )

            _counter += 1

            if not update_database:
                continue

            if 0 < test_size < 1:
                logging.info(
                    "Eval model (test_size=%f) detected, saving training summary",
                    test_size,
                )
                # update global training summary
                update_global_training_summary(
                    df=_df,
                    model=_model,
                    newcomer_thres=newcomer_thres,
                )

                # update repo training summary
                # df_l = [x[1] for x in _groupby]
                # if update_db_with_workers:
                #     def update_summary_wrapper(df: pd.DataFrame) -> None:
                #         update_repo_training_summary(
                #             newcomer_thres=newcomer_thres, df=df, model=_model
                #         )
                #
                #     parallel(update_summary_wrapper, df_l)
                # else:
                for _, df in _groupby:
                    update_repo_training_summary(
                        newcomer_thres=newcomer_thres, df=df, model=_model
                    )
            else:
                # update issue prediction
                logging.info(
                    "Full model (test_size=%f) detected, saving prediction", test_size
                )

                for _, df in _groupby:
                    update_repo_prediction(
                        newcomer_thres=newcomer_thres, df=df, model=_model
                    )

            # _x, _y = get_x_y(_df)
            # _predicted = _model.predict(_x)
            # _x["prediction"] = _predicted
            # _x["is_gfi"] = _y
            # _path = get_full_path(
            #     GFIBOT_CACHE_PATH,
            #     f'{model_name}.prediction.csv',
            # )
            # _x.to_csv(_path, index=False)
            # logging.info("Prediction saved to %s", _path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        "Train all models from full dataset and save to disk."
    )
    parser.add_argument(
        "--newcomer-thresholds",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4, 5],
        help="iteration newcomer thresholds. (default: [1, 2, 3, 4, 5])",
    )
    parser.add_argument(
        "--test-sizes",
        type=float,
        nargs="+",
        default=[0.1, 0],
        help="iteration test sizes. (default: [0.1, 0])",
    )
    parser.add_argument(
        "--cache-dataset",
        action="store_true",
        help="Cache dataset to disk for faster loading.",
    )
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument(
        "--text-features", action="store_true", help="Whether to include text features."
    )
    parser.add_argument(
        "--all-features",
        action="store_true",
        help="Whether to include insignificant features.",
    )
    parser.add_argument(
        "--split-by",
        type=str,
        default="created_at",
        choices=["random", "closed_at", "created_at"],
        help="Split train and test by [random, closed_at, created_at] (default: created_at).",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default=["xgb"],
        nargs="+",
        choices=["xgb", "lgb"],
        help="boosters to use (default: xgb)",
    )
    parser.add_argument(
        "--optimal-params", action="store_true", help="Use pre-tuned optimal parameters"
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", choices=["INFO", "DEBUG", "WARN"]
    )
    parser.add_argument(
        "--repeat-hours",
        type=int,
        default=24,
        help="Repeat every N hours, 0 to disable (default: 24)",
    )
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--update-database", action="store_true", help="if True, write predictions to database"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.getLevelName(args.log_level))

    def train_worker(args):
        for _type in args.model_type:
            _params = None
            _fit_params = None
            if args.optimal_params:
                if _type == "xgb":
                    _params = OPTIMAL_XGB_PARAMS
                    _fit_params = OPTIMAL_XGB_FIT_PARAMS
                else:
                    _params = OPTIMAL_LGB_PARAMS
                    _fit_params = OPTIMAL_LGB_FIT_PARAMS

            reconnect_mongoengine()
            train_all(
                newcomer_thresholds=args.newcomer_thresholds,
                test_sizes=args.test_sizes,
                cache_dataset=args.cache_dataset,
                random_seed=args.random_seed,
                text_features=args.text_features,
                split_by=args.split_by,
                model_type=_type,
                model_params=_params,
                fit_params=_fit_params,
                drop_insignificant_features=not args.all_features,
                update_database=args.update_database,
            )

    if args.repeat_hours > 0 and not args.run_once:
        logging.info("Repeating training every %d hours", args.repeat_hours)
        from apscheduler.schedulers.blocking import BlockingScheduler

        scheduler = BlockingScheduler()
        scheduler.add_job(
            train_worker,
            "interval",
            hours=args.repeat_hours,
            args=[args],
            next_run_time=datetime.now(),
        )
        scheduler.start()

    else:
        train_worker(args)
