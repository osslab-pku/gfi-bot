import logging
import time
import re
import os
import json
from typing import Final, List, Union, Any, Dict, Tuple, Literal, Optional

import numpy as np
import pandas as pd
from pymongo import MongoClient
from mongoengine import Q
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from nltk.stem.snowball import EnglishStemmer
from nltk.corpus import stopwords

from gfibot.collections import *
from .parallel import parallel, agg_append_df, _get_default_n_workers
from .utils import downcast_df, reconnect_mongoengine


DEFAULT_VECTORIZER_PARAMS: Final = {
    "decode_error": "ignore",
    "n_features": 128,
    "stop_words": None,
    "alternate_sign": False,
    "norm": None
}

# features with f-score < 0.002
_ins_path = os.path.join(os.path.dirname(__file__), "insignificant_features.json")
with open(_ins_path, 'r') as f:
    INSIGNIFICANT_FEATURES = json.load(f)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

EMOJI_ALT_PATTERN = re.compile(r"(:\w+:)", flags=re.UNICODE)

_emoticon_path = os.path.join(os.path.dirname(__file__), "emojicons.json")
with open(_emoticon_path, "r") as f:
    _emoticon = json.load(f)
EMOTICON_PATTERN = re.compile("(" + "|".join(_emoticon.keys()) + ")")

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")

HTML_PATTERN = re.compile(r"<.*?>")

MARKDOWN_PATTERN = re.compile(r"(\*|_|~|`|`{3}|#|\+|-|!|\[|\]|\(|\)|\{|\})")

STOPWORDS = set(stopwords.words("english"))


class GFIDataLoader(object):
    def __init__(
        self,
        log_level: int = logging.INFO,
        text_features: Union[None, bool, dict] = False,
        random_seed: int = 0,
        downcast_df: bool = True,
        balance_samples: bool = False,
        just_latest_record: bool = True,
        drop_open_issues: bool = False,
        drop_insignificant_features: bool = True,
    ):
        """
        Load training data from MongoDB.
        :param text_features: Whether to use text features. (can be True or a dict of parameters for HashingVectorizer)
        :param balance_samples: Whether to undersample the majority class. (force positive:negative = 1:1)
        :param random_seed: Random seed for sampling. (default: 0)
        :param downcast_df: downcast dataframe to save memory. (default: True)
        :param log_level: logger log level (default: INFO)
        :param just_latest_record: Whether to only use the latest record for each issue. (default: True)
        :param drop_open_issues: Whether to drop open issues. (default: False)
        :param drop_insignificant_features: Whether to drop insignificant features. (default: True)
        """
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)

        # dataset options
        self._random_seed = random_seed
        self._balance_samples = balance_samples
        self._downcast_df = downcast_df
        self._just_latest_record = just_latest_record
        self._drop_open_issues = drop_open_issues
        self._drop_insignificant_features = drop_insignificant_features

        if text_features not in (False, None):
            self._use_text_features = True
            if not isinstance(text_features, dict):
                text_features = DEFAULT_VECTORIZER_PARAMS
            self._vectorizer = HashingVectorizer(**text_features)
            self._transformer = TfidfTransformer()
            self._stemmer = EnglishStemmer()
        else:
            self._use_text_features = False
            self._vectorizer = None
            self._transformer = None
            self._stemmer = None

    @staticmethod
    def _is_user_newcomer(n_user_commits: int, newcomer_thres: int) -> Literal[0, 1]:
        return 1 if n_user_commits < newcomer_thres else 0

    @staticmethod
    def _get_newcomer_ratio(n_user_commits: List[int], newcomer_thres: int) -> float:
        if not n_user_commits:
            return 0.0
        return np.mean(np.array(n_user_commits) < newcomer_thres)

    @staticmethod
    def _get_newcomer_num(n_user_commits: List[int], newcomer_thres: int) -> int:
        if not n_user_commits:
            return 0
        return np.sum(np.array(n_user_commits) < newcomer_thres)

    @staticmethod
    def _get_user_feature_avg(
        user_list: List[Dataset.UserFeature], newcomer_thres: int
    ) -> Dict[str, float]:
        if not user_list:
            return {
                "commits_num": 0.0,
                "issues_num": 0.0,
                "pulls_num": 0.0,
                "repo_num": 0.0,
                "commits_num_all": 0.0,
                "issues_num_all": 0.0,
                "pulls_num_all": 0.0,
                "review_num_all": 0.0,
                "max_stars_commit": 0.0,
                "max_stars_issue": 0.0,
                "max_stars_pull": 0.0,
                "max_stars_review": 0.0,
                "gfi_ratio": 0.0,
                "gfi_num": 0.0,
            }
        uf_df = pd.DataFrame([u.to_mongo() for u in user_list])
        s_res = uf_df.mean(numeric_only=True)
        s_res["gfi_num"] = np.sum(
            [np.sum(np.array(x) < newcomer_thres) for x in uf_df["resolver_commits"]]
        )
        s_res["gfi_ratio"] = s_res["gfi_num"] / len(user_list)
        return s_res.to_dict()

    def _preprocess_text(self, text: str) -> np.ndarray:
        """
        Preprocess text.
        """
        if not self._use_text_features:
            raise ValueError("text_features is not enabled")
        _text = text.lower()
        # remove markdown tags
        _text = MARKDOWN_PATTERN.sub("", _text)
        # remove urls
        _text = URL_PATTERN.sub("", _text)
        # remove html tags
        _text = HTML_PATTERN.sub("", _text)
        # remove punctuation
        _text = re.sub(r"[^\w\s]", "", _text)
        # remove emojis
        _text = EMOJI_PATTERN.sub(r"", _text)
        _text = EMOJI_ALT_PATTERN.sub(r"", _text)
        _text = EMOTICON_PATTERN.sub(r"", _text)
        # remove numbers
        _text = re.sub(r"\d+\.?\d*", "", _text)
        # stemming
        _text = " ".join([self._stemmer.stem(w) for w in _text.split()])
        # remove stop words
        _text = " ".join([w for w in _text.split() if w not in STOPWORDS])
        return _text

    def _get_text_features(self, text: str) -> np.ndarray:
        """
        Preprocess and vectorized text.
        """
        _text = self._preprocess_text(text)
        return self._vectorizer.transform([_text]).toarray()[0]

    def _get_issue_features(
        self, issue: Dataset, newcomer_thres: int
    ) -> Dict[str, Any]:
        # ---------- Newcomer Features ----------
        # if the issue resolver is a newcomer, it is a ground-truth gfi
        is_gfi = self._is_user_newcomer(issue.resolver_commit_num, newcomer_thres)
        rpt_is_new = self._is_user_newcomer(
            issue.reporter_feat.n_commits, newcomer_thres
        )
        rpt_gfi_ratio = self._get_newcomer_ratio(
            issue.reporter_feat.resolver_commits, newcomer_thres
        )
        owner_gfi_ratio = self._get_newcomer_ratio(
            issue.owner_feat.resolver_commits, newcomer_thres
        )
        owner_gfi_num = self._get_newcomer_num(
            issue.owner_feat.resolver_commits, newcomer_thres
        )
        pro_gfi_ratio = self._get_newcomer_ratio(
            issue.prev_resolver_commits, newcomer_thres
        )
        pro_gfi_num = self._get_newcomer_num(
            issue.prev_resolver_commits, newcomer_thres
        )

        # ---------- User Features ----------
        commenter = self._get_user_feature_avg(issue.comment_users, newcomer_thres)
        eventer = self._get_user_feature_avg(issue.event_users, newcomer_thres)
        comment_num = len(issue.comments)
        event_num = len(issue.events)

        issue_features = {
            # ---------- Ground Truth ----------
            # !!!! remove in training data !!!!
            "owner": issue.owner,
            "name": issue.name,
            "number": issue.number,
            "is_gfi": is_gfi,
            # tz-aware pymongo datetime makes pandas confused
            # Note: this walkaround is not necessary in pandas 1.4.0-1.4.2, but 1.4.3 reverted so :(
            "created_at": issue.created_at.replace(tzinfo=None)
            if issue.created_at
            else None,
            "closed_at": issue.closed_at.replace(tzinfo=None)
            if issue.closed_at
            else None,
            # "title": issue.title,
            # "body": issue.body,
            # ---------- Testing ----------
            # "_number": issue.number,
            "created_at_timestamp": int(issue.created_at.timestamp()),
            # ---------- Content ----------
            "len_title": issue.len_title,
            "len_body": issue.len_body,
            "n_code_snips": issue.n_code_snips,
            "n_urls": issue.n_urls,
            "n_imgs": issue.n_urls,
            "coleman_liau_index": issue.coleman_liau_index,
            "flesch_reading_ease": issue.flesch_reading_ease,
            "flesch_kincaid_grade": issue.flesch_kincaid_grade,
            "automated_readability_index": issue.automated_readability_index,
            "bug_num": issue.label_category.bug,
            "feature_num": issue.label_category.feature,
            "test_num": issue.label_category.test,
            "build_num": issue.label_category.build,
            "doc_num": issue.label_category.doc,
            "coding_num": issue.label_category.coding,
            "enhance_num": issue.label_category.enhance,
            "gfi_num": issue.label_category.gfi,
            "medium_num": issue.label_category.medium,
            "major_num": issue.label_category.major,
            "triaged_num": issue.label_category.triaged,
            "untriaged_num": issue.label_category.untriaged,
            # ---------- Background ----------
            "rpt_is_new": rpt_is_new,
            "rpt_gfi_ratio": rpt_gfi_ratio,
            "rpt_commits_num": issue.reporter_feat.n_commits,
            "rpt_issues_num": issue.reporter_feat.n_issues,
            "rpt_pulls_num": issue.reporter_feat.n_pulls,
            "rpt_repo_num": issue.reporter_feat.n_repos,
            "rpt_commits_num_all": issue.reporter_feat.n_commits_all,
            "rpt_issues_num_all": issue.reporter_feat.n_issues_all,
            "rpt_pulls_num_all": issue.reporter_feat.n_pulls_all,
            "rpt_reviews_num_all": issue.reporter_feat.n_reviews_all,
            "rpt_max_stars_commit": issue.reporter_feat.max_stars_commit,
            "rpt_max_stars_issue": issue.reporter_feat.max_stars_issue,
            "rpt_max_stars_pull": issue.reporter_feat.max_stars_pull,
            "rpt_max_stars_review": issue.reporter_feat.max_stars_review,
            "owner_gfi_ratio": owner_gfi_ratio,
            "owner_gfi_num": owner_gfi_num,
            "owner_commits_num": issue.owner_feat.n_commits,
            "owner_issues_num": issue.owner_feat.n_issues,
            "owner_pulls_num": issue.owner_feat.n_pulls,
            "owner_repo_num": issue.owner_feat.n_repos,
            "owner_commits_num_all": issue.owner_feat.n_commits_all,
            "owner_issues_num_all": issue.owner_feat.n_issues_all,
            "owner_pulls_num_all": issue.owner_feat.n_pulls_all,
            "owner_reviews_num_all": issue.owner_feat.n_reviews_all,
            "owner_max_stars_commit": issue.owner_feat.max_stars_commit,
            "owner_max_stars_issue": issue.owner_feat.max_stars_issue,
            "owner_max_stars_pull": issue.owner_feat.max_stars_pull,
            "owner_max_stars_review": issue.owner_feat.max_stars_review,
            "pro_gfi_ratio": pro_gfi_ratio,
            "pro_gfi_num": pro_gfi_num,
            "n_stars": issue.n_stars,
            "n_pulls": issue.n_pulls,
            "n_commits": issue.n_commits,
            "n_contributors": issue.n_contributors,
            "n_closed_issues": issue.n_closed_issues,
            "n_open_issues": issue.n_open_issues,
            "r_open_issues": issue.r_open_issues,
            "issue_close_time": issue.issue_close_time,
            # ---------- Dynamics ----------
            # "comments": comments,
            "comment_num": comment_num,
            "event_num": event_num,
        }
        for k, v in commenter.items():
            issue_features["commenter_" + k] = v
        for k, v in eventer.items():
            issue_features["eventer_" + k] = v

        # ---------- Text Features ----------
        if self._use_text_features:
            comments = " ".join(issue.comments)
            _comments_features = self._get_text_features(comments)
            for i in range(len(_comments_features)):
                issue_features["text_comments_" + str(i)] = _comments_features[i]

            title = issue.title
            _title_features = self._get_text_features(title)
            for i in range(len(_title_features)):
                issue_features["text_title_" + str(i)] = _title_features[i]

            body = issue.body
            _body_features = self._get_text_features(body)
            for i in range(len(_body_features)):
                issue_features["text_body_" + str(i)] = _body_features[i]
        return issue_features

    def _load_from_db(
        self, queries: List[Q], newcomer_thres: int, chunk_size: int = 1000
    ) -> pd.DataFrame:
        """
        Load dataset from the database.
        :param queries: The queries to filter the issues.
        :param newcomer_thres: The #commits threshold of newcomers.
        :param chunk_size: Split querie results into chunks to save memory. (default: 1000, 0 to disable)
        :return: dataset (pd.DataFrame)
        """

        df_data = pd.DataFrame()
        __start_time = time.time()

        for q in queries:
            _start_time = time.time()
            _issue_counter = 0
            while True:
                _feat_list = []
                if chunk_size > 0:
                    _q = (
                        Dataset.objects(q)
                        .order_by("-before")
                        .skip(_issue_counter)
                        .limit(chunk_size)
                    )
                else:
                    _q = Dataset.objects(q).order_by("-before")
                # # err: query memory limit exceeded
                # if self._drop_open_issues:
                #     _q = _q.filter(closed_at__ne=None)
                for issue in _q:
                    issue_feat = self._get_issue_features(issue, newcomer_thres)
                    _feat_list.append(issue_feat)
                _df = pd.DataFrame(_feat_list)
                df_data = pd.concat([df_data, _df], ignore_index=True)
                _issue_counter += len(_feat_list)
                self._logger.debug(
                    f"{time.time() - _start_time}s query {q}: {_issue_counter} issues loaded"
                )
                if chunk_size <= 0 or len(_feat_list) < chunk_size:
                    break

        # empty dataframe
        if len(df_data) == 0:
            self._logger.warning("empty dataframe: query=%s", queries)
            return pd.DataFrame()

        # drop insignificant columns
        if self._drop_insignificant_features:
            df_data = df_data.drop(
                columns=df_data.filter(INSIGNIFICANT_FEATURES.keys())
            )

        # drop open issues
        if self._drop_open_issues:
            df_data = df_data.dropna(subset=["closed_at"])
            self._logger.debug(f"{len(df_data)} issues after dropping open issues")

        # dedup -> use the latest record
        if self._just_latest_record:
            df_data = df_data.drop_duplicates(subset=["name", "owner", "number"])
            self._logger.debug(f"{len(df_data)} issues after dedup")

        # downcast df
        if self._downcast_df:
            df_data = downcast_df(df_data)
            self._logger.debug("mem: %d", df_data.memory_usage(index=True).sum())

        # undersample the negatives
        if self._balance_samples:
            p_train = df_data[df_data["is_gfi"] == 1]
            n_train = df_data[df_data["is_gfi"] == 0]
            if p_train.shape[0] != 0:
                n_train = n_train.sample(
                    frac=p_train.shape[0] / n_train.shape[0],
                    replace=True,
                    random_state=self._random_seed,
                )
            df_data = pd.concat([p_train, n_train], ignore_index=True)
            # df_data = pd.concat([p_train, n_train.reindex(p_train.columns)])
        self._logger.info(
            f"{len(df_data)} issues loaded for {queries} in {time.time() - __start_time}s"
        )

        return df_data

    def load_dataset(
        self,
        queries: List[Q],
        newcomer_thres: int,
        chunk_size: int = 1000,
        with_workers: Union[bool, int] = True,
        queries_per_worker: int = 1,
    ) -> pd.DataFrame:
        """
        Load dataset from the database
        :param queries: The queries to filter the issues
        :param newcomer_thres: The #commits threshold of newcomers
        :param chunk_size: Split query results into chunks to save memory. (default: 1000, 0 to disable)
        :param with_workers: Use workers to load the dataset (default: True, False to disable multiprocessing)
        :param queries_per_worker: The number of queries per worker (default: 1)
        :return: full dataset (pd.DataFrame)
        """

        if with_workers is False:
            df_dataset = self._load_from_db(queries, newcomer_thres, chunk_size)
        else:
            if with_workers is True or with_workers == 0:
                with_workers = 0
                self._logger.info(
                    "Using %d processes to load the dataset", _get_default_n_workers()
                )

            queries_splited = []
            for i in range(len(queries) // queries_per_worker):
                queries_splited.append(
                    queries[i * queries_per_worker : (i + 1) * queries_per_worker]
                )

            def dataloader_wrapper(q: List[Q]):
                try:
                    return self._load_from_db(q, newcomer_thres, chunk_size)
                except Exception as e:
                    self._logger.error(
                        "error in dataloader_wrapper: args=%s: %s", q, e, exc_info=True
                    )
                    return pd.DataFrame()

            reconnect_mongoengine()
            df_dataset = parallel(
                dataloader_wrapper,
                queries_splited,
                agg_func=agg_append_df,
                n_workers=with_workers,
            )

            # reindex df_dataset
            df_dataset = df_dataset.reset_index(drop=True)

            if self._use_text_features:
                # apply tf-idf
                for _text_type in ("title", "body", "comments"):
                    _cols = [
                        col for col in df_dataset.columns if f"text_{_text_type}" in col
                    ]
                    if len(_cols) > 0:
                        self._logger.info(
                            "tf-idf: %d %s columns", len(_cols), _text_type
                        )
                        _df = df_dataset[_cols]
                        _df = _df.fillna(0)
                        _transformed = self._transformer.fit_transform(_df)
                        df_dataset = df_dataset.drop(columns=_cols)
                        df_dataset = pd.concat(
                            [
                                df_dataset,
                                pd.DataFrame(_transformed.toarray(), columns=_cols),
                            ],
                            axis=1,
                        )

        self._logger.info(f"{len(df_dataset)} issues loaded")

        return df_dataset
