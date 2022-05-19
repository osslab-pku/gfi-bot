import { asyncRequest, BASE_URL } from './query';
import {
  GetRepoDetailedInfo,
  GFIInfo,
  GFIRepoInfo,
  GFITrainingSummary,
} from '../module/data/dataModel';
import { store } from '../module/storage/configureStorage';

export const userInfo = () => {
  return [
    store.getState().loginReducer.hasLogin,
    store.getState().loginReducer.name,
    store.getState().loginReducer.loginName,
    store.getState().loginReducer.token,
  ];
};

export const getRepoNum = async (lang?: string) => {
  return await asyncRequest<number | undefined>({
    url: '/api/repos/num',
    params: {
      lang,
    },
    baseURL: BASE_URL,
  });
};

export const getIssueNum = async () => {
  return await asyncRequest<number | undefined>({
    url: '/api/issue/num',
    baseURL: BASE_URL,
  });
};

export const getPagedRepoDetailedInfo = async (
  beginIdx: string | number,
  capacity: string | number,
  lang?: string,
  filter?: string
) => {
  return await asyncRequest<GetRepoDetailedInfo>({
    url: '/api/repos/info/paged',
    params: {
      start: beginIdx,
      length: capacity,
      lang,
      filter,
    },
    baseURL: BASE_URL,
  });
};

export const getRepoDetailedInfo = async (name: string, owner: string) => {
  return await asyncRequest<GetRepoDetailedInfo>({
    url: '/api/repos/info/detail',
    params: {
      name,
      owner,
    },
    baseURL: BASE_URL,
  });
};

export const searchRepoInfoByNameOrURL = async (
  repoName?: string,
  repoURL?: string
) => {
  const [hasLogin, userName] = userInfo();
  return await asyncRequest<GFIRepoInfo>({
    url: '/api/repos/info/search',
    params: {
      repo: repoName,
      url: repoURL,
      user: userName,
    },
    baseURL: BASE_URL,
  });
};

export const getGFIByRepoName = async (repoName: string, repoOwner: string) => {
  return await asyncRequest<GFIInfo | undefined>({
    url: '/api/issue/gfi',
    params: {
      repo: repoName,
      owner: repoOwner,
    },
    baseURL: BASE_URL,
  });
};

export const getGFINum = async (repoName?: string, repoOwner?: string) => {
  return await asyncRequest<number | undefined>({
    url: '/api/issue/gfi/num',
    params: {
      repo: repoName,
      owner: repoOwner,
    },
    baseURL: BASE_URL,
  });
};

export const getLanguageTags = async () => {
  return await asyncRequest<string[] | undefined>({
    url: '/api/repos/language',
    baseURL: BASE_URL,
  });
};

export const addRepoToGFIBot = async (repoName: string, repoOwner: string) => {
  const [hasLogin, _, loginName] = userInfo();
  return await asyncRequest<any>({
    method: 'POST',
    url: '/api/repos/add',
    headers: {
      'Content-Type': 'application/json',
    },
    data: {
      user: loginName,
      repo: repoName,
      owner: repoOwner,
    },
    baseURL: BASE_URL,
  });
};

export const getAddRepoHistory = async () => {
  const [_, __, loginName] = userInfo();
  return await asyncRequest<{
    nums?: number;
    queries: GFIRepoInfo[];
    finished_queries?: GFIRepoInfo[];
  }>({
    url: '/api/user/queries',
    params: {
      user: loginName,
    },
    baseURL: BASE_URL,
  });
};

export const getTrainingSummary = async (name?: string, owner?: string) => {
  return await asyncRequest<GFITrainingSummary[] | undefined>({
    url: '/api/model/training/result',
    params: {
      name,
      owner,
    },
    baseURL: BASE_URL,
  });
};
