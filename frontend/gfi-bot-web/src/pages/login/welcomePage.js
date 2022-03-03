import React, {useEffect} from 'react';
import {useDispatch} from 'react-redux';
import {useHistory} from 'react-router-dom';
import PropTypes from 'prop-types';
import {Container, Col, Row, ToastContainer, Toast} from 'react-bootstrap';

import '../../style/gfiStyle.css'
import {defaultFontFamily} from '../../utils';
import {createLoginAction} from '../../module/storage/reducers';


export const LoginRedirect = (props) => {

    const dispatch = useDispatch()
    let history = useHistory()

    useEffect(() => {
        const params = new URLSearchParams(props.location.search)
        const userName = params.get('github_name')
        const userUrl = params.get('github_avatar_url')
        const userId = params.get('github_id')
        const userToken = params.get('github_token')
        dispatch(createLoginAction(userId, userName, userToken, userUrl))
        history.push('/', {justLogin: true})
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

export const GFIWelcome = ({userName, userAvatarUrl, onClose, show}) => {

    return (
        <ToastContainer position={'top-end'} style={{
            zIndex: '9999',
        }}>
            <Toast show={show} animation={true} onClose={() => onClose()}>
                <Toast.Header>
                    <img src={userAvatarUrl} alt={''} className={'rounded me-2'} style={{
                        width: '30px',
                    }}/>
                    <strong className={'me-auto'}> Hello, {userName} </strong>
                </Toast.Header>
                <Toast.Body>
                    Welcome to GFI-Bot
                </Toast.Body>
            </Toast>
        </ToastContainer>
    )
}

GFIWelcome.propTypes = {
    userName: PropTypes.string,
    userAvatarUrl: PropTypes.string,
    onClose: PropTypes.func
}
