import axios from 'axios';
import { KeyMap } from '../module/data/dataModel';

type HTTPMethods = 'GET' | 'POST' | 'DELETE' | 'PATCH' | 'PUT';
type ErrorFunc = null | ((error: Error) => void);

type RequestParams = {
  method?: HTTPMethods;
  url?: string;
  params?: KeyMap;
  headers?: KeyMap;
  baseURL?: string;
  onError?: ErrorFunc;
  customRequestResponse?: boolean;
  data?: KeyMap;
};

export const URL_KEY = 'baseURL';

export const getBaseURL = () => {
  if (process.env.REACT_APP_ENV === 'production') {
    return process.env.REACT_APP_BASE_URL;
  }
  const url = localStorage.getItem(URL_KEY);
  if (url && url.length) {
    return url;
  }
  const baseURL = process.env.REACT_APP_BASE_URL || '';
  localStorage.setItem(URL_KEY, baseURL);
  return baseURL;
};

export const asyncRequest: <T>(
  params: RequestParams
) => Promise<T | undefined> = async (params: RequestParams) => {
  try {
    let method: HTTPMethods = 'GET';
    if (params?.method) {
      method = params.method;
    }
    if (params.customRequestResponse === undefined) {
      params.customRequestResponse = true;
    }

    const res = await axios({
      method,
      url: params.url,
      baseURL: params.baseURL,
      params: params.params,
      headers: params.headers,
      data: params.data,
    });

    if (params.customRequestResponse) {
      if (res?.status === 200) {
        if (res.data.code === 200) {
          return res.data.result;
        }
        if (typeof params.onError === 'function') {
          return params.onError(res.data);
        }
        return undefined;
      }
      throw new Error('server response failed');
    } else {
      return res;
    }
  } catch (error) {
    if (typeof params.onError === 'function' && error instanceof Error) {
      params.onError(error);
    }
    return error;
  }
};