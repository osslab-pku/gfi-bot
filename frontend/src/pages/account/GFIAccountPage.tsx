import React, {useEffect} from 'react';
import {Container, Nav} from 'react-bootstrap';
import {LinkContainer} from 'react-router-bootstrap';
import {withRouter} from 'react-router-dom';

import '../../style/gfiStyle.css'
import {useDispatch} from 'react-redux';
import {createAccountNavStateAction} from '../../module/storage/reducers';

export interface GFIAccountPage {}

export const GFIAccountPage = (props: GFIAccountPage) => {

	const dispatch = useDispatch()
	useEffect(() => {
		dispatch(createAccountNavStateAction({ show: true }))
	}, [])

	return (
		<></>
	)
}

export const GFIAccountPageNav = withRouter((props: {id?: string}) => {
	return (
		<>
			<Nav
				variant={'pills'}
				className={'flex-row justify-content-center align-center'}
				id={props?.id}
			>
				<Nav.Item className={'account-nav-container'}>
					<LinkContainer to={'/my'}>
						<Nav.Link eventKey={1} className={'account-nav'}>
							My Account
						</Nav.Link>
					</LinkContainer>
				</Nav.Item>
				<Nav.Item className={'account-nav-container'}>
					<LinkContainer to={'/repos'}>
						<Nav.Link eventKey={2} className={'account-nav'} active={false}>
							Repo Data
						</Nav.Link>
					</LinkContainer>
				</Nav.Item>
			</Nav>
		</>
	)
})