import React, {useEffect, useState} from 'react';
import {Container, Col, Row, Form, InputGroup, Button, Pagination, Alert} from 'react-bootstrap';
import {gsap} from 'gsap';

import backgroundLogo from '../assets/gfi_logo_cut.png'
import background from '../assets/Tokyo-Tower-.jpg'
import gfiLogo from '../assets/gfi-logo.png'

import '../style/gfiStyle.css'
import {SearchOutlined} from '@ant-design/icons';
import {defaultFontFamily} from '../utils';
import {store} from '../module/storage/configureStorage';

import {GFIWelcome} from './login/welcomePage';
import {useIsMobile, useWindowSize} from './app/windowContext';

export const MainPage = (props) => {
    let [userName, setUserName] = useState('')
    let [userAvatarUrl, setUserAvatarUrl] = useState('')
    let [showLoginMsg, setShowLoginMsg] = useState(false)

    const isMobile = useIsMobile()
    const {width, height} = useWindowSize()

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

    const renderSearchArea = () => {
        return (
            <>
                <Row style={{marginTop: '20px', marginBottom: '10px'}}>
                    <Col style={{
                        display: 'flex',
                        justifyContent: 'flex-start',
                        alignItems: 'center',
                    }}>
                        <div style={{
                            maxWidth: '50px',
                        }}>
                            <img src={gfiLogo} alt={''} height={'50px'} width={'50px'} className={'logo'} />
                        </div>
                        <div style={{
                            fontSize: isMobile ? '36px' : '42px',
                            fontFamily: defaultFontFamily,
                            textAlign: 'left',
                            color: '#ffffff',
                            fontWeight: isMobile ? '10px' : '15px',
                            marginLeft: '10px',
                        }}>
                            GFI BOT
                        </div>
                    </Col>
                </Row>
                <Row>
                    <Col style={{
                        marginTop: '10px',
                    }}>
                        <Form.Group>
                            <InputGroup>
                                <Form.Control
                                    placeholder={'Github URL or Repo Name'}
                                    style={{
                                        minWidth: '240px',
                                        borderColor: '#ffffff',
                                        backgroundColor: 'rgba(255, 255, 255, 0.5)'
                                    }}
                                    aria-describedby={'append-icon'}
                                />
                                <Button variant={'outline-light'} style={{
                                    borderColor: 'rgba(255, 255, 255, 0.0)'
                                }}>
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
                </Row>
            </>
        )
    }

    const renderMainArea = () => {
        if (isMobile) {
            return (
                <Row>
                    {renderSearchArea()}
                </Row>
            )
        } else {
            return (
                    <Row>
                        <Col>
                            {renderSearchArea()}
                        </Col>
                        <Col />
                    </Row>
            )
        }
    }

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
                {renderMainArea()}
            </Container>
            <img src={backgroundLogo} alt={''} style={{
                width: isMobile ? width : width / 2,
                maxWidth: '1000px',
                position: 'fixed',
                right: '0',
                bottom: '0',
                opacity: '0.8',
            }} className={'logo'}/>
            <Container style={{
                backgroundImage: `url(${background})`,
                backgroundSize: 'cover',
                backgroundAttachment: 'fixed',
                width: width,
                maxWidth: width,
                height: height,
                position: 'fixed',
                top: '0',
                zIndex: '-999',
            }}>
            </Container>
        </>

    )
}