const initialLoginState = {
    hasLogin: false,
}

// TODO: @MSKYurina Add Available Reducers

const LOGIN = 'LOGIN'
const LOGOUT = 'LOGOUT'

export const createLogoutAction = () => {
    return {
        'type': LOGOUT,
    }
}

export const createLoginAction = (id: String, name: String, avatar: String) => {
    return {
        'type': LOGIN,
        'id': id,
        'name': name,
        'avatar': avatar,
    }
}

export const loginReducer = (state = initialLoginState, action) => {
    switch (action.type) {
        case LOGIN: {
            return { hasLogin: true, id: action.id, name: action.name, avatar: action.avatar }
        }
        case LOGOUT:
            return { hasLogin: false, id: null, name: null, avatar: null}
        default:
            return state
    }
}