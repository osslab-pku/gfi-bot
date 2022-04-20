from datetime import datetime, timezone
from pandas.testing import assert_frame_equal
import os
import sys

current_work_dir = os.path.dirname(__file__)
utpath = os.path.join(current_work_dir, "../..")
sys.path.append(utpath)
from gfibot.collections import *
from gfibot.model.predictor import *
from gfibot.model.utils import *
from tests.conftest import *


def test_util():
    assert cat_comment("```comment```" "```comment```") == "```comment``````comment```"

    assert user_new(0, 1) == 1
    assert user_new(1, 2) == 1
    assert user_new(2, 3) == 1
    assert user_new(5, 4) == 0
    assert user_new(6, 5) == 0
    assert user_new(3, 3) == 0

    assert get_ratio(None, 1) == 0
    assert get_ratio([1, 2, 3, None, 4, 5], 3) == 0.4
    assert get_ratio([10, 12, 14, 0], 2) == 0.25

    assert get_num(None, 1) == 0
    assert get_num([None, None], 1) == 0
    assert get_num([1, 3, 4, 7, 10], 4) == 2


def test_get_user_average(mock_mongodb):
    issue = Dataset.objects(name="name", owner="owner", number=5).first()
    commits_num, issues_num, pulls_num, user_gfi_ratio, user_gfi_num = get_user_average(
        issue.comment_users, 2
    )
    assert commits_num == 4
    assert issues_num == 1
    assert pulls_num == 1.5
    assert user_gfi_ratio == 0.25
    assert user_gfi_num == 0.5


def test_load_data(mock_mongodb):
    threshold = 1
    batch = [["name", "owner", [5, datetime(1970, 1, 3, tzinfo=timezone.utc)]]]
    df_diff = assert_frame_equal(
        load_data(threshold, batch),
        pd.DataFrame(
            [
                {
                    "owner": "owner",
                    "name": "name",
                    "number": 5,
                    "is_gfi": 0,
                    "len_title": 1,
                    "len_body": 1,
                    "n_code_snips": 0,
                    "n_urls": 0,
                    "n_imgs": 0,
                    "coleman_liau_index": 0.1,
                    "flesch_reading_ease": 0.1,
                    "flesch_kincaid_grade": 0.1,
                    "automated_readability_index": 0.1,
                    "bug_num": 0,
                    "feature_num": 0,
                    "test_num": 0,
                    "build_num": 0,
                    "doc_num": 0,
                    "coding_num": 0,
                    "enhance_num": 0,
                    "gfi_num": 1,
                    "medium_num": 0,
                    "major_num": 0,
                    "triaged_num": 0,
                    "untriaged_num": 0,
                    "rpt_is_new": 0,
                    "rpt_gfi_ratio": 0.0,
                    "owner_gfi_ratio": 0.0,
                    "owner_gfi_num": 0,
                    "pro_gfi_ratio": 0,
                    "pro_gfi_num": 0,
                    "n_stars": 0,
                    "n_pulls": 1,
                    "n_commits": 5,
                    "n_contributors": 2,
                    "n_closed_issues": 1,
                    "n_open_issues": 1,
                    "r_open_issues": 1.0,
                    "issue_close_time": 1.0,
                    "commenter_commits_num": 4.0,
                    "commenter_issues_num": 1.0,
                    "commenter_pulls_num": 1.5,
                    "commenter_gfi_ratio": 0.0,
                    "commenter_gfi_num": 0.0,
                    "eventer_commits_num": 0,
                    "eventer_issues_num": 0,
                    "eventer_pulls_num": 0,
                    "eventer_gfi_ratio": 0,
                    "eventer_gfi_num": 0,
                    "comment_num": 0,
                    "event_num": 0,
                }
            ]
        ),
    )
    assert df_diff is None


def test_get_issue_data(mock_mongodb):
    issue = Dataset.objects(name="name", owner="owner", number=5).first()
    threshold = 1
    one_issue = get_issue_data(issue, threshold)
    assert one_issue == {
        "owner": "owner",
        "name": "name",
        "number": 5,
        "is_gfi": 0,
        "len_title": 1,
        "len_body": 1,
        "n_code_snips": 0,
        "n_urls": 0,
        "n_imgs": 0,
        "coleman_liau_index": 0.1,
        "flesch_reading_ease": 0.1,
        "flesch_kincaid_grade": 0.1,
        "automated_readability_index": 0.1,
        "bug_num": 0,
        "feature_num": 0,
        "test_num": 0,
        "build_num": 0,
        "doc_num": 0,
        "coding_num": 0,
        "enhance_num": 0,
        "gfi_num": 1,
        "medium_num": 0,
        "major_num": 0,
        "triaged_num": 0,
        "untriaged_num": 0,
        "rpt_is_new": 0,
        "rpt_gfi_ratio": 0.0,
        "owner_gfi_ratio": 0.0,
        "owner_gfi_num": 0,
        "pro_gfi_ratio": 0,
        "pro_gfi_num": 0,
        "n_stars": 0,
        "n_pulls": 1,
        "n_commits": 5,
        "n_contributors": 2,
        "n_closed_issues": 1,
        "n_open_issues": 1,
        "r_open_issues": 1.0,
        "issue_close_time": 1.0,
        "commenter_commits_num": 4.0,
        "commenter_issues_num": 1.0,
        "commenter_pulls_num": 1.5,
        "commenter_gfi_ratio": 0.0,
        "commenter_gfi_num": 0.0,
        "eventer_commits_num": 0,
        "eventer_issues_num": 0,
        "eventer_pulls_num": 0,
        "eventer_gfi_ratio": 0,
        "eventer_gfi_num": 0,
        "comment_num": 0,
        "event_num": 0,
    }


def test_update_model(mock_mongodb):
    model_path = None
    threshold = 2
    train_add = [
        ["name", "owner", [5, datetime(1970, 1, 3, tzinfo=timezone.utc)]],
        ["name", "owner", [6, datetime(1971, 1, 3, tzinfo=timezone.utc)]],
    ]
    batch_size = 100
    assert isinstance(
        update_model(model_path, threshold, train_add, batch_size), xgb.core.Booster
    )


def test_load_train_data():
    data = pd.DataFrame(
        [
            {
                "owner": "owner",
                "name": "name",
                "number": 6,
                "is_gfi": 1,
                "len_title": 1,
                "len_body": 1,
                "n_code_snips": 0,
                "n_urls": 0,
                "n_imgs": 0,
                "coleman_liau_index": 0.1,
                "flesch_reading_ease": 0.1,
                "flesch_kincaid_grade": 0.1,
                "automated_readability_index": 0.1,
                "bug_num": 0,
                "feature_num": 0,
                "test_num": 0,
                "build_num": 0,
                "doc_num": 0,
                "coding_num": 0,
                "enhance_num": 0,
                "gfi_num": 1,
                "medium_num": 0,
                "major_num": 0,
                "triaged_num": 0,
                "untriaged_num": 0,
                "rpt_is_new": 0,
                "rpt_gfi_ratio": 0.0,
                "owner_gfi_ratio": 0.0,
                "owner_gfi_num": 0,
                "pro_gfi_ratio": 0,
                "pro_gfi_num": 0,
                "n_stars": 0,
                "n_pulls": 1,
                "n_commits": 5,
                "n_contributors": 2,
                "n_closed_issues": 1,
                "n_open_issues": 1,
                "r_open_issues": 1.0,
                "issue_close_time": 1.0,
                "commenter_commits_num": 4.0,
                "commenter_issues_num": 1.0,
                "commenter_pulls_num": 1.5,
                "commenter_gfi_ratio": 0.0,
                "commenter_gfi_num": 0.0,
                "eventer_commits_num": 0,
                "eventer_issues_num": 0,
                "eventer_pulls_num": 0,
                "eventer_gfi_ratio": 0,
                "eventer_gfi_num": 0,
                "comment_num": 0,
                "event_num": 0,
            },
            {
                "owner": "owner",
                "name": "name",
                "number": 5,
                "is_gfi": 0,
                "len_title": 1,
                "len_body": 1,
                "n_code_snips": 0,
                "n_urls": 0,
                "n_imgs": 0,
                "coleman_liau_index": 0.1,
                "flesch_reading_ease": 0.1,
                "flesch_kincaid_grade": 0.1,
                "automated_readability_index": 0.1,
                "bug_num": 0,
                "feature_num": 0,
                "test_num": 0,
                "build_num": 0,
                "doc_num": 0,
                "coding_num": 0,
                "enhance_num": 0,
                "gfi_num": 1,
                "medium_num": 0,
                "major_num": 0,
                "triaged_num": 0,
                "untriaged_num": 0,
                "rpt_is_new": 0,
                "rpt_gfi_ratio": 0.0,
                "owner_gfi_ratio": 0.0,
                "owner_gfi_num": 0,
                "pro_gfi_ratio": 0,
                "pro_gfi_num": 0,
                "n_stars": 0,
                "n_pulls": 1,
                "n_commits": 5,
                "n_contributors": 2,
                "n_closed_issues": 1,
                "n_open_issues": 1,
                "r_open_issues": 1.0,
                "issue_close_time": 1.0,
                "commenter_commits_num": 4.0,
                "commenter_issues_num": 1.0,
                "commenter_pulls_num": 1.5,
                "commenter_gfi_ratio": 0.0,
                "commenter_gfi_num": 0.0,
                "eventer_commits_num": 0,
                "eventer_issues_num": 0,
                "eventer_pulls_num": 0,
                "eventer_gfi_ratio": 0,
                "eventer_gfi_num": 0,
                "comment_num": 0,
                "event_num": 0,
            },
        ]
    )
    y_train = data["is_gfi"]
    X_train = data.drop(["is_gfi", "owner", "name", "number"], axis=1)
    x, y = load_train_data(data)
    df_diff_x = assert_frame_equal(x, X_train)
    df_diff_y = assert_frame_equal(pd.DataFrame(y), pd.DataFrame(y_train))
    assert df_diff_x is None
    assert df_diff_y is None


def test_load_test_incremental(mock_mongodb):
    test_set = [["name", "owner", [5, datetime(1970, 1, 3, tzinfo=timezone.utc)]]]
    threshold = 1
    data = pd.DataFrame(
        [
            {
                "owner": "owner",
                "name": "name",
                "number": 5,
                "is_gfi": 0,
                "len_title": 1,
                "len_body": 1,
                "n_code_snips": 0,
                "n_urls": 0,
                "n_imgs": 0,
                "coleman_liau_index": 0.1,
                "flesch_reading_ease": 0.1,
                "flesch_kincaid_grade": 0.1,
                "automated_readability_index": 0.1,
                "bug_num": 0,
                "feature_num": 0,
                "test_num": 0,
                "build_num": 0,
                "doc_num": 0,
                "coding_num": 0,
                "enhance_num": 0,
                "gfi_num": 1,
                "medium_num": 0,
                "major_num": 0,
                "triaged_num": 0,
                "untriaged_num": 0,
                "rpt_is_new": 0,
                "rpt_gfi_ratio": 0.0,
                "owner_gfi_ratio": 0.0,
                "owner_gfi_num": 0,
                "pro_gfi_ratio": 0,
                "pro_gfi_num": 0,
                "n_stars": 0,
                "n_pulls": 1,
                "n_commits": 5,
                "n_contributors": 2,
                "n_closed_issues": 1,
                "n_open_issues": 1,
                "r_open_issues": 1.0,
                "issue_close_time": 1.0,
                "commenter_commits_num": 4.0,
                "commenter_issues_num": 1.0,
                "commenter_pulls_num": 1.5,
                "commenter_gfi_ratio": 0.0,
                "commenter_gfi_num": 0.0,
                "eventer_commits_num": 0,
                "eventer_issues_num": 0,
                "eventer_pulls_num": 0,
                "eventer_gfi_ratio": 0,
                "eventer_gfi_num": 0,
                "comment_num": 0,
                "event_num": 0,
            }
        ]
    )
    y_test = data["is_gfi"]
    X_test = data.drop(["is_gfi", "owner", "name"], axis=1)
    x, y = load_test_incremental(test_set, threshold)
    df_diff_x = assert_frame_equal(x, X_test)
    df_diff_y = assert_frame_equal(pd.DataFrame(y), pd.DataFrame(y_test))
    assert df_diff_x is None
    assert df_diff_y is None


def test_predict_issues(mock_mongodb):
    test_set = [["name", "owner", [5, datetime(1970, 1, 3, tzinfo=timezone.utc)]]]
    threshold = 1
    batch_size = 100
    params = {"objective": "binary:logistic"}
    data = pd.DataFrame(
        [
            {
                "owner": "owner",
                "name": "name",
                "number": 6,
                "is_gfi": 1,
                "len_title": 1,
                "len_body": 1,
                "n_code_snips": 0,
                "n_urls": 0,
                "n_imgs": 0,
                "coleman_liau_index": 0.1,
                "flesch_reading_ease": 0.1,
                "flesch_kincaid_grade": 0.1,
                "automated_readability_index": 0.1,
                "bug_num": 0,
                "feature_num": 0,
                "test_num": 0,
                "build_num": 0,
                "doc_num": 0,
                "coding_num": 0,
                "enhance_num": 0,
                "gfi_num": 1,
                "medium_num": 0,
                "major_num": 0,
                "triaged_num": 0,
                "untriaged_num": 0,
                "rpt_is_new": 0,
                "rpt_gfi_ratio": 0.0,
                "owner_gfi_ratio": 0.0,
                "owner_gfi_num": 0,
                "pro_gfi_ratio": 0,
                "pro_gfi_num": 0,
                "n_stars": 0,
                "n_pulls": 1,
                "n_commits": 5,
                "n_contributors": 2,
                "n_closed_issues": 1,
                "n_open_issues": 1,
                "r_open_issues": 1.0,
                "issue_close_time": 1.0,
                "commenter_commits_num": 4.0,
                "commenter_issues_num": 1.0,
                "commenter_pulls_num": 1.5,
                "commenter_gfi_ratio": 0.0,
                "commenter_gfi_num": 0.0,
                "eventer_commits_num": 0,
                "eventer_issues_num": 0,
                "eventer_pulls_num": 0,
                "eventer_gfi_ratio": 0,
                "eventer_gfi_num": 0,
                "comment_num": 0,
                "event_num": 0,
            },
            {
                "owner": "owner",
                "name": "name",
                "number": 5,
                "is_gfi": 0,
                "len_title": 1,
                "len_body": 1,
                "n_code_snips": 0,
                "n_urls": 0,
                "n_imgs": 0,
                "coleman_liau_index": 0.1,
                "flesch_reading_ease": 0.1,
                "flesch_kincaid_grade": 0.1,
                "automated_readability_index": 0.1,
                "bug_num": 0,
                "feature_num": 0,
                "test_num": 0,
                "build_num": 0,
                "doc_num": 0,
                "coding_num": 0,
                "enhance_num": 0,
                "gfi_num": 1,
                "medium_num": 0,
                "major_num": 0,
                "triaged_num": 0,
                "untriaged_num": 0,
                "rpt_is_new": 0,
                "rpt_gfi_ratio": 0.0,
                "owner_gfi_ratio": 0.0,
                "owner_gfi_num": 0,
                "pro_gfi_ratio": 0,
                "pro_gfi_num": 0,
                "n_stars": 0,
                "n_pulls": 1,
                "n_commits": 5,
                "n_contributors": 2,
                "n_closed_issues": 1,
                "n_open_issues": 1,
                "r_open_issues": 1.0,
                "issue_close_time": 1.0,
                "commenter_commits_num": 4.0,
                "commenter_issues_num": 1.0,
                "commenter_pulls_num": 1.5,
                "commenter_gfi_ratio": 0.0,
                "commenter_gfi_num": 0.0,
                "eventer_commits_num": 0,
                "eventer_issues_num": 0,
                "eventer_pulls_num": 0,
                "eventer_gfi_ratio": 0,
                "eventer_gfi_num": 0,
                "comment_num": 0,
                "event_num": 0,
            },
        ]
    )
    y_train = data["is_gfi"]
    X_train = data.drop(["is_gfi", "owner", "name", "number"], axis=1)
    xg_train = xgb.DMatrix(X_train, label=y_train)
    model = xgb.train(params, xg_train, xgb_model=None)
    y_test_all, y_prob_all = predict_issues(test_set, threshold, batch_size, model)
    assert y_test_all == [0]
    assert y_prob_all == [0.5]


def test_get_all_metrics():
    y_test = [1, 0, 1]
    pred_labels = [0, 1, 1]
    y_prob = [0.4, 0.7, 0.8]
    auc_, precision, recall, f1 = get_all_metrics(y_test, pred_labels, y_prob)
    assert auc_ == 0.5
    assert precision == 0.5
    assert recall == 0.5
    assert f1 == 0.5
