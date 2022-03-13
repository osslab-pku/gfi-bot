import axios from 'axios';
import {store} from '../module/storage/configureStorage';

import {asyncGet} from './gfiQuery';

// for local development
export const DEV_URL = 'https://dev.mskyurina.top'

export const getRepoNum = async () => {
    return await asyncGet('/api/repos/num', {}, DEV_URL)
}

export const getIssueNum = async () => {
    return await asyncGet('/api/issue/num', {}, DEV_URL)
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

export const getLanguageTags = async () => {
    return await asyncGet('/api/repos/language', {}, DEV_URL)
}
