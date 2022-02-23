import axios from 'axios';

export const DEV_URL = 'http://172.18.182.44:5000/'

export const getRepoNum = async () => {
    return await asyncGet('/api/repos/num', null)
}

export const getRepoInfo = async (beginIdx, capacity) => {
    return await asyncGet('/api/repos/info', {
        start: beginIdx,
        length: capacity,
    })
}

const asyncGet = async (url, params) => {
    let res = await axios.get(url, {
        baseURL: DEV_URL,
        params: params
    })
    if (res?.status === 200) {
        return res.data.result
    } else {
        return null
    }
}
