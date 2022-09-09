import { requestGFI, getBaseURL } from './query';
import { userInfo } from '../storage';

import type {
  RepoSort,
  RepoBrief,
  RepoDetail,
  RepoGFIConfig,
  SearchedRepo,
  RepoUpdateConfig,
  UserQueryHistory,
  GFIInfo,
  GFITrainingSummary,
  GFIResponse,
  GFIFailure,
} from '../model/api';

export const getRepoNum = async (lang?: string) => {
  return await requestGFI<number>({
    url: '/api/repos/num',
    params: { lang },
  });
};

export const getPagedRepoDetailedInfo = async (
  start: string | number,
  length: string | number,
  lang?: string,
  filter?: RepoSort
) => {
  return await requestGFI<RepoDetail[]>({
    url: '/api/repos/info/',
    params: { start, length, lang, filter },
    baseURL: getBaseURL(),
  });
};

export const getPagedRepoBrief = async (
  start: number,
  length: number,
  lang?: string,
  filter?: RepoSort
) =>
  await requestGFI<RepoBrief[]>({
    url: '/api/repos/info/paged',
    params: { start, length, lang, filter },
  });

export const getRepoDetailedInfo = async (name: string, owner: string) => {
  return await requestGFI<RepoDetail>({
    url: '/api/repos/info/detail',
    params: { name, owner },
  });
};

export const getRepoInfo = async (name: string, owner: string) => {
  return await requestGFI<RepoBrief>({
    url: '/api/repos/info',
    params: { name, owner },
  });
};

export const searchRepoInfoByNameOrURL = async (
  repoName?: string,
  repoURL?: string
) => {
  const { githubLogin } = userInfo();
  return await requestGFI<[RepoBrief]>({
    url: '/api/repos/info/search',
    params: {
      repo: repoName,
      url: repoURL,
      user: githubLogin,
    },
  });
};

export const getGFIByRepoName = async (
  name: string,
  owner: string,
  start?: number,
  length?: number
) =>
  await requestGFI<GFIInfo[]>({
    url: '/api/issue/gfi',
    params: { owner, repo: name, start, length },
  });

export const getGFINum = async (repoName?: string, repoOwner?: string) => {
  return await requestGFI<number | undefined>({
    url: '/api/issue/gfi/num',
    params: {
      name: repoName,
      owner: repoOwner,
    },
  });
};

export const getLanguageTags = async () => {
  return await requestGFI<string[]>({
    url: '/api/repos/language',
  });
};

export const addRepoToGFIBot = async (repoName: string, repoOwner: string) => {
  const { githubLogin } = userInfo();
  return await requestGFI<any>({
    method: 'POST',
    url: '/api/repos/add',
    headers: {
      'Content-Type': 'application/json',
    },
    data: {
      user: githubLogin,
      repo: repoName,
      owner: repoOwner,
    },
  });
};

export const getAddRepoHistory = async (filter?: RepoSort) => {
  const { githubLogin } = userInfo();
  return await requestGFI<UserQueryHistory>({
    url: '/api/user/queries',
    params: {
      user: githubLogin,
      filter: filter,
    },
  });
};

export const getTrainingSummary = async (name?: string, owner?: string) => {
  return await requestGFI<GFITrainingSummary[]>({
    url: '/api/model/training/result',
    params: {
      name,
      owner,
    },
  });
};

export const getUserSearches = async () => {
  const { githubLogin } = userInfo();
  return await requestGFI<SearchedRepo[]>({
    url: '/api/user/searches',
    params: {
      user: githubLogin,
    },
  });
};

export const deleteUserSearch = async (
  name: string,
  owner: string,
  id: number
) => {
  const { githubLogin } = userInfo();
  return await requestGFI<SearchedRepo[]>({
    method: 'DELETE',
    url: '/api/user/searches',
    params: {
      user: githubLogin,
      name,
      owner,
      id,
    },
  });
};

export const deleteRepoQuery = async (name: string, owner: string) => {
  const { githubLogin } = userInfo();
  return await requestGFI<{
    nums?: number;
    queries: RepoBrief[];
    finished_queries?: RepoBrief[];
  }>({
    method: 'DELETE',
    url: '/api/user/queries',
    params: {
      user: githubLogin,
      name,
      owner,
    },
    baseURL: getBaseURL(),
  });
};

export const updateRepoInfo = async (name: string, owner: string) => {
  const { githubLogin } = userInfo();
  return await requestGFI<string>({
    method: 'PUT',
    url: '/api/repos/update/',
    data: {
      github_login: githubLogin,
      name,
      owner,
    },
    baseURL: getBaseURL(),
  });
};

export const getRepoConfig = async (name: string, owner: string) => {
  const { githubLogin } = userInfo();
  return await requestGFI<RepoGFIConfig>({
    url: '/api/user/queries/config',
    params: {
      user: githubLogin,
      name,
      owner,
    },
  });
};

export const updateRepoConfig = async (
  name: string,
  owner: string,
  config: RepoGFIConfig
) => {
  const { githubLogin } = userInfo();
  return await requestGFI<string>({
    method: 'PUT',
    url: '/api/user/queries/config',
    params: {
      user: githubLogin,
      name,
      owner,
    },
    data: config,
  });
};
