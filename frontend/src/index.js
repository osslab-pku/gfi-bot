import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';

import reportWebVitals from './reportWebVitals';
import {Helmet, HelmetProvider} from 'react-helmet-async';
import {Provider} from 'react-redux';
import {persistor, store} from './module/storage/configureStorage';
import {PersistGate} from "redux-persist/integration/react";
import {BrowserRouter, Route} from 'react-router-dom';
import {CacheRoute, CacheSwitch} from 'react-router-cache-route';
import {AliveScope} from 'react-activation';

import {DescriptionPage} from './pages/descriptionPage';
import {GFIHeader} from './pages/gfiHeader';
import {Repositories} from './pages/repositories/repositories';

import {Container} from 'react-bootstrap';
import {MainPage} from './pages/main/mainPage';
import {LoginRedirect} from './pages/login/welcomePage';
import {GlobalRefProvider, WindowContextProvider} from './pages/app/windowContext';
import {GFIQueryProcessContextProvider} from './pages/app/processStatusProvider';

ReactDOM.render(
	<React.StrictMode>
		<HelmetProvider>
			<Helmet>
				<title> GFI Bot </title>
			</Helmet>
			<Provider store={store}>
				<PersistGate loading={null} persistor={persistor}>
					<WindowContextProvider>
						<GlobalRefProvider>
							<BrowserRouter>
								<AliveScope>
									<Container fluid className={'no-gutters mx-0 px-0'}>
										<GFIHeader />
										<CacheSwitch>
											<CacheRoute exact path={'/'} component={MainPage} />
											<CacheRoute path={'/home'} component={DescriptionPage} />
											<CacheRoute path={'/repos'} component={Repositories} />
											<Route path={'/login/redirect'} component={LoginRedirect} />
											<CacheRoute path={'*'} component={MainPage} />
										</CacheSwitch>
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
