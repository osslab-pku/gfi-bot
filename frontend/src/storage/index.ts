import { store } from "./configureStorage";

export const userInfo = () => ({
  hasLogin: store.getState().loginReducer.hasLogin,
  name: store.getState().loginReducer.name,
  githubLogin: store.getState().loginReducer.loginName,
  githubToken: store.getState().loginReducer.token
})