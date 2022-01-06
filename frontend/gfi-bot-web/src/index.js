import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';

import reportWebVitals from './reportWebVitals';
import {Helmet, HelmetProvider} from 'react-helmet-async';
import {Provider} from 'react-redux';
import {persistor, store} from './module/storage/configureStorage';
import {PersistGate} from "redux-persist/integration/react";

import {BrowserRouter, Route, Switch} from 'react-router-dom';
import {MainPage} from './pages/mainPage';
import {Header} from './pages/header';
import {Repositories} from './pages/repositories/repositories';

import {Container} from 'react-bootstrap';

ReactDOM.render(
    <React.StrictMode>
        <HelmetProvider>
            <Helmet>
                <title> GFI-Bot </title>
            </Helmet>
            <Provider store={store}>
                <PersistGate loading={null} persistor={persistor}>
                    <BrowserRouter>
                        <Container fluid className={'no-gutters mx-0 px-0'}>
                            <Header />
                            <Switch>
                                <Route exact path={'/'} component={MainPage} />
                                <Route path={'/home'} component={MainPage} />
                                <Route path={'/repos'} component={Repositories} />
                            </Switch>
                        </Container>
                    </BrowserRouter>
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
