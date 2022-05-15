// TODO:MSKYurina
// Refactor using TypeScript

import React, { useEffect, useRef, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'

import {
	Container,
	Nav,
	Navbar,
	Button,
	Popover,
	OverlayTrigger,
	ProgressBar,
} from 'react-bootstrap'
import { LinkContainer } from 'react-router-bootstrap'
import { GithubFilled, UserDeleteOutlined } from '@ant-design/icons'
import 'bootstrap/dist/css/bootstrap.min.css'

import { gsap } from 'gsap'

import { useIsMobile } from './app/windowContext'
import { defaultFontFamily } from '../utils'
import { gitHubLogin } from '../api/githubApi'
import {
	createAccountNavStateAction,
	createLogoutAction,
} from '../module/storage/reducers'
import '../style/gfiStyle.css'

import navLogo from '../assets/favicon-thumbnail.png'
import { GFIPortalPageNav } from './portal/GFIPortal'

export const GFIHeader = () => {
	const dispatch = useDispatch()

	const logout = () => {
		dispatch(createLogoutAction())
		window.location.reload()
	}

	const hasLogin = useSelector((state) => {
		if ('loginReducer' in state && 'hasLogin' in state.loginReducer)
			return state.loginReducer.hasLogin
		return undefined
	})

	const userName = useSelector((state) => {
		if ('loginReducer' in state && 'name' in state.loginReducer)
			return state.loginReducer.name
		return undefined
	})

	// Login / Logout related components

	const [popOverToggled, setPopOverToggled] = useState(false)
	const [showPopOver, setShowPopOver] = useState(false)
	const popOverRef = useRef(null)
	const loginBtnRef = useRef(null)

	const checkIfClosePopOver = (e) => {
		const ele = e.target
		if (
			popOverRef.current &&
			!popOverRef.current.contains(ele) &&
			!loginBtnRef.current.contains(ele)
		) {
			e.preventDefault()
			e.stopPropagation()
			setShowPopOver(false)
		}
	}

	useEffect(() => {
		if (popOverToggled === true) {
			window.addEventListener('mousedown', (e) => checkIfClosePopOver(e))
		}
		return () => {
			window.removeEventListener('mousedown', (e) =>
				checkIfClosePopOver(e)
			)
		}
	}, [popOverToggled])

	// Popover menu, currently for user logout

	const logoutPopover = (
		<Popover id={'popover-basic'}>
			<Popover.Body>
				<div ref={popOverRef}>
					<p>
						{' '}
						<u> Hi, {userName} </u>{' '}
					</p>
					<div
						style={{
							display: 'flex',
							justifyContent: 'center',
							alignItems: 'center',
						}}
					>
						<UserDeleteOutlined
							style={{
								fontSize: '17px',
							}}
						/>
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
			return (
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

	const hideAccountNav = () => {
		dispatch(createAccountNavStateAction({ show: false }))
	}
	const showAccountNav = () => {
		dispatch(createAccountNavStateAction({ show: true }))
	}

	const renderNavItem = () => {
		const renderSignInItems = () => {
			const hoverTimeline = gsap.timeline()
			const hoveredColor = '#404040'
			const normalColor = '#707070'

			return (
				<Container
					style={{
						padding: '0',
						display: 'flex',
						alignItems: 'center',
						height: '40px',
						marginRight: '0px',
					}}
				>
					<div
						style={{
							display: 'inline-block',
							width: '80%',
							textAlign: isMobile ? '' : 'right',
						}}
					>
						{signInLink()}
					</div>
					<div
						style={{
							display: 'inline-block',
							width: '20%',
							textAlign: 'right',
						}}
					>
						<GithubFilled
							style={{ fontSize: '30px', color: normalColor }}
							onClick={() =>
								window.open(
									'https://github.com/osslab-pku/gfi-bot'
								)
							}
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

		const MyPage = () => {
			if (hasLogin) {
				return (
					<LinkContainer
						to={'/portal'}
						onClick={() => {
							showAccountNav()
						}}
					>
						<Nav.Link> Portal </Nav.Link>
					</LinkContainer>
				)
			}
			return <></>
		}

		return (
			<Container
				style={{
					marginRight: '5px',
					marginLeft: '5px',
					maxWidth: '100vw',
				}}
			>
				<LinkContainer
					to={'/'}
					onClick={() => {
						hideAccountNav()
					}}
				>
					<Navbar.Brand>
						<img
							alt={''}
							src={navLogo}
							width={'30'}
							height={'30'}
							className={'d-inline-block align-top'}
						/>{' '}
						GFI-Bot
					</Navbar.Brand>
				</LinkContainer>
				<Navbar.Toggle />
				<Navbar.Collapse>
					<Nav>
						{MyPage()}
						<LinkContainer
							to={'/home'}
							onClick={() => {
								hideAccountNav()
							}}
						>
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
			<div className={'flex-col sticky-top'}>
				<Navbar bg={'light'} sticky={'top'}>
					{renderNavItem(false)}
				</Navbar>
				<GFIGlobalProgressBar />
			</div>
		)
	}

	const renderMobileNavbar = () => {
		return (
			<>
				<Navbar bg={'light'} sticky={'top'} expand={'false'}>
					{renderNavItem(true)}
				</Navbar>
				<GFIGlobalProgressBar />
			</>
		)
	}

	const render = () => {
		if (!isMobile) {
			return renderDesktopNavbar()
		} else {
			return renderMobileNavbar()
		}
	}

	const shouldShowAccountNav = useSelector((state) => {
		if (
			'accountNavStateReducer' in state &&
			'show' in state.accountNavStateReducer
		)
			return state.accountNavStateReducer.show
		return false
	})

	return (
		<>
			{render()}
			{shouldShowAccountNav && (
				<GFIPortalPageNav id={'portal-page-nav'} />
			)}
		</>
	)
}

const GFIGlobalProgressBar = () => {
	const ref = useRef(null)
	const hidden = useSelector((state) => {
		if (
			'globalProgressBarReducer' in state &&
			'hidden' in state.globalProgressBarReducer
		) {
			if (state.globalProgressBarReducer.hidden) {
				return 'gfi-hidden-with-space'
			}
		}
		return ''
	})

	return (
		<>
			<ProgressBar
				ref={ref}
				className={`progress-bar-thin ${hidden} sticky-top transition-01`}
				animated={true}
				now={100}
			/>
		</>
	)
}
