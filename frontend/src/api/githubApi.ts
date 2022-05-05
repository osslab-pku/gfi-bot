import {store} from '../module/storage/configureStorage';
import {asyncRequest} from './query';
import {DEV_URL, userInfo} from './api';
import {RepoPermissions, StandardHTTPResponse} from '../module/data/dataModel';

export const gitHubLogin = () => {
	const [hasLogin, userName] = userInfo()
	if (hasLogin  && userName !== undefined) {
		window.location.reload()
		return
	}
	gitHubOAuthLogin().then((url : string) => {
		window.open(url)
	})
}

export const checkGithubLogin = async () => {
	const userToken = store.getState().loginReducer.token
	const userLoginName = store.getState().loginReducer.loginName
	if (userToken) {
		const res = await asyncRequest<StandardHTTPResponse<any>>({
			url: `https://api.github.com/users/${userLoginName}`,
			headers: {
				'Authorization': `token ${userToken}`,
			},
			customRequestResponse: false,
		})
		if (res?.status === 200) {
			return true
		}
	}
	return false
}

const gitHubOAuthLogin = async () => {
	return await asyncRequest<string>({
		url: '/api/user/github/login',
		baseURL: DEV_URL
	})
}

export const checkHasRepoPermissions = async (repoName: string, owner: string) => {
	const hasLogin = store.getState().loginReducer.hasLogin
	const userToken = store.getState().loginReducer.token
	if (!hasLogin) {
		return false
	}
	const res = await asyncRequest<StandardHTTPResponse<{ permissions?: RepoPermissions }>>({
		url: `https://api.github.com/repos/${owner}/${repoName}`,
		headers: {
			'Authorization': `token ${userToken}`,
		},
		customRequestResponse: false,
	})

	if (res === undefined) return false
	return !!res.data?.permissions?.maintain;
}

export const getIssueByRepoInfo = async (repoName: string, owner?: string, issueId?: string | number) => {
	// url such as https://api.github.com/repos/pallets/flask/issues/4333

	const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueId}`
	const hasLogin = store.getState().loginReducer.hasLogin
	const userToken = store.getState().loginReducer.token
	let res: any
	const headers: any | undefined = (hasLogin && userToken) ? {'Authorization': `token ${userToken}`}: undefined

	res = await asyncRequest({
		url: url,
		headers: headers,
		customRequestResponse: false,
	}).catch((error: any) => {
		if ('response' in error) {
			return error.response
		}
	})

	if (res?.status === 200) {
		return {
			code: 200,
			result: res.data
		}
	} else {
		return {
			code: res.status,
			result: ''
		}
	}
}
