import { Reducer } from 'redux';
import { RepoShouldDisplayPopoverState } from '../pages/main/GFIRepoDisplayView';

export type LoginState = {
  hasLogin: boolean;
  id?: string | number;
  loginName?: string;
  name?: string;
  token?: string;
  avatar?: string;
};

const initialLoginState: LoginState = {
  hasLogin: false,
};

const LOGIN = 'LOGIN';
const LOGOUT = 'LOGOUT';

export const createLogoutAction = () => {
  return {
    type: LOGOUT,
  };
};

export const createLoginAction = (
  id: string,
  loginName: string,
  name: string,
  token: string,
  avatar: string
) => {
  return {
    type: LOGIN,
    id,
    loginName,
    name,
    token,
    avatar,
  };
};

export interface LoginAction {
  type: 'LOGIN';
  id?: string | number;
  loginName?: string;
  name?: string;
  token?: string;
  avatar?: string;
}

export interface LogoutAction {
  type: 'LOGOUT';
}

export const loginReducer: Reducer<LoginState, LoginAction | LogoutAction> = (
  state = initialLoginState,
  action: LoginAction | LogoutAction
) => {
  switch (action.type) {
    case LOGIN: {
      return {
        hasLogin: true,
        id: action.id,
        loginName: action.loginName,
        name: action.name,
        token: action.token,
        avatar: action.avatar,
      };
    }
    case LOGOUT:
      return { hasLogin: false };
    default:
      return state;
  }
};

type POPOVER_ACTION_TYPE = 'POPOVER';
const POPOVER_ACTION_TYPE: POPOVER_ACTION_TYPE = 'POPOVER';

export interface PopoverAction extends RepoShouldDisplayPopoverState {
  type: POPOVER_ACTION_TYPE;
}

export const createPopoverAction: (
  p?: RepoShouldDisplayPopoverState
) => PopoverAction = (p) => {
  return {
    type: 'POPOVER',
    shouldDisplayPopover: p ? p.shouldDisplayPopover : false,
    popoverComponent: p ? p.popoverComponent : undefined,
    popoverID: p ? p.popoverID : undefined,
  };
};

const initialPopover: RepoShouldDisplayPopoverState = {};

export const showMainPagePopoverReducer: Reducer<
  RepoShouldDisplayPopoverState,
  PopoverAction
> = (state = initialPopover, action) => {
  if (action.type === POPOVER_ACTION_TYPE) {
    return {
      shouldDisplayPopover: action.shouldDisplayPopover,
      popoverComponent: action.popoverComponent,
      popoverID: action.popoverID,
    };
  }
  return state;
};

export interface GlobalProgressBarState {
  hidden: boolean;
}

const initialProgressBarState: GlobalProgressBarState = {
  hidden: true,
};

type PROGRESS_BAR_ACTION_TYPE = 'PROGRESSBAR';
const PROGRESS_BAR_ACTION_TYPE: PROGRESS_BAR_ACTION_TYPE = 'PROGRESSBAR';

export interface ProgressBarAction extends GlobalProgressBarState {
  type: PROGRESS_BAR_ACTION_TYPE;
}

export const createGlobalProgressBarAction: (
  p?: GlobalProgressBarState
) => ProgressBarAction = (p) => {
  let hidden = p?.hidden;
  if (hidden === undefined) {
    hidden = true;
  }
  return {
    type: 'PROGRESSBAR',
    hidden,
  };
};

export const globalProgressBarStateReducer: Reducer<
  GlobalProgressBarState,
  ProgressBarAction
> = (state = initialProgressBarState, action) => {
  if (action.type === 'PROGRESSBAR') {
    let { hidden } = action;
    if (hidden === undefined) {
      hidden = true;
    }
    return {
      hidden,
    };
  }
  return state;
};

export interface AccountNavState {
  show: boolean;
}

type ACCOUNT_NAV_ACTION_TYPE = 'ACCOUNT_NAV';
const ACCOUNT_NAV_ACTION_TYPE: ACCOUNT_NAV_ACTION_TYPE = 'ACCOUNT_NAV';

export interface AccountNavStateAction extends AccountNavState {
  type: ACCOUNT_NAV_ACTION_TYPE;
}

const initialAccountNavState: AccountNavState = {
  show: false,
};

export const createAccountNavStateAction: (
  p: AccountNavState
) => AccountNavStateAction = (p) => {
  return {
    type: 'ACCOUNT_NAV',
    show: p.show,
  };
};

export const accountNavStateReducer: Reducer<
  AccountNavState,
  AccountNavStateAction
> = (state = initialAccountNavState, action) => {
  if (action.type === ACCOUNT_NAV_ACTION_TYPE) {
    return {
      show: action.show,
    };
  }
  return state;
};

type MAIN_LANG_SELECT_ACTION_TYPE = 'MAIN_LANG_SELECT';
const MAIN_LANG_SELECT_ACTION_TYPE: MAIN_LANG_SELECT_ACTION_TYPE =
  'MAIN_LANG_SELECT';

export interface MainPageLangTagSelectedState {
  tagSelected?: string;
}

export interface MainPageLangTagSelectedAction
  extends MainPageLangTagSelectedState {
  type: MAIN_LANG_SELECT_ACTION_TYPE;
}

const initMainPageLangTagSelectedState: MainPageLangTagSelectedState = {};

export const createMainPageLangTagSelectedAction: (
  p: MainPageLangTagSelectedState
) => MainPageLangTagSelectedAction = (p) => {
  return {
    type: MAIN_LANG_SELECT_ACTION_TYPE,
    tagSelected: p.tagSelected,
  };
};

export const mainPageLangTagSelectedStateReducer: Reducer<
  MainPageLangTagSelectedState,
  MainPageLangTagSelectedAction
> = (state = initMainPageLangTagSelectedState, action) => {
  if (action.type === MAIN_LANG_SELECT_ACTION_TYPE) {
    return {
      tagSelected: action.tagSelected,
    };
  }
  return state;
};
