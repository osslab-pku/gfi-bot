from typing import List, Tuple, TypeVar, Generic, Dict, Any, Optional, Final
from enum import Enum
from datetime import datetime

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class GFIResponse(GenericModel, Generic[T]):
    code: int = 200
    result: T


class RepoQuery(BaseModel):
    owner: str
    name: str


### Repo Models ###


class RepoBrief(BaseModel):
    name: str
    owner: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str] = []
    stars: Optional[int] = 0
    forks: Optional[int] = 0
    contributors_count: Optional[int] = 0
    n_gfis: Optional[int] = 0


class MonthlyCount(BaseModel):
    month: datetime
    count: int


class RepoDetail(BaseModel):
    name: str
    owner: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str] = []
    stars: Optional[int] = 0
    forks: Optional[int] = 0
    contributors_count: Optional[int] = 0
    n_gfis: Optional[int] = 0
    monthly_stars: List[MonthlyCount] = []
    monthly_commits: List[MonthlyCount] = []
    monthly_issues: List[MonthlyCount] = []
    monthly_pulls: List[MonthlyCount] = []


class RepoSort(Enum):
    STARS = "popularity"
    GFIS = "gfis"
    ISSUE_CLOSE_TIME = "median_issue_resolve_time"
    NEWCOMER_RESOLVE_RATE = "newcomer_friendly"


class IssueSort(Enum):
    PROBABILITY_DESC = "probability_desc"
    PROBABILITY_ASC = "probability_asc"
    NEWEST = "newest"
    OLDEST = "oldest"


class UserSearchedRepo(BaseModel):
    name: str
    owner: str
    created_at: datetime
    increment: int


### GFI Config Models ###


class UpdateConfig(BaseModel):
    task_id: str
    interval: int
    begin_time: datetime


class RepoConfig(BaseModel):
    newcomer_threshold: int
    gfi_threshold: float
    need_comment: bool
    issue_tag: str


class Config(BaseModel):
    update_config: UpdateConfig
    repo_config: RepoConfig


### GFI Data Models ###


class GFIBrief(BaseModel):
    name: str
    owner: str
    number: int
    threshold: float
    probability: float
    last_updated: datetime
    state: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    labels: List[str] = []
    has_pending_pr: bool = False
    created_at: Optional[datetime] = None
    html_url: Optional[str] = None
    gfi_probability_percentage: Optional[str] = None



class TrainingResult(BaseModel):
    owner: str
    name: str
    issues_train: int
    issues_test: int
    n_resolved_issues: int
    n_newcomer_resolved: int
    accuracy: Optional[float]
    auc: Optional[float]
    last_updated: datetime


### GitHub API Data Models ###


class GitHubRepo(BaseModel):
    full_name: str
    name: str

    @property
    def owner(self) -> str:
        return self.full_name.split("/")[0]


class GitHubAppWebhookResponse(BaseModel):
    sender: Dict[str, Any]
    action: str
    issue: Optional[Dict[str, Any]]
    repository: Optional[GitHubRepo]
    repositories: Optional[List[GitHubRepo]]
    repositories_added: Optional[List[GitHubRepo]]
    repositories_removed: Optional[List[GitHubRepo]]


class GitHubUserInfo(BaseModel):
    id: str
    login: str
    name: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    twitter_username: Optional[str] = None


### Chatbot Models ###


class ChatMessageModel(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ChatbotSessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    expertise_level: str = "beginner"
    repo_name: Optional[str] = None
    owner: Optional[str] = None


class ChatbotSessionResponse(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    expertise_level: str
    repo_name: Optional[str] = None
    owner: Optional[str] = None
    messages: List[ChatMessageModel] = []
    created_at: datetime
    updated_at: datetime


class ChatbotQueryRequest(BaseModel):
    session_id: str
    message: str


class ChatbotQueryResponse(BaseModel):
    session_id: str
    reply: str
    expertise_level: str
    history: List[ChatMessageModel]


### Model Evaluation Models ###


class ModelCompModel(BaseModel):
    model_name: str
    accuracy: Optional[float]
    auc: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1: Optional[float]
    best_params: Dict[str, Any] = {}


class AblationStudyModel(BaseModel):
    feature_group: str
    auc: Optional[float]
    f1: Optional[float]


class FeatureImportanceModel(BaseModel):
    feature_name: str
    importance: float


class ModelEvaluationResponse(BaseModel):
    owner: str
    name: str
    threshold: int
    evaluation_time: datetime
    model_comparisons: List[ModelCompModel] = []
    ablation_studies: List[AblationStudyModel] = []
    feature_importances: List[FeatureImportanceModel] = []


