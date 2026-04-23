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

#Light-weight repository object used for search results or list views where heavy metrics aren't required
class RepoBrief(BaseModel):
    name: str
    owner: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str]

# represents data point for time-series charts
class MonthlyCount(BaseModel):
    month: datetime
    count: int

# Full repository profile including health metrics and activity history
class RepoDetail(BaseModel):
    name: str
    owner: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str]
    monthly_stars: List[MonthlyCount]
    monthly_commits: List[MonthlyCount]
    monthly_issues: List[MonthlyCount]
    monthly_pulls: List[MonthlyCount]

# Criteria for ranking repositories in the discovery UI
class RepoSort(Enum):
    STARS = "popularity"
    GFIS = "gfis"
    ISSUE_CLOSE_TIME = "median_issue_resolve_time"
    NEWCOMER_RESOLVE_RATE = "newcomer_friendly"

# Logs when a user expresses interest in a repo, likely for "Trending" algorithms
class UserSearchedRepo(BaseModel):
    name: str
    owner: str
    created_at: datetime
    increment: int


### GFI Config Models ###

# Controls the background worker task that syncs GitHub data.
class UpdateConfig(BaseModel):
    task_id: str
    interval: int
    begin_time: datetime

#Heuristics used to tune the GFI detection algorithm for a specific project.
class RepoConfig(BaseModel):
    newcomer_threshold: int
    gfi_threshold: float
    need_comment: bool
    issue_tag: str


class Config(BaseModel):
    update_config: UpdateConfig
    repo_config: RepoConfig


### GFI Data Models ###

# an individual issue that has been analyzed by the GFI model
class GFIBrief(BaseModel):
    name: str
    owner: str
    number: int
    threshold: float
    probability: float
    last_updated: datetime
    state: Optional[str] = None
    title: Optional[str] = None

# performance metrics for the ML model specific to one repository's history
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

# Helper model to map github's "owner/repo" string back to the internal owner field
class GitHubRepo(BaseModel):
    full_name: str
    name: str

    @property
    def owner(self) -> str:
        return self.full_name.split("/")[0]

# flexible schema to handle various events from github webhooks
class GitHubAppWebhookResponse(BaseModel):
    sender: Dict[str, Any]
    action: str
    issue: Optional[Dict[str, Any]]
    repository: Optional[GitHubRepo]
    repositories: Optional[List[GitHubRepo]]
    repositories_added: Optional[List[GitHubRepo]]
    repositories_removed: Optional[List[GitHubRepo]]

# user profile data used for authentication or attributing issues
class GitHubUserInfo(BaseModel):
    id: str
    login: str
    name: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    twitter_username: Optional[str] = None
