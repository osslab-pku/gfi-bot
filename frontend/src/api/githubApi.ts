import { store } from '../module/storage/configureStorage';
import { asyncRequest, BASE_URL } from './query';
import { userInfo } from './api';
import {
  GitHubIssueResponse,
  RepoPermissions,
  StandardHTTPResponse,
} from '../module/data/dataModel';

export const gitHubLogin = () => {
  const [hasLogin, userName] = userInfo();
  if (hasLogin && userName !== undefined) {
    window.location.reload();
    return;
  }
  gitHubOAuthLogin().then((url: string) => {
    window.location.assign(url);
  });
};

export const checkGithubLogin = async () => {
  const userToken = store.getState().loginReducer.token;
  const userLoginName = store.getState().loginReducer.loginName;
  if (userToken) {
    const res = await asyncRequest<StandardHTTPResponse<any>>({
      url: `https://api.github.com/users/${userLoginName}`,
      headers: {
        Authorization: `token ${userToken}`,
      },
      customRequestResponse: false,
    });
    if (res?.status === 200) {
      return true;
    }
  }
  return false;
};

const gitHubOAuthLogin = async () => {
  return await asyncRequest<string>({
    url: '/api/user/github/login',
    baseURL: BASE_URL,
  });
};

export const checkHasRepoPermissions = async (
  repoName: string,
  owner: string
) => {
  const { hasLogin } = store.getState().loginReducer;
  const userToken = store.getState().loginReducer.token;
  if (!hasLogin) {
    return false;
  }
  const res = await asyncRequest<
    StandardHTTPResponse<{ permissions?: RepoPermissions }>
  >({
    url: `https://api.github.com/repos/${owner}/${repoName}`,
    headers: {
      Authorization: `token ${userToken}`,
    },
    customRequestResponse: false,
  });

  if (res === undefined) return false;
  return !!res.data?.permissions?.maintain;
};

export const getIssueByRepoInfo = async (
  repoName: string,
  owner?: string,
  issueId?: string | number
) => {
  // url such as https://api.github.com/repos/pallets/flask/issues/4333

  const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueId}`;
  const { hasLogin } = store.getState().loginReducer;
  const userToken = store.getState().loginReducer.token;
  const headers: any | undefined =
    hasLogin && userToken ? { Authorization: `token ${userToken}` } : undefined;

  return await asyncRequest<StandardHTTPResponse<Partial<GitHubIssueResponse>>>(
    {
      url,
      headers,
      customRequestResponse: false,
    }
  );
};
