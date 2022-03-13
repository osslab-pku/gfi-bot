import axios from 'axios';
import {store} from '../module/storage/configureStorage';

// for local development
const DEV_URL = 'https://dev.mskyurina.top'

export const gitHubLogin = () => {
    const hasLogin = store.getState().hasLogin
    const userName = store.getState().name
    if (hasLogin === true  && userName !== undefined) {
        window.location.reload()
        return
    }
    gitHubOAuthLogin().then((url : String) => {
        window.open(url)
    })
}

const gitHubOAuthLogin = async () => {
    return await asyncGet('/api/user/github/login', {}, DEV_URL)
}

export const getRepoNum = async () => {
    return await asyncGet('/api/repos/num', {}, DEV_URL)
}

export const getRepoInfo = async (beginIdx, capacity) => {
    return await asyncGet('/api/repos/info', {
        start: beginIdx,
        length: capacity,
    }, DEV_URL)
}

export const getRecommendedRepoInfo = async () => {
    return await asyncGet('/api/repos/recommend', {}, DEV_URL)
}

export const getGFIByRepoName = async (repoName) => {
    return await asyncGet('/api/issue/gfi', {
        repo: repoName,
    }, DEV_URL)
}

export const getIssueByRepoInfo = async (repoName, owner, issueId) => {
    // url such as https://api.github.com/repos/pallets/flask/issues/4333
    const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueId}`
    const hasLogin = store.getState().hasLogin
    const userToken = store.getState().token
    let res
    if (hasLogin && userToken) {
        res = await axios
            .get(url, { baseURL: '', headers: { 'Authorization': `token ${userToken}`}})
            .catch((error) => {
                return error.response
            })
    } else {
        res = await axios
            .get(url, { baseURL: ''})
            .catch((error) => {
                return error.response
            })
    }

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

const asyncGet = async (url: String, params, baseUrl: string, onError = null) => {
    try {
        let res = await axios.get(url, {
            baseURL: baseUrl,
            params: params
        })
        if (res?.status === 200) {
            if (res.data.code === 200) {
                return res.data.result
            } else if (onError && typeof onError === 'function') {
                return onError(res.data)
            } else {
                return ''
            }
        } else {
            throw new Error('server response failed')
        }
    } catch (e) {
        return null
    }
}
