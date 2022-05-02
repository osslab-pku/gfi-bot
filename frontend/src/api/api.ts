import {userInfo} from './githubApi';
import {asyncRequest} from './query';
import {GetRepoDetailedInfo} from '../module/data/dataModel';

// for local development
export const DEV_URL = 'https://dev.mskyurina.top'

// currently, a compromise
export const WEBSOCKET_URL = 'ws://la-3.1919114.xyz:5000/gfi_process'

export const getRepoNum = async (lang?: string) => {
	return await asyncRequest<any>({
		url: '/api/repos/num',
		params: {
			lang: lang ? lang : '',
		},
		baseURL: DEV_URL,
	})
}

export const getIssueNum = async () => {
	return await asyncRequest<any>({
		url: '/api/issue/num',
		baseURL: DEV_URL,
	})
}

export const getRepoDetailedInfo = async (beginIdx: string | number, capacity: string | number, lang: undefined | string) => {
	return await asyncRequest<GetRepoDetailedInfo>({
		url: '/api/repos/detailed_info',
		params: {
			start: beginIdx,
			length: capacity,
			lang: lang ? lang: '',
		},
		baseURL: DEV_URL,
	})
}

export const getRepoDetailedInfoByName = async (name: string) => {
	return await asyncRequest<any>({
		url: '/api/repos/detail_info_name',
		params: {
			name: name,
		},
		baseURL: DEV_URL,
	})
}

export const getRepoInfoByNameOrURL = async (repoName: string, repoURL?: string) => {
	const [hasLogin, userName] = userInfo()
	return await asyncRequest<any>({
		url: '/api/repos/info',
		params: {
			repo: repoName,
			url: repoURL,
			user: userName,
		},
		baseURL: DEV_URL,
	})
}

export const getRecommendedRepoInfo = async () => {
	return await asyncRequest<any>({
		url: '/api/repos/recommend',
		baseURL: DEV_URL,
	})
}

export const getGFIByRepoName = async (repoName: string) => {
	return await asyncRequest<any>({
		url: '/api/issue/gfi',
		params: {
			repo: repoName,
		},
		baseURL: DEV_URL,
	})
}

export const getLanguageTags = async () => {
	return await asyncRequest<any>({
		url: '/api/repos/language',
		baseURL: DEV_URL,
	})
}

export const getProcessingSearches = async (shouldClearSession: boolean) => {
	const [hasLogin, userName] = userInfo()
	return await asyncRequest<any>({
		url: '/api/repos/searches',
		params: {
			user: userName,
			clear_session: shouldClearSession,
		},
		baseURL: DEV_URL,
	})
}
