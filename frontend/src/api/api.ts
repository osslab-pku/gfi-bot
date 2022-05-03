import {asyncRequest} from './query';
import {GetRepoDetailedInfo, GFIRepoInfo} from '../module/data/dataModel';
import {store} from '../module/storage/configureStorage';

export const userInfo = () => {
	return [
		store.getState().loginReducer.hasLogin,
		store.getState().loginReducer.name,
		store.getState().loginReducer.loginName,
		store.getState().loginReducer.token,
	]
}

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

export const getRepoDetailedInfo = async (beginIdx: string | number, capacity: string | number, lang?: string, filter?: string) => {
	return await asyncRequest<GetRepoDetailedInfo>({
		url: '/api/repos/detailed_info',
		params: {
			start: beginIdx,
			length: capacity,
			lang: lang,
			filter: filter,
		},
		baseURL: DEV_URL,
	})
}

export const getRepoDetailedInfoByName = async (name: string) => {
	return await asyncRequest<GetRepoDetailedInfo>({
		url: '/api/repos/detail_info_name',
		params: {
			name: name,
		},
		baseURL: DEV_URL,
	})
}

export const getRepoInfoByNameOrURL = async (repoName?: string, repoURL?: string) => {
	const [hasLogin, userName] = userInfo()
	return await asyncRequest<GFIRepoInfo>({
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

export const addRepoToGFIBot = async (repoName: string, repoOwner: string) => {
	const [hasLogin, _, loginName] = userInfo()
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
		baseURL: DEV_URL,
	})
}

export const getAddRepoHistory = async () => {
	const [_, __, loginName] = userInfo()
	return await asyncRequest<{
		nums?: number,
		queries: GFIRepoInfo[],
		finished_queries?: GFIRepoInfo[],
	}>({
		url: '/api/user/queries',
		params: {
			user: loginName,
		},
		baseURL: DEV_URL,
	})
}
