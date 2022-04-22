import {Reducer} from 'redux';

export type LoginState = {
	hasLogin: boolean,
	id?: string | number,
	name?: string,
	token?: string,
	avatar?: string,
}

const initialLoginState: LoginState = {
	hasLogin: false,
}


const LOGIN = 'LOGIN'
const LOGOUT = 'LOGOUT'

export const createLogoutAction = () => {
	return {
		'type': LOGOUT,
	}
}

export const createLoginAction = (id: string, name: string, token: string, avatar: string) => {
	return {
		'type': LOGIN,
		'id': id,
		'name': name,
		'token': token,
		'avatar': avatar,
	}
}

export interface LoginAction {
	type: 'LOGIN',
	id?: string | number,
	name?: string,
	token?: string,
	avatar?: string,
}

export interface LogoutAction {
	type: 'LOGOUT',
}

export const loginReducer: Reducer<LoginState, LoginAction | LogoutAction> = (state = initialLoginState, action: LoginAction | LogoutAction) => {
	switch (action.type) {
		case LOGIN: {
			return {
				hasLogin: true,
				id: action.id,
				name: action.name,
				token: action.token,
				avatar: action.avatar,
			}
		}
		case LOGOUT:
			return { hasLogin: false }
		default:
			return state
	}
}
