import axios from 'axios';

type HTTPMethods = 'GET' | 'POST'
type ErrorFunc = null | ((error: Error) => void)

type RequestParams = {
	method?: HTTPMethods,
	url?: string,
	params?: any,
	headers?: any,
	baseURL?: string,
	onError?: ErrorFunc,
}

export const asyncRequest = async (params: RequestParams) => {
	try {
		let method: HTTPMethods = 'GET'
		if (params.method !== undefined) {
			method = params.method
		}

		const res = await axios({
			method: method,
			url: params.url,
			baseURL: params.baseURL,
			params: params.params,
			headers: params.headers,
		})

		if (res?.status === 200) {
			if (res.data.code === 200) {
				return res.data.result
			} else if (typeof params.onError === 'function') {
				return params.onError(res.data)
			} else {
				return ''
			}
		} else {
			throw new Error('server response failed')
		}

	} catch (error) {
		if (typeof params.onError === 'function' && error instanceof Error) {
			params.onError(error)
		}
	}
}