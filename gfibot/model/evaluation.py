import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

from gfibot.collections import (
    ModelEvaluation,
    ModelEvaluationResult,
    AblationStudyResult,
    FeatureImportance,
)
from gfibot.model.utils import get_x_y, get_binary_classifier_metrics, split_train_test

logger = logging.getLogger(__name__)


def evaluate_candidate_models(
    X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series
) -> List[ModelEvaluationResult]:
    """
    Evaluates alternative classifiers (RandomForest, GradientBoosting/LightGBM, LogisticRegression, SVM, MLP)
    and returns performance metrics for comparison.
    """
    candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "SVM": SVC(probability=True, random_state=42),
        "MLPClassifier": MLPClassifier(max_iter=500, random_state=42),
    }

    results: List[ModelEvaluationResult] = []

    for name, clf in candidates.items():
        try:
            clf.fit(X_train, y_train)
            if hasattr(clf, "predict_proba"):
                y_pred = clf.predict_proba(X_test)[:, 1]
            else:
                y_pred = clf.predict(X_test)

            metrics = get_binary_classifier_metrics(y_test.to_numpy(), y_pred)
            results.append(
                ModelEvaluationResult(
                    model_name=name,
                    accuracy=float(metrics["accuracy"]),
                    auc=float(metrics["auc"]),
                    precision=float(metrics["precision"]),
                    recall=float(metrics["recall"]),
                    f1=float(metrics["f1"]),
                    best_params=getattr(clf, "get_params", lambda: {})(),
                )
            )
        except Exception as e:
            logger.warning(f"Evaluation failed for model {name}: {e}")

    return results


def run_ablation_study(
    df_data: pd.DataFrame, test_size: float = 0.2
) -> List[AblationStudyResult]:
    """
    Runs feature ablation studies by systematically dropping feature groups
    (e.g., text readability metrics, issue label categories, user features) to measure impact on AUC and F1.
    """
    X_full, y_full = get_x_y(df_data)
    X_tr, X_te, y_tr, y_te = split_train_test(df_data, test_size=test_size)

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_tr, y_tr)
    y_pred_full = clf.predict_proba(X_te)[:, 1]
    metrics_full = get_binary_classifier_metrics(y_te.to_numpy(), y_pred_full)

    ablation_results = [
        AblationStudyResult(
            feature_group="all_features",
            auc=float(metrics_full["auc"]),
            f1=float(metrics_full["f1"]),
        )
    ]

    # Feature group definitions for ablation
    groups = {
        "w/o_readability": [c for c in X_full.columns if "readability" in c or "flesch" in c or "coleman" in c],
        "w/o_label_categories": [c for c in X_full.columns if c.endswith("_num")],
        "w/o_content_counts": [c for c in X_full.columns if c.startswith("n_") or c.startswith("len_")],
    }

    for grp_name, cols_to_drop in groups.items():
        if not cols_to_drop:
            continue
        cols_keep = [c for c in X_tr.columns if c not in cols_to_drop]
        if not cols_keep:
            continue

        try:
            clf_sub = RandomForestClassifier(n_estimators=50, random_state=42)
            clf_sub.fit(X_tr[cols_keep], y_tr)
            y_pred_sub = clf_sub.predict_proba(X_te[cols_keep])[:, 1]
            metrics_sub = get_binary_classifier_metrics(y_te.to_numpy(), y_pred_sub)
            ablation_results.append(
                AblationStudyResult(
                    feature_group=grp_name,
                    auc=float(metrics_sub["auc"]),
                    f1=float(metrics_sub["f1"]),
                )
            )
        except Exception as e:
            logger.warning(f"Ablation study failed for {grp_name}: {e}")

    return ablation_results


def extract_feature_importances(
    X_train: pd.DataFrame, y_train: pd.Series, top_n: int = 15
) -> List[FeatureImportance]:
    """
    Fits a RandomForest model and extracts top feature importances.
    """
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    importances = clf.feature_importances_
    features = X_train.columns

    indices = np.argsort(importances)[::-1][:top_n]
    fi_list = []
    for idx in indices:
        fi_list.append(
            FeatureImportance(
                feature_name=str(features[idx]),
                importance=float(importances[idx]),
            )
        )
    return fi_list


def run_systematic_evaluation(
    df_data: pd.DataFrame, owner: str = "", name: str = "", threshold: int = 3
) -> ModelEvaluation:
    """
    Executes full systematic evaluation pipeline and persists results into MongoDB ModelEvaluation collection.
    """
    X_train, X_test, y_train, y_test = split_train_test(df_data, test_size=0.2)

    model_comps = evaluate_candidate_models(X_train, y_train, X_test, y_test)
    ablations = run_ablation_study(df_data)
    feat_imps = extract_feature_importances(X_train, y_train)

    now = datetime.utcnow()
    eval_doc = ModelEvaluation.objects(owner=owner, name=name, threshold=threshold).first()
    if not eval_doc:
        eval_doc = ModelEvaluation(
            owner=owner,
            name=name,
            threshold=threshold,
            evaluation_time=now,
            model_comparisons=model_comps,
            ablation_studies=ablations,
            feature_importances=feat_imps,
        )
    else:
        eval_doc.evaluation_time = now
        eval_doc.model_comparisons = model_comps
        eval_doc.ablation_studies = ablations
        eval_doc.feature_importances = feat_imps

    eval_doc.save()
    return eval_doc
