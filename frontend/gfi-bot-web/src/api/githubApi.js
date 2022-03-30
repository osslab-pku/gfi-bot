import {store} from '../module/storage/configureStorage';
import axios from 'axios';
import {asyncGet} from './gfiQuery';
import {DEV_URL} from './api';

export const userInfo = () => {
    return [
        store.getState().hasLogin,
        store.getState().name,
    ]
}

export const gitHubLogin = () => {
    const [hasLogin, userName] = userInfo()
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