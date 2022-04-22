import React, {useEffect, useRef, useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';

import {Container, Nav, Navbar, Button, Popover, OverlayTrigger} from 'react-bootstrap';
import {LinkContainer} from 'react-router-bootstrap';
import {GithubFilled, UserDeleteOutlined} from '@ant-design/icons';
import 'bootstrap/dist/css/bootstrap.min.css';

import {gsap} from 'gsap';

import {useIsMobile} from './app/windowContext';
import {defaultFontFamily} from '../utils';
import {gitHubLogin} from '../api/githubApi';
import {createLogoutAction, LoginState} from '../module/storage/reducers';
import '../style/gfiStyle.css'

import navLogo from '../assets/favicon-thumbnail.png';

export const GFIHeader = () => {

    // Account Actions

    const dispatch = useDispatch()

    const logout = () => {
        dispatch(createLogoutAction())
    }

    const checkLogin = () => {
        // TODO: MSKYurina
        // currently for debugging
        logout()
    }

    useEffect(() => {
        checkLogin()
    }, [])

    const hasLogin = useSelector((state: LoginState) => {
        if ('hasLogin' in state) return state.hasLogin
        return undefined
    })

    const userName = useSelector((state: LoginState) => {
        if ('name' in state) return state.name
        return undefined
    })

    // Login / Logout related components

    const [popOverToggled, setPopOverToggled] = useState(false)
    const [showPopOver, setShowPopOver] = useState(false)
    const popOverRef = useRef<HTMLDivElement>(null)
    const loginBtnRef = useRef<HTMLDivElement>(null)

    const checkIfClosePopOver = (e: MouseEvent) => {
        const ele = e.target as Node
        if (popOverRef.current && !popOverRef.current.contains(ele) && loginBtnRef.current && !loginBtnRef.current.contains(ele)) {
            e.preventDefault()
            e.stopPropagation()
            setShowPopOver(false)
        }
    }

    useEffect(() => {
        if (popOverToggled) {
            window.addEventListener('mousedown', (e) => checkIfClosePopOver(e))
        }
        return () => {
            window.removeEventListener('mousedown', (e) => checkIfClosePopOver(e))
        }
    }, [popOverToggled])

    // Popover menu, currently for user logout

    const logoutPopover = (
        <Popover id={'popover-basic'}>
            <Popover.Body>
                <div ref={popOverRef}>
                    <p> <u> Hi, {userName} </u> </p>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                    }}>
                        <UserDeleteOutlined style={{
                            fontSize: '17px',
                        }}/>
                        <Button
                            onClick={logout}
                            size={'sm'}
                            variant={'outline-danger'}
                            style={{ marginLeft: 'auto' }}
                        >
                            Logout
                        </Button>
                    </div>
                </div>
            </Popover.Body>
        </Popover>
    )

    // Sign in component

    const signInLink = () => {
        const login = hasLogin === true && userName !== undefined
        if (!login) {
            return  (
                <Button
                    onClick={gitHubLogin}
                    variant={'outline-secondary'}
                    size={'sm'}
                    style={{ marginRight: '15px' }}
                    className={'sign-in'}
                >
                    {'Sign in via GitHub'}
                </Button>
            )
        } else {
            return (
                <div ref={loginBtnRef}>
                    <OverlayTrigger
                        trigger={'click'}
                        placement={'bottom'}
                        overlay={logoutPopover}
                        onToggle={() => {
                            setShowPopOver(true)
                            setPopOverToggled(true)
                        }}
                        show={showPopOver}
                        defaultShow={false}
                        delay={0}
                        flip={false}
                        onHide={undefined}
                        popperConfig={{}}
                        target={undefined}
                    >
                        <Button
                            variant={'outline-secondary'}
                            size={'sm'}
                            style={{
                                marginRight: '15px',
                            }}
                            onClick={() => {
                                if (showPopOver) {
                                    setShowPopOver(false)
                                    setPopOverToggled(false)
                                }
                            }}
                        >
                            {userName}
                        </Button>
                    </OverlayTrigger>
                </div>
            )
        }
    }

    // Display responsively

    const isMobile = useIsMobile()
    const iconRef = useRef(null)

    const renderNavItem = () => {

        const renderSignInItems = () => {

            const hoverTimeline = gsap.timeline()
            const hoveredColor = '#404040'
            const normalColor = '#707070'

            return (
                <Container style={{
                    padding: '0',
                    display: 'flex',
                    alignItems: 'center',
                    height: '40px',
                    marginRight: '0px',
                }}>
                    <div style={{
                        display: 'inline-block',
                        width: '80%',
                        textAlign: isMobile ? undefined: 'right',
                    }}>
                        {signInLink()}
                    </div>
                    <div style={{
                        display: 'inline-block',
                        width: '20%',
                        textAlign: 'right',
                    }}>
                        <GithubFilled
                            style={{fontSize: '30px', color: normalColor}}
                            onClick={() => window.open('https://github.com/osslab-pku/gfi-bot')}
                            onMouseEnter={() => {
                                hoverTimeline
                                    .pause()
                                    .clear()
                                    .to(iconRef.current, {
                                        color: hoveredColor,
                                        duration: 0.3,
                                    })
                                    .play()
                            }}
                            onMouseLeave={() => {
                                hoverTimeline
                                    .pause()
                                    .clear()
                                    .to(iconRef.current, {
                                        color: normalColor,
                                        duration: 0.1,
                                    })
                                    .play()
                            }}
                            ref={iconRef}
                        />
                    </div>
                </Container>
            )
        }

        const renderMobileSignIn = () => {
            if (isMobile) {
                return renderSignInItems()
            } else {
                return <></>
            }
        }

        const renderDesktopSignIn = () => {
            if (!isMobile) {
                return (
                    <Navbar.Collapse
                        className={'justify-content-end'}
                        style={{
                            fontFamily: defaultFontFamily,
                            maxWidth: '180px',
                        }}
                    >
                        {renderSignInItems()}
                    </Navbar.Collapse>
                )
            } else {
                return <></>
            }
        }

        return (
            <Container style={{marginRight: '5px', marginLeft: '5px', maxWidth: '100vw'}}>
                <LinkContainer to={'/'}>
                    <Navbar.Brand>
                        <img
                            alt={''}
                            src={navLogo}
                            width={'30'}
                            height={'30'}
                            className={'d-inline-block align-top'}
                        />
                        {' '} GFI-Bot
                    </Navbar.Brand>
                </LinkContainer>
                <Navbar.Toggle />
                <Navbar.Collapse>
                    <Nav>
                        <LinkContainer to={'/repos'}>
                            <Nav.Link> Repositories </Nav.Link>
                        </LinkContainer>
                        <LinkContainer to={'/home'}>
                            <Nav.Link> About Us </Nav.Link>
                        </LinkContainer>
                        {renderMobileSignIn()}
                    </Nav>
                </Navbar.Collapse>
                {renderDesktopSignIn()}
            </Container>
        )
    }

    // Explain:
    // The 'expand' property of React-bootstrap Navbar turn out to be effective (equals to 'false') even when set to 'true' or ''
    // so temporarily using two functions to render navbar responsively

    const renderDesktopNavbar = () => {
        return (
            <Navbar bg={'light'} sticky={'top'}>
                {renderNavItem()}
            </Navbar>
        )
    }

    const renderMobileNavbar = () => {
        return (
            <Navbar bg={'light'} sticky={'top'} expanded={false}>
                {renderNavItem()}
            </Navbar>
        )
    }

    const render = () => {
        if (!isMobile) {
            return renderDesktopNavbar()
        } else {
            return renderMobileNavbar()
        }
    }

    return (
        render()
    )
}
