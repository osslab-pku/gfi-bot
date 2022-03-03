import React, {useEffect, useRef} from 'react';
import {useSelector} from 'react-redux';

import 'bootstrap/dist/css/bootstrap.min.css';
import {Container, Nav, Navbar, Button} from 'react-bootstrap';
import {LinkContainer} from 'react-router-bootstrap';
import {GithubFilled} from '@ant-design/icons';

import {gsap} from 'gsap';

import {useWindowSize} from './app/windowContext';
import {defaultFontFamily} from '../utils';
import {gitHubLogin} from '../api/api';

import navLogo from '../assets/favicon-thumbnail.png';

export const GFIHeader = () => {

    const {width} = useWindowSize()
    const widthThreshold = 630
    const hasLogin = useSelector(state => {
        if ('hasLogin' in state) return state.hasLogin
        return undefined
    })
    const userName = useSelector(state => {
        if ('name' in state) return state.name
        return undefined
    })

    const checkLogin = () => {
        // TODO: MSKYurina
    }

    useEffect(() => {
        checkLogin()
        console.log(userName)
    }, [])

    // Explain:
    // The 'expand' property of React-bootstrap Navbar turn out to be effective (equals to 'false') even when set to 'true' or ''
    // so temporarily using two functions to render navbar responsively

    const signInLink = () => {
        const login = hasLogin === true && userName !== undefined
        return (
            <Button onClick={login ? () => {}: gitHubLogin} variant={'outline-secondary'} size={'sm'} style={{
                marginRight: '15px',
            }}>
                {login ? userName : 'Sign in via GitHub'}
            </Button>
        )
    }

    const iconRef = useRef(null)

    const renderNavItem = (isMobile: Boolean) => {

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
                        textAlign: isMobile ? '': 'right',
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
                            onClick={() => window.open('https://github.com')}
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
                    <Navbar.Collapse className={'justify-content-end'} style={{
                        fontFamily: defaultFontFamily,
                        maxWidth: '180px',
                    }}>
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

    const renderDesktopNavbar = () => {
        return (
            <Navbar bg={'light'} sticky={'top'}>
                {renderNavItem(false)}
            </Navbar>
        )
    }

    const renderMobileNavbar = () => {
        return (
            <Navbar bg={'light'} sticky={'top'} expand={'false'}>
                {renderNavItem(true)}
            </Navbar>
        )
    }

    const render = () => {
        if (width > widthThreshold) {
            return renderDesktopNavbar()
        } else {
            return renderMobileNavbar()
        }
    }

    return (
        render()
    )
}
