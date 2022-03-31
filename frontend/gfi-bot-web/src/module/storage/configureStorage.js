import {createStore} from 'redux';
import {persistStore, persistReducer} from 'redux-persist';
import storage from 'redux-persist/lib/storage';

import {loginReducer} from './reducers';

const persistConfig = {
    key: 'root',
    storage: storage,
    blacklist: [],
}

const reducers = persistReducer(persistConfig, loginReducer)

export const store = createStore(reducers)
export const persistor = persistStore(store)
