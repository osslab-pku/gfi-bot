import React, {MouseEventHandler, useEffect, useRef, useState} from 'react';
import {Button, Col, Container, Form, ListGroup, Nav, Overlay, Popover, Row} from 'react-bootstrap';
import {LinkContainer} from 'react-router-bootstrap';
import {withRouter} from 'react-router-dom';

import '../../style/gfiStyle.css'
import {useDispatch, useSelector} from 'react-redux';
import {createAccountNavStateAction} from '../../module/storage/reducers';
import {GFIRootReducers} from '../../module/storage/configureStorage';
import {checkIsGitRepoURL} from '../../utils';

import importTips from '../../assets/git-add-demo.png'
import {checkHasRepoPermissions} from '../../api/githubApi';
import {GFIAlarm, GFIAlarmPanelVariants} from '../GFIComponents';
import {addRepoToGFIBot, getAddRepoHistory} from '../../api/api';
import {GFIRepoInfo, GFIUserSearchHistoryItem} from '../../module/data/dataModel';

export interface GFIPortal {}

type SubPanelIDs = 'Add Project' | 'Search History' | 'My Account'
const SubPanelTitles: SubPanelIDs[] & string[] = [
	'Add Project',
	'Search History',
	'My Account',
]

export const GFIPortal = (props: GFIPortal) => {

	const dispatch = useDispatch()
	useEffect(() => {
		dispatch(createAccountNavStateAction({ show: true }))
	}, [])

	const [currentPanelID, setCurrentPanelID] = useState<SubPanelIDs & string>('Add Project')

	const renderSubPanel = () => {
		if (currentPanelID === 'Add Project') {
			return <AddProjectComponent />
		} else if (currentPanelID === 'Search History') {
			return <></>
		} else if (currentPanelID === 'My Account') {
			return <></>
		}
	}

	return (
		<Container className={'account-page-sub-container'}>
			<Row className={'account-page-sub-container-row'}>
				<Col sm={3}>
					<AccountSideBar
						actionList={SubPanelTitles}
						onClick={(i) => {
							setCurrentPanelID(SubPanelTitles[i])
						}}
					/>
				</Col>
				<Col sm={9}> {renderSubPanel()} </Col>
			</Row>
		</Container>
	)
}

export const GFIPortalPageNav = withRouter((props: {id?: string}) => {
	return (
		<>
			<Nav
				variant={'pills'}
				className={'flex-row justify-content-center align-center'}
				id={props?.id}
				style={{ marginTop: '10px' }}
			>
				<Nav.Item className={'account-nav-container'}>
					<LinkContainer to={'/portal'}>
						<Nav.Link eventKey={1} className={'account-nav'}>
							Dashboard
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


interface AccountSideBar {
	actionList: string[]
	onClick?: (i: number) => void
}

const AccountSideBar = (props: AccountSideBar) => {
	const {actionList, onClick} = props
	const [selectedList, setSelectedList] = useState(actionList.map((_, i) => {
		return !i;
	}))

	const userName = useSelector((state: GFIRootReducers) => {
		if ('name' in state.loginReducer) return state.loginReducer.name
		return undefined
	})

	const userAvatar = useSelector((state: GFIRootReducers) => {
		if ('avatar' in state.loginReducer) return state.loginReducer.avatar
		return undefined
	})

	const renderItems = () => {
		return actionList.map((title, i) => {
			return (
				<ListGroup.Item
					action={true}
					as={'button'}
					onClick={() => {
						setSelectedList(selectedList.map((_, idx) => { return idx === i }))
						if (onClick) {
							onClick(i)
						}
					}}
					variant={ selectedList[i] ? 'primary': 'light' }
				>
					{title}
				</ListGroup.Item>
			)
		})
	}

	return (
		<div className={'flex-col flex-wrap'} id={'portal-side-bar'}>
			<div className={'flex-row align-center'} id={'portal-side-bar-userinfo'}>
				<div className={'flex-col'} id={'portal-side-bar-userinfo-name'}>
					<div> Hello, </div>
					<div> {userName} </div>
				</div>
				<img src={userAvatar} alt={''}/>
			</div>
			<ListGroup>
				{renderItems()}
			</ListGroup>
		</div>
	)
}

const AddProjectComponent = () => {

	const [projectURL, setProjectURL] = useState<string>()
	const [showAlarmMsg, setShowAlarmMsg] = useState(false)

	const [mainAlarmConfig, setMainAlarmConfig] = useState<{
		show: boolean,
		msg: string,
		variant ?: GFIAlarmPanelVariants,
	}>({ show: false, msg: '', variant: 'danger' })

	const [addedRepos, setAddedRepos] = useState<GFIUserSearchHistoryItem[]>()
	const fetchAddedRepos = () => {
		getAddRepoHistory().then((res) => {
			const finishedQueries: GFIUserSearchHistoryItem[] | undefined = res?.finished_queries?.map((info) => {
				return {
					pending: false,
					repo: info,
				}
			})
			const pendingQueries: GFIUserSearchHistoryItem[] | undefined = res?.queries?.map((info) => {
				return {
					pending: true,
					repo: info,
				}
			})
			setAddedRepos(finishedQueries ? finishedQueries.concat(pendingQueries) : pendingQueries)
		})
	}
	useEffect(() => {
		fetchAddedRepos()
	}, [])

	const addGFIRepo = () => {
		let shouldDisplayAlarm = true
		if (projectURL && checkIsGitRepoURL(projectURL)) {
			const urls = projectURL.split('/')
			const repoName = urls[urls.length - 1].split('.git')[0]
			const repoOwner = urls[urls.length - 2]
			if (repoName && repoOwner) {
				checkHasRepoPermissions(repoName, repoOwner).then((res) => {
					if (res) {
						addRepoToGFIBot(repoName, repoOwner).then((result?: string) => {
							if (result) {
								setMainAlarmConfig({
									show: true,
									msg: `Repo ${repoOwner}/${repoName} ${result}`,
									variant: 'success',
								})
								fetchAddedRepos()
							} else {
								setMainAlarmConfig({
									show: true,
									msg: `Connection Lost`,
									variant: 'danger',
								})
							}
						})
					} else {
						setMainAlarmConfig({
							show: true,
							msg: `You\'re not a maintainer of ${repoOwner}/${repoName}`,
							variant: 'danger',
						})
					}
				})
				shouldDisplayAlarm = false
			}
		}
		setShowAlarmMsg(shouldDisplayAlarm)
	}

	const [overlayTarget, setOverlayTarget] = useState<EventTarget>()
	const [showOverlay, setShowOverlay] = useState(false)
	const overlayContainer = useRef(null)
	const popoverRef = useRef<HTMLDivElement>(null)
	const onErrorTipClick: MouseEventHandler<HTMLDivElement> = (e) => {
		setOverlayTarget(e.target)
		setShowOverlay(!showOverlay)
	}
	const checkIfClosePopover = (e: MouseEvent) => {
		if (!popoverRef?.current?.contains(e.target as Node)) {
			setShowOverlay(false)
		}
	}

	useEffect(() => {
		if (showOverlay) {
			document.addEventListener('mousedown', checkIfClosePopover)
		} else {
			document.removeEventListener('mousedown', checkIfClosePopover)
		}
		return () => {
			document.removeEventListener('mousedown', checkIfClosePopover)
		}
	}, [showOverlay])

	const onRepoHistoryClicked = (repoInfo: GFIRepoInfo) => {
		console.log(repoInfo)
	}

	const renderRepoHistory = () => {
		if (addedRepos) {
			return addedRepos.map((item) => {
				return <RepoHistoryTag pending={item.pending} repoInfo={item.repo} available={true} onClick={onRepoHistoryClicked} />
			})
		}
		return (
			<RepoHistoryTag
				pending={true}
				repoInfo={{
					name: 'None',
					owner: 'Try to add your projects!',
				}}
				available={false}
			/>
		)
	}

	return (
		<div className={'flex-col'}>
			{mainAlarmConfig.show ?
				<GFIAlarm
					title={mainAlarmConfig.msg}
					onClose={() => setMainAlarmConfig({
						show: false,
						msg: ''
					})}
					variant={mainAlarmConfig?.variant}
				/> : <></>
			}
			<div className={'account-page-panel-title'} id={'project-add-comp-title'}>
				Add Your Project To GFI-Bot
			</div>
			<div id={'project-add-comp-tips'}>
				<p> <strong>Notice: </strong> We'll register the repository to our database and use it for data training and predictions. </p>
				<p> Make sure that you are one of the maintainers of the repository. </p>
			</div>
			<div id={'project-adder'}>
				<Form className={'flex-col'} id={'project-adder-form'}>
					<Form.Label id={'project-adder-label'}> Please input a GitHub Repo URL </Form.Label>
					<Form.Control
						placeholder={'GitHub URL'}
						onChange={(e) => {
							setProjectURL(e.target.value)
						}}
						onKeyDown={(event) => {
							if (event.key === 'Enter') {
								event.preventDefault()
								addGFIRepo()
							}
						}}
					/>
					<div className={'flex-row align-center'} style={{ marginTop: '0.5rem' }}>
						{showAlarmMsg &&
							<div ref={overlayContainer}>
                                <div
	                                className={'hoverable'}
	                                id={'project-add-alarm'}
	                                onClick={onErrorTipClick}
                                >
                                    Please input a correct GitHub Repo URL
                                </div>
								<Overlay
									show={showOverlay}
									// @ts-ignore
									target={overlayTarget}
									container={overlayContainer}
									placement={'bottom-start'}
								>
									<Popover className={'fit'} ref={popoverRef}>
										<Popover.Body className={'fit'}>
											<img src={importTips} alt={''} id={'project-add-overlay-warn-tip'} />
										</Popover.Body>
									</Popover>
								</Overlay>
							</div>
						}
						<Button
							size={'sm'}
							variant={'outline-primary'}
							style={{ marginLeft: 'auto' }}
							onClick={() => {
								addGFIRepo()
							}}
						> Add Project </Button>
					</div>
				</Form>
			</div>
			<div className={'account-page-panel-title'} id={'project-add-comp-added'}>
				Project Added
			</div>
			<div className={'flex-row flex-wrap align-center'} style={{ marginTop: '0.7rem' }}>
				{renderRepoHistory()}
			</div>
			<div className={'account-page-panel-title'} id={'project-add-comp-tutorial'}>
				Tutorial
			</div>
			<div id={'account-page-panel-tutorial'}>
				<p> To Be Completed. </p>
				<p> We describe our envisioned use cases for GFI-Bot in this <a href={'https://github.com/osslab-pku/gfi-bot/blob/main/USE_CASES.md'}>documentation</a>. </p>
			</div>
		</div>
	)
}

const RepoHistoryTag = (props: {pending: boolean, repoInfo: GFIRepoInfo, available: boolean, onClick?: (repoInfo: GFIRepoInfo) => void}) => {
	const {pending, repoInfo, available, onClick} = props
	const isPending = available ? (pending ? 'query-pending': 'query-succeed'): 'query-none'
	const stateMsg = available ? (pending ? 'Pending': 'Succeed'): ''
	return (
		<div
			className={`repo-history-tag ${isPending} hoverable`}
			onClick={() => {
				if (onClick) {
					onClick(repoInfo)
				}
			}}
		>
			<div> {repoInfo.owner} {available ? '|': ''} {stateMsg} </div>
			<div> {repoInfo.name} </div>
		</div>
	)
}
