import {combineReducers, createStore, Reducer} from 'redux';
import {persistStore, persistReducer} from 'redux-persist';
import storage from 'redux-persist/lib/storage';

import {loginReducer, PopoverAction, showMainPagePopoverReducer} from './reducers';
import {RepoShouldDisplayPopoverState} from '../../pages/main/GFIRepoDisplayView';

const persistConfig = {
	key: 'root',
	storage: storage,
	blacklist: [],
}

const reducers = persistReducer(persistConfig, loginReducer)

const reducer = combineReducers({
	loginReducer: reducers,
	mainPopoverReducer: showMainPagePopoverReducer,
})

export const store = createStore(reducer)
export const persistor = persistStore(store)

export interface GFIRootReducers {
	loginReducer: any,
	mainPopoverReducer: RepoShouldDisplayPopoverState,
}
