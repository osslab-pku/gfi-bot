import axios from 'axios';
import {store} from '../module/storage/configureStorage';

// for local development
const DEV_URL = 'https://dev.mskyurina.top'

export const gitHubLogin = () => {
    const hasLogin = store.getState().hasLogin
    const userName = store.getState().name
    if (hasLogin === true  && userName !== undefined) {
        window.location.reload(false)
        return
    }
    gitHubOAuthLogin().then((url : String) => {
        window.open(url)
    })
}

const gitHubOAuthLogin = async () => {
    return await asyncGet('/api/user/github/login', {}, true)
}

export const getRepoNum = async () => {
    return await asyncGet('/api/repos/num', {}, true)
}

export const getRepoInfo = async (beginIdx, capacity) => {
    return await asyncGet('/api/repos/info', {
        start: beginIdx,
        length: capacity,
    }, true)
}

const asyncGet = async (url: String, params, useBaseURL: boolean) => {
    try {
        let res = await axios.get(url, {
            baseURL: useBaseURL ? DEV_URL : '',
            params: params
        })
        if (res?.status === 200) {
            return res.data.result
        } else {
            throw new Error('server response failed')
        }
    } catch (e) {
        return null
    }

}
