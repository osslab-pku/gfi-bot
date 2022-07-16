from typing import List, Union
from datetime import datetime
from mongoengine import *


class Prediction(Document):
    """
    The GFI prediction result for an open issue.
    This collection will be updated periodically and used by backend and bot for GFI recommendation.
    Attributes:
        owner, name, number: uniquely identifies a GitHub issue.
        threshold: the number of in-repository commits that disqualify one as a newcomer,
            can be one to five. For more details please check the ICSE'22 paper.
        probability: the modeled probability that the issue is a GFI.
        last_updated: the last time this prediction result was updated,
            necessary for incremental update.
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True)
    threshold: int = IntField(required=True, min_value=1, max_value=5)
    probability: float = FloatField(required=True)
    last_updated: datetime = DateTimeField(required=True)

    tagged: bool = BooleanField(default=False)
    commented: bool = BooleanField(default=False)

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "number", "threshold"], "unique": True},
            {"fields": ["probability"]},
        ]
    }


class TrainingSummary(Document):
    """
    Describes model training result for a specific repository and threshold.
    This collection will be used to communicate the effectiveness of our model to users.
    Attributes:
        owner, name, threshold: uniquely identifies a GitHub repository and a training setting.
            If owner="", name="", then this is a global summary result.
        n_resolved_issues: total number of resolved issues in this repository.
        n_newcomer_resolved: the number of issues resolved by newcomers in this repository.
        accuracy, auc, precision, recall, f1: performance metrics in this repo.
        last_updated: the last time this training summary was updated.
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    threshold: int = IntField(required=True, min_value=1, max_value=5)
    issues_train: List[list] = ListField(ListField(), default=[])
    issues_test: List[list] = ListField(ListField(), default=[])
    n_resolved_issues: int = IntField(required=True)
    n_newcomer_resolved: int = IntField(required=True)
    accuracy: float = FloatField(null=True)
    auc: float = FloatField(null=True)
    precision: float = FloatField(null=True)
    recall: float = FloatField(null=True)
    f1: float = FloatField(null=True)
    batch_accuracy: List[str] = ListField(StringField(), default=[])
    batch_auc: List[str] = ListField(StringField(), default=[])
    batch_precision: List[str] = ListField(StringField(), default=[])
    batch_recall: List[str] = ListField(StringField(), default=[])
    batch_f1: List[str] = ListField(StringField(), default=[])
    last_updated: datetime = DateTimeField(required=True)

    # -- To accelerate backend sorts --
    r_newcomer_resolved: float = FloatField(null=True)
    n_stars: int = IntField(null=True)
    n_gfis: int = IntField(null=True)
    issue_close_time: float = FloatField(null=True)

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "threshold"], "unique": True},
            "r_newcomer_resolved",
            "n_stars",
            "n_gfis",
            "issue_close_time",
        ]
    }
