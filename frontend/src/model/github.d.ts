type AnyObject = { [key: string]: any };

export type GitHubHTTPResponse<T extends AnyObject> = {
  [key: string]: any;
  status: number;
  data?: T;
};

export type GitHubIssueResponse = {
  number: number;
  title: string;
  state: string;
  active_lock_reason: string;
  body: string;
  html_url: string;
};

export type GitHubRepoPermissions = {
  admin: boolean;
  maintain: boolean;
  push: boolean;
  triage: boolean;
  pull: boolean;
};
