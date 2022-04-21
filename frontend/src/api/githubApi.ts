import {store} from '../module/storage/configureStorage';
import {asyncRequest} from './query';
import {DEV_URL} from './api';

export const userInfo = () => {
	return [
		store.getState().hasLogin,
		store.getState().name,
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

const gitHubOAuthLogin = async () => {
	return await asyncRequest({
		url: '/api/user/github/login',
		baseURL: DEV_URL
	})
}

export const getIssueByRepoInfo = async (repoName: string, owner?: string, issueId?: string | number) => {
	// url such as https://api.github.com/repos/pallets/flask/issues/4333
	const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueId}`
	const hasLogin = store.getState().hasLogin
	const userToken = store.getState().token
	let res: any
	const headers: any | undefined = (hasLogin && userToken) ? {'Authorization': `token ${userToken}`}: undefined

	res = await asyncRequest({
		url: url,
		headers: headers,
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
		// not good, needs to be changed
		return {
			code: 403,
			result: ''
		}
	}
}
