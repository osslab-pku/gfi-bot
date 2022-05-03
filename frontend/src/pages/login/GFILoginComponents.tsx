import React, {useEffect} from 'react';
import {useDispatch} from 'react-redux';
import {useHistory} from 'react-router-dom';
import {Container, ToastContainer, Toast, Button} from 'react-bootstrap';

import '../../style/gfiStyle.css'
import {defaultFontFamily} from '../../utils';
import {createLoginAction} from '../../module/storage/reducers';
import {UserOutlined} from '@ant-design/icons';


export const LoginRedirect = (props: any) => {

	const dispatch = useDispatch()
	let history = useHistory()

	useEffect(() => {
		const params = new URLSearchParams(props.location.search)
		const loginName = params.get('github_login')
		const userName = params.get('github_name')
		const userUrl = params.get('github_avatar_url')
		const userId = params.get('github_id')
		const userToken = params.get('github_token')
		if (userId && loginName && userName && userToken && userUrl) {
			dispatch(createLoginAction(userId, loginName, userName, userToken, userUrl))
			history.push('/', {justLogin: true})
		}
	}, [])

	return (
		<Container style={{
			textAlign: 'center',
			fontFamily: defaultFontFamily
		}}>
			Redirecting...
		</Container>
	)
}

export interface GFINotiToastProps {
	userName: string,
	userAvatarUrl?: string,
	onClose: () => void,
	context?: string,
	buttonContext?: string,
	onClick?: () => void,
	show: boolean,
}

export const GFINotiToast = (props: GFINotiToastProps) => {

	const {userName, userAvatarUrl, onClose, show, context, buttonContext, onClick} = props

	return (
		<ToastContainer position={'top-end'} style={{
			zIndex: '9999',
		}}>
			<Toast show={show} animation={true} onClose={() => onClose()}>
				<Toast.Header>
					{userAvatarUrl ? <img src={userAvatarUrl} alt={''} className={'rounded me-2'} style={{ width: '30px' }}/>
						: <UserOutlined style={{ fontSize: '30px' }} />}
					<strong className={'me-auto'} style={{ marginLeft: '5px' }}> Hello, {userName} </strong>
				</Toast.Header>
				<Toast.Body>
					{context ? context : 'Welcome to GFI-Bot'}
				</Toast.Body>
				{buttonContext ?
					<div style={{
						display: 'flex',
						justifyContent: 'flex-end',
						paddingRight: '1rem',
						paddingBottom: '0.5rem',
					}}>
						<Button variant={'outline-primary'} size={'sm'} onClick={onClick}>
							{buttonContext}
						</Button>
					</div>
					: <></>
				}
			</Toast>
		</ToastContainer>
	)
}
