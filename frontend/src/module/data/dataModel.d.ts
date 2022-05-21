export type KeyMap = { [key: string]: any };

export type StandardHTTPResponse<T extends KeyMap> = {
  [key: string]: any;
  status: number;
  data?: KeyMap & T;
};

export interface GFIRepoInfo {
  name: string;
  owner: string;
  description?: string;
  url?: string;
  topics?: string[];
}

export type GetRepoDetailedInfo = {
  name?: string;
  description?: string;
  language?: string[];
  monthly_stars?: string[];
  monthly_commits?: string[];
  monthly_issues?: string[];
  monthly_pulls?: string[];
};

export type RepoPermissions = {
  admin: boolean;
  maintain: boolean;
  push: boolean;
  triage: boolean;
  pull: boolean;
};

export type GFIUserQueryHistoryItem = {
  pending: boolean;
  repo: GFIRepoInfo;
};

export type GFIInfo = {
  name: string;
  owner: string;
  probability: number;
  number: number;
  last_updated: string;
};

export type GitHubIssueResponse = {
  number: number;
  title: string;
  state: string;
  active_lock_reason: string;
  body: string;
  html_url: string;
};

export type GFITrainingSummary = {
  name: string;
  owner: string;
  issues_train: number;
  issues_test: number;
  n_resolved_issues: number;
  n_newcomer_resolved: number;
  accuracy: number;
  auc: number;
  last_updated: string;
};

export type GFIRepoConfig = {
  newcomer_threshold: number;
  gfi_threshold: number;
  need_comment: boolean;
  issue_tag: string;
};

export type GFIRepoUpdateConfig = {
  interval: number;
  begin_time: string;
};

export type GFIUserSearch = {
  name: string;
  owner: string;
  created_at: string;
  increment: number;
};
