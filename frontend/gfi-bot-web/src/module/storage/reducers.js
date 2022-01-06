const initialLoginState = {
    hasLogin: false,
}

// TODO: @MSKYurina Add Available Reducers

const LOGIN = 'LOGIN'
const LOGOUT = 'LOGOUT'

const loginAction = {
    'type': LOGIN,
    'token': String,
}

export const logoutAction = {
    'type': LOGOUT,
}

export const loginReducer = (state = initialLoginState, action) => {
    switch (action.type) {
        case LOGIN: {
            return { hasLogin: true, token: action.token }
        }
        case LOGOUT:
            return { hasLogin: false, token: null }
        default:
            return state
    }
}