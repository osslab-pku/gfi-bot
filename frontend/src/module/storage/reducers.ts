import {Reducer} from 'redux';
import {RepoShouldDisplayPopoverState} from '../../pages/main/GFIRepoDisplayView';

export type LoginState = {
	hasLogin: boolean,
	id?: string | number,
	loginName?: string,
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

export const createLoginAction = (id: string, loginName: string, name: string, token: string, avatar: string) => {
	return {
		'type': LOGIN,
		'id': id,
		'loginName': loginName,
		'name': name,
		'token': token,
		'avatar': avatar,
	}
}

export interface LoginAction {
	type: 'LOGIN',
	id?: string | number,
	loginName?: string,
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
				loginName: action.loginName,
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

export interface PopoverAction extends RepoShouldDisplayPopoverState {
	type: 'POPOVER'
}

export const createPopoverAction: (p?: RepoShouldDisplayPopoverState) => PopoverAction = (p) => {
	return {
		type: 'POPOVER',
		shouldDisplayPopover: p? p.shouldDisplayPopover: false,
		popoverComponent: p? p.popoverComponent: undefined,
		popoverID: p? p.popoverID: undefined,
	}
}

const initialPopover: RepoShouldDisplayPopoverState = {

}

export const showMainPagePopoverReducer: Reducer<RepoShouldDisplayPopoverState, PopoverAction> = (state = initialPopover, action) => {
	return {
		shouldDisplayPopover: action.shouldDisplayPopover,
		popoverComponent: action.popoverComponent,
		popoverID: action.popoverID
	}
}
