const initialLoginState = {
    hasLogin: false,
}

const LOGIN = 'LOGIN'
const LOGOUT = 'LOGOUT'

export const createLogoutAction = () => {
    return {
        'type': LOGOUT,
    }
}

export const createLoginAction = (id: String, name: String, token: String, avatar: String) => {
    return {
        'type': LOGIN,
        'id': id,
        'name': name,
        'token': token,
        'avatar': avatar,
    }
}

export const loginReducer = (state = initialLoginState, action) => {
    switch (action.type) {
        case LOGIN: {
            return { hasLogin: true, id: action.id, name: action.name, token: action.token, avatar: action.avatar }
        }
        case LOGOUT:
            return { hasLogin: false, id: null, name: null, token: null, avatar: null}
        default:
            return state
    }
}
