import axios from 'axios';

export const asyncGet = async (url: String, params, baseUrl: string, onError = null) => {
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