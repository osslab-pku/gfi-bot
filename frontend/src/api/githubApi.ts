import { asyncRequest, RequestParams } from './query';
import { userInfo } from '../storage';
import {
  GitHubIssueResponse,
  GitHubRepoPermissions,
  GitHubHTTPResponse,
} from '../model/github';

export const requestGitHub = async <T>(params: RequestParams) => {
  // if token exists, add token to headers
  const { githubToken } = userInfo()
  if (githubToken)
    params.headers = {"Authorization": `token ${githubToken}`}
  const res = await asyncRequest<GitHubHTTPResponse<T>>(params);
  if (!res) return undefined;
  if (res && !res.error) {
    return res.data? res.data : res;
  } else if (typeof params.onError === "function") {
    // normally when an error occurs, status code != 200
    // but in this case, we want to keep the compatibility
    params.onError(new Error(String(res.error)));
  }
  return undefined;
}

/** redirect to gh oauth login */
const gitHubOAuthLogin = async () => {
  return await asyncRequest<string>({
    url: '/api/user/github/login',
  });
};

export const gitHubLogin = () => {
  const { hasLogin, name } = userInfo();
  if (hasLogin && name !== undefined) {
    window.location.reload();
    return;
  }
  gitHubOAuthLogin().then((url) => {
    if (url) {
      window.location.assign(url);
    }
  });
};

export const checkGithubLogin = async () => {
  const { githubLogin, githubToken } = userInfo();
  if (githubToken) {
    const res = await requestGitHub<any>({
      url: `https://api.github.com/users/${githubLogin}`,
    });
    if (res) return true;
  }
  return false;
};

/** User must have write access */
export const checkHasRepoPermissions = async (
  repoName: string,
  owner: string
) => {
  const { hasLogin, githubToken } = userInfo()
  if (!hasLogin) return false;
  const res = await requestGitHub<{ permissions: GitHubRepoPermissions }>({
    url: `https://api.github.com/repos/${owner}/${repoName}`,
  });
  if (!res || !res.permissions) return false;
  return (!!res.permissions.maintain) || (!!res.permissions.admin) || (!!res.permissions.push) ;
};

export const getIssueByRepoInfo = async (
  repoName: string,
  owner?: string,
  issueId?: string | number
) => {
  // url such as https://api.github.com/repos/pallets/flask/issues/4333
  const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueId}`;
  return await requestGitHub<Partial<GitHubIssueResponse>>({url});
};
