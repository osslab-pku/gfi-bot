import {store} from '../module/storage/configureStorage';
import {asyncRequest} from './query';
import {DEV_URL} from './api';

export const userInfo = () => {
	return [
		store.getState().loginReducer.hasLogin,
		store.getState().loginReducer.name,
		store.getState().loginReducer.loginName,
		store.getState().loginReducer.token,
	]
}

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
		const res = await asyncRequest({
			url: `https://api.github.com/users/${userLoginName}`,
			headers: {
				'Authorization': `token ${userToken}`,
			},
			customReq: false,
		})
		if (res?.status === 200) {
			return true
		}
	}
	return false
}

const gitHubOAuthLogin = async () => {
	return await asyncRequest({
		url: '/api/user/github/login',
		baseURL: DEV_URL
	})
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
		customReq: false,
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
