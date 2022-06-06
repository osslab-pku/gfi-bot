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
        model_file: relative path to the model file, with repository as root.
        n_resolved_issues: total number of resolved issues in this repository.
        n_newcomer_resolved: the number of issues resolved by newcomers in this repository.
        accuracy: the accuracy of the model on the training data.
        auc: the area under the ROC curve.
        last_updated: the last time this training summary was updated.
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    issues_train: List[list] = ListField(ListField(), default=[])
    issues_test: List[list] = ListField(ListField(), default=[])
    threshold: int = IntField(required=True, min_value=1, max_value=5)
    model_90_file: str = StringField(required=True)
    model_full_file: str = StringField(required=True)
    n_resolved_issues: int = IntField(required=True)
    n_newcomer_resolved: int = IntField(required=True)
    accuracy: float = FloatField(required=True)
    auc: float = FloatField(required=True)
    last_updated: datetime = DateTimeField(required=True)
    meta = {
        "indexes": [
            {"fields": ["owner", "name", "threshold"], "unique": True},
        ]
    }
