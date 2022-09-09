import axios, { AxiosError } from 'axios';
import { userInfo } from "../storage";
import { GFIResponse } from "../model/api";

type HTTPMethods = 'GET' | 'POST' | 'DELETE' | 'PATCH' | 'PUT';
type ErrorFunc = null | ((error: Error | AxiosError) => any);
type AnyObject = { [key: string]: any };

export type RequestParams = {
  /** request method */
  method?: HTTPMethods;
  /** request data */
  baseURL?: string;
  /** request url */
  url: string;
  /** request params */
  params?: AnyObject;
  /** request headers */
  headers?: AnyObject;
  /** request payload */
  data?: AnyObject;
  /** error handler */
  onError?: ErrorFunc;
};

export const URL_KEY = 'baseURL';

export const getBaseURL = () => {
  if (import.meta.env.REACT_APP_ENV === 'production') {
    return import.meta.env.REACT_APP_BASE_URL;
  }
  const url = localStorage.getItem(URL_KEY);
  if (url && url.length) {
    return url;
  }
  const baseURL = import.meta.env.REACT_APP_BASE_URL || '';
  localStorage.setItem(URL_KEY, baseURL);
  return baseURL;
};

/** wrapper for request data **/
export const requestGFI = async <T>(params: RequestParams) => {
  // if token exists, add token to headers
  const { githubToken } = userInfo();
  if (githubToken) params.headers = { Authorization: `token ${githubToken}` };
  const res = await asyncRequest<GFIResponse<T>>(params);
  if (!res) return undefined;
  if (200 <= res.code && res.code < 300 && res.result) {
    return res.result;
  } else if (typeof params.onError === 'function') {
    // normally when an error occurs, status code != 200
    // but in this case, we want to keep the compatibility
    params.onError(new Error(String(res.result)));
  }
  return undefined;
};

/** request wrapper */
export const asyncRequest: <T>(
  params: RequestParams
) => Promise<T | undefined> = async (params: RequestParams) => {
  try {
    const method = params.method || 'GET';
    const baseURL = params.baseURL || getBaseURL();
    const res = await axios({
      method,
      baseURL,
      url: params.url,
      params: params.params,
      headers: params.headers,
      data: params.data,
    });
    if (200 <= res.status && res.status < 300 && res.data) {
      return res.data;
    } else {
      // use callback function to handle error
      const msg = res.data || res.statusText;
      throw new Error(msg);
    }
  } catch (error: any | AxiosError) {
    // log
    console.error('%s %s: %s', params.url, error.name, error.message);
    if (typeof params.onError === 'function') {
      params.onError(error);
    }
    return undefined;
  }
};
