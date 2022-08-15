import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';

import { Helmet, HelmetProvider } from 'react-helmet-async';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { BrowserRouter, Route } from 'react-router-dom';
import { CacheRoute, CacheSwitch } from 'react-router-cache-route';
import { AliveScope } from 'react-activation';

import { Container } from 'react-bootstrap';
import { DescriptionPage } from './pages/descriptionPage';
import { GFIHeader } from './pages/GFIHeader';
import { Repositories } from './pages/repositories/repositories';

import { persistor, store } from './storage/configureStorage';
import reportWebVitals from './reportWebVitals';
import { MainPage } from './pages/main/mainPage';
import { LoginRedirect } from './pages/login/GFILoginComponents';
import {
  GlobalRefProvider,
  WindowContextProvider,
} from './pages/app/windowContext';
import { GFIPortal } from './pages/portal/GFIPortal';
import { GFICopyright } from './pages/GFIComponents';

ReactDOM.render(
  <React.StrictMode>
    <HelmetProvider>
      <Helmet></Helmet>
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <WindowContextProvider>
            <GlobalRefProvider>
              <BrowserRouter>
                <AliveScope>
                  <Container
                    fluid
                    className="no-gutters mx-0 px-0 main-container"
                  >
                    <GFIHeader />
                    <CacheSwitch>
                      <CacheRoute exact path="/" component={MainPage} />
                      <CacheRoute path="/home" component={DescriptionPage} />
                      <CacheRoute path="/repos" component={Repositories} />
                      <CacheRoute path="/portal" component={GFIPortal} />
                      <Route path="/login/redirect" component={LoginRedirect} />
                      <CacheRoute path="*" component={MainPage} />
                    </CacheSwitch>
                    <GFICopyright />
                  </Container>
                </AliveScope>
              </BrowserRouter>
            </GlobalRefProvider>
          </WindowContextProvider>
        </PersistGate>
      </Provider>
    </HelmetProvider>
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
