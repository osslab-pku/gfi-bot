import axios from 'axios';
import {KeyMap} from '../module/data/dataModel';

type HTTPMethods = 'GET' | 'POST'
type ErrorFunc = null | ((error: Error) => void)

type RequestParams = {
	method?: HTTPMethods,
	url?: string,
	params?: KeyMap,
	headers?: KeyMap,
	baseURL?: string,
	onError?: ErrorFunc,
	customRequestResponse?: boolean,
	data?: KeyMap,
}

export const asyncRequest: <T>(params: RequestParams) => Promise<T>
	= async <T>(params: RequestParams) => {
	try {
		let method: HTTPMethods = 'GET'
		if (params?.method) {
			method = params.method
		}
		if (params.customRequestResponse === undefined) {
			params.customRequestResponse = true
		}

		const res = await axios({
			method: method,
			url: params.url,
			baseURL: params.baseURL,
			params: params.params,
			headers: params.headers,
			data: params.data,
		})

		if (params.customRequestResponse) {
			if (res?.status === 200) {
				if (res.data.code === 200) {
					return res.data.result
				} else if (typeof params.onError === 'function') {
					return params.onError(res.data)
				} else {
					return undefined
				}
			} else {
				throw new Error('server response failed')
			}
		} else {
			return res
		}
	} catch (error) {
		if (typeof params.onError === 'function' && error instanceof Error) {
			params.onError(error)
		}
	}
}
