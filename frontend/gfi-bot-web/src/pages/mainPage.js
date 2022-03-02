import React, {useEffect, useState} from 'react';
import {Container, Col, Row, Form, InputGroup, Button, Pagination, Alert} from 'react-bootstrap';
import {gsap} from 'gsap';

import '../style/gfiStyle.css'
import {SearchOutlined} from '@ant-design/icons';
import {defaultFontFamily} from '../utils';
import {store} from '../module/storage/configureStorage';

import {GFIWelcome} from './login/welcomePage';

export const MainPage = (props) => {

    let [userName, setUserName] = useState('')
    let [userAvatarUrl, setUserAvatarUrl] = useState('')
    let [showLoginMsg, setShowLoginMsg] = useState(false)

    useEffect(() => {
        let params = new URLSearchParams(props.location.search)
        if (params.get('justLogin') === 'true') {
            const storeState = store.getState()
            if ('name' in storeState) {
                setUserName(storeState.name)
            }
            if ('avatar' in storeState) {
                setUserAvatarUrl(storeState.avatar)
            }
            setShowLoginMsg(true)
        }
    }, [])

    return (
        <>
            <Container className={'singlePage'}>
                <Row>
                    <GFIWelcome
                        show={showLoginMsg}
                        userName={userName}
                        userAvatarUrl={userAvatarUrl}
                        onClose={() => {
                            setShowLoginMsg(false)
                        }}
                    />
                </Row>
                <Row style={{marginTop: '7px', marginBottom: '7px'}}>
                    <Col sm={1}/>
                    <Col style={{
                        fontSize: 'xx-large',
                        fontWeight: 'bold',
                        fontFamily: defaultFontFamily,
                    }}>
                        GFI BOT
                    </Col>
                    <Col sm={1}/>
                </Row>
                <Row>
                    <Col sm={1}/>
                    <Col>
                        <Form.Group>
                            <InputGroup>
                                <Form.Control
                                    placeholder={'Github URL'}
                                    style={{
                                        minWidth: '270px',
                                    }}
                                    aria-describedby={'append-icon'}
                                />
                                <Button>
                                    <SearchOutlined style={{
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        width: '24px',
                                        height: '24px',
                                    }}/>
                                </Button>
                            </InputGroup>
                        </Form.Group>
                    </Col>
                    <Col sm={1}/>
                </Row>
            </Container>
        </>

    )
}