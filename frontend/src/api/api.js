import {asyncGet} from './gfiQuery';
import {userInfo} from './githubApi';

// for local development
export const DEV_URL = 'https://dev.mskyurina.top'

// currently, a compromise
export const WEBSOCKET_URL = 'ws://la-3.1919114.xyz:5000/gfi_process'

export const getRepoNum = async (lang) => {
    return await asyncGet('/api/repos/num', {
        lang: lang ? lang : '',
    }, DEV_URL)
}

export const getIssueNum = async () => {
    return await asyncGet('/api/issue/num', {}, DEV_URL)
}

export const getRepoDetailedInfo = async (beginIdx, capacity, lang) => {
    return await asyncGet('/api/repos/detailed_info', {
        start: beginIdx,
        length: capacity,
        lang: lang ? lang : '',
    }, DEV_URL)
}

export const getRepoInfoByNameOrURL = async (repoName, repoURL) => {
    const [hasLogin, userName] = userInfo()
    return await asyncGet('/api/repos/info', {
        repo: repoName,
        url: repoURL,
        user: userName,
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

export const getLanguageTags = async () => {
    return await asyncGet('/api/repos/language', {}, DEV_URL)
}

export const getProcessingSearches = async (shouldClearSession: boolean) => {
    const [hasLogin, userName] = userInfo()
    return await asyncGet('/api/repos/searches', {
        user: userName,
        clear_session: shouldClearSession,
    }, DEV_URL)
}
