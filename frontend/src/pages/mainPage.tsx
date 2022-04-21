import React, {forwardRef, Key, useEffect, useRef, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {useIsMobile, useWindowSize} from './app/windowContext';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';

import {Container, Col, Row, Form, InputGroup, Button} from 'react-bootstrap';
import {gsap} from 'gsap';
import {ReloadOutlined, UpOutlined, DownOutlined} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkGemoji from 'remark-gemoji';

import background from '../assets/Tokyo-Tower-.jpg';
import gfiLogo from '../assets/gfi-logo.png';

import '../style/gfiStyle.css'
import {SearchOutlined} from '@ant-design/icons';
import {checkIsNumber, defaultFontFamily} from '../utils';

import {GFINotiToast} from './login/welcomePage';
import {GFIAlarm, GFICopyright, GFIPagination} from './gfiComponents';
import {
	getRecommendedRepoInfo,
	getGFIByRepoName,
	getRepoNum,
	getIssueNum,
	getLanguageTags,
	getRepoInfoByNameOrURL, getRepoDetailedInfo, getProcessingSearches
} from '../api/api';
import {getIssueByRepoInfo, userInfo} from '../api/githubApi';
import type {LoginState} from '../module/storage/reducers';

import {checkIsGitRepoURL} from '../utils';
import {useSucceedQuery} from './app/processStatusProvider';

// TODO: MSKYurina
// Animation & Searching History

interface RepoInfo {
	name: string,
	owner: string,
	url?: string,
}

export const MainPage = () => {

	let [showLoginMsg, setShowLoginMsg] = useState(false)
	let [showSearchMsg, setShowSearchMsg] = useState(false)

	const succeedQuery = useSucceedQuery()
	useEffect(() => {
		console.log(succeedQuery)
	}, [succeedQuery])

	const isMobile = useIsMobile()
	const {width, height} = useWindowSize()

	const userName = useSelector((state: LoginState) => {
		if ('name' in state) return state.name
		return ''
	})

	const userAvatarUrl = useSelector((state: LoginState) => {
		if ('avatar' in state) return state.avatar
		return ''
	})

	const defaultRepoInfo = {
		name: '',
		owner: '',
		url: '',
	}

	let [recommendedRepoInfo, setRecommendedRepoInfo] = useState<RepoInfo | undefined>(defaultRepoInfo)

	let [searchedRepoInfo, setSearchedRepoInfo] = useState<RepoInfo[] | undefined>([defaultRepoInfo])

	let [alarmConfig, setAlarmConfig] = useState({
		show: false,
		msg: ''
	})

	const showAlarm = (msg: string) => {
		setAlarmConfig({
			show: true,
			msg: msg,
		})
	}

	const fetchRepoInfo = async () => {
		const res = await getRecommendedRepoInfo()
		if ('name' in res && 'owner' in res) {
			setRecommendedRepoInfo(res)
		} else {
			setRecommendedRepoInfo({
				name: '',
				owner: '',
				url: '',
			})
		}
	}

	interface LocationStateLoginType {
		state: {
			justLogin: boolean
		}
	}

	const location = useLocation() as LocationStateLoginType

	useEffect(() => {
		getRecommendedRepoInfo()
			.then((info?: RepoInfo) => {
				setRecommendedRepoInfo(info)
			})

		if ('state' in location && location.state && location.state.justLogin) {
			setShowLoginMsg(true)
		}
	}, [])

	const repoCapacity = 3
	let [pageIdx, setPageIdx] = useState(1)
	let [totalRepos, setTotalRepos] = useState(0)
	let [repoTag, setRepoTag] = useState('')
	let [pageFormInput, setPageFormInput] = useState<string | number | undefined>(0)

	const pageNums = () => {
		if (totalRepos % repoCapacity === 0) {
			return Math.floor(totalRepos / repoCapacity)
		} else {
			return Math.floor(totalRepos / repoCapacity) + 1
		}
	}

	const toPage = (i: number) => {
		if (1 <= i && i <= pageNums()) {
			setPageIdx(i)
		}
	}

	const onKanbanClicked: React.MouseEventHandler<HTMLButtonElement> = (e) => {
		const element = e.target as HTMLElement
		const tag = element.innerText
		setSearchedRepoInfo([])
		setShowRecommended(false)
		getRepoNum(tag)
			.then((res) => {
				if (res && Number.isInteger(res)) {
					setTotalRepos(res)
					setRepoTag(tag)
				} else {
					setTotalRepos(0)
				}
				setPageIdx(1)
			})
	}

	useEffect(() => {
		fetchRepoInfoList(1, repoTag)
	}, [repoTag])

	useEffect(() => {
		fetchRepoInfoList(pageIdx, repoTag)
	}, [pageIdx])

	const fetchRepoInfoList = (pageNum: number, tag?: string) => {
		let beginIdx = (pageNum - 1) * repoCapacity
		getRepoDetailedInfo(beginIdx, repoCapacity, tag).then((repoList) => {
			if (repoList && Array.isArray(repoList)) {
				const repoInfoList = repoList.map((repo, i) => {
					const parsedRepo = JSON.parse(repo)
					console.log(parsedRepo)
					if ('name' in parsedRepo && 'owner' in parsedRepo) {
						return {
							name: parsedRepo.name,
							owner: parsedRepo.owner,
							url: '',
						}
					} else {
						return defaultRepoInfo
					}
				})
				console.log(repoInfoList)
				setSearchedRepoInfo(repoInfoList)
			}
		})
	}

	const onPageBtnClicked = () => {
		if (checkIsNumber(pageFormInput)) {
			pageFormInput = Number(pageFormInput)
			if (pageFormInput > 0 && pageFormInput <= pageNums()) {
				toPage(pageFormInput)
			}
		}
	}

	const renderLogo = () => {
		if (width > 700 || isMobile) {
			return (
				<img src={gfiLogo} alt={''} height={'32px'} width={'32px'} className={'logo'} style={{
					opacity: '0.8',
					marginRight: '15px',
				}} />
			)
		} else {
			return <></>
		}
	}

	let [searchURL, setSearchURL] = useState('')
	let [showRecommended, setShowRecommended] = useState(true)
	let [queryNums, setQueryNums] = useState(0)
	let [succeedQueries, setSucceedQueries] = useState([])
	let [searchStarted, setSearchStarted] = useState(false)
	let [intervalId, setIntervalId] = useState<ReturnType<typeof setTimeout>>()

	const showSearchResult = () => {
		if (succeedQueries.length && searchStarted) {
			const repoInfo = succeedQueries.map((item, _) => {
				return {
					name: item,
					owner: '',
					url: '',
				}
			})
			if (repoInfo !== searchedRepoInfo) {
				setSearchedRepoInfo(repoInfo)
			}
			setShowRecommended(false)
			setSearchStarted(false)
			setShowSearchMsg(false)
		}
	}

	useEffect(() => {
		if (queryNums === 0 && searchStarted) {
			clearInterval(intervalId as ReturnType<typeof setTimeout>)
			getProcessingSearches(true).then(() => {})
			setShowSearchMsg(true)
		}
	}, [queryNums])

	const handleSearchBtn = () => {
		if (checkIsGitRepoURL(searchURL)) {
			getRepoInfoByNameOrURL('', searchURL).then((res) => {
				if (res && 'name' in res && 'owner' in res) {
					setShowRecommended(true)
					setRecommendedRepoInfo(res)
				} else {
					const [hasLogin, userName] = userInfo()
					if (!hasLogin) {
						setAlarmConfig({
							show: true,
							msg: 'You Need to Login For Data Retrieving',
						})
					} else {
						if (!searchStarted) {
							setSearchStarted(true)
							const id = setInterval(() => {
								getProcessingSearches(false).then((res) => {
									if ('user_query_num' in res) {
										if (res.user_query_num !== 0) {
											setAlarmConfig({
												show: true,
												msg: `${res.user_query_num} Requests Under Processing`,
											})
										}
										setQueryNums(res.user_query_num)
										if (queryNums === 0) {
											clearInterval(intervalId as ReturnType<typeof setTimeout>)
										}
									}
									if ('user_succeed_queries' in res) {
										setSucceedQueries(res.user_succeed_queries)
									}
								})
							}, 500)
							setIntervalId(id)
						}
					}
				}
			})
		} else if (!recommendedRepoInfo || searchURL !== recommendedRepoInfo.name) {
			getRepoInfoByNameOrURL(searchURL, '').then((res) => {
				console.log(res)
				if (res && ('name' in res) && ('owner' in res)) {
					setRecommendedRepoInfo(res)
				} else {
					setAlarmConfig({
						show: true,
						msg: 'Repo Name Doesn\'t Exist',
					})
				}
			})
		}
	}

	const renderSearchArea = () => {

		return (
			<>
				<Row>
					<Col style={{
						marginTop: '30px',
					}}>
						<Form.Group>
							<InputGroup style={{
								display: 'flex',
								alignItems: 'center',
							}}>
								{renderLogo()}
								<Form.Control
									placeholder={'Github URL or Repo Name'}
									style={{
										minWidth: '240px',
										borderColor: '#ffffff',
										backgroundColor: 'rgba(255, 255, 255, 0.5)',
										borderTopLeftRadius: '17px',
										borderBottomLeftRadius: '17px',
										borderRightColor: 'rgba(255, 255, 255, 0)',
									}}
									aria-describedby={'append-icon'}
									onChange={(event) => {setSearchURL(event.target.value)}}
									onKeyDown={(e) => {
										if (e.key === 'Enter') {
											e.preventDefault()
											handleSearchBtn()
										}
									}}
									type={'input'}
								/>
								<Button
									variant={'outline-light'}
									onClick={handleSearchBtn}
									style={{
										borderLeftColor: 'rgba(255, 255, 255, 0)',
										width: '40px',
										alignItems: 'center',
										justifyContent: 'center',
										display: 'flex',
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

	const renderInfoComponent = () => {
		if (showRecommended) {
			return (
				<InfoShowComponent
					key={recommendedRepoInfo?.url as Key}
					repoInfo={recommendedRepoInfo}
					onRefresh={fetchRepoInfo}
					onRequestFailed={(msg: string) => {
						showAlarm(msg)
					}}
					isRecommended={showRecommended}
				/>
			)
		} else if (searchedRepoInfo && searchedRepoInfo.length) {
			return searchedRepoInfo.map((item, _) => {
				return (
					<InfoShowComponent
						key={item.url as Key}
						repoInfo={item}
						onRefresh={fetchRepoInfo}
						onRequestFailed={(msg: string) => {
							showAlarm(msg)
						}}
						isRecommended={showRecommended}
					/>
				)
			})
		} else {
			return (
				<></>
			)
		}
	}

	const renderMainArea = () => {
		return (
			<>
				<Row>
					<Col>
						{renderSearchArea()}
					</Col>
					{isMobile ? <></> : <Col/>}
				</Row>
				<Row>
					<Col style={{
						display: 'flex',
						alignItems: 'flex-start',
						justifyContent: 'flex-start',
					}}>
						<Container style={{
							marginTop: '30px',
							display: 'flex',
							padding: '0px',
							marginLeft: '0px',
							maxWidth: isMobile ? '100%' : '70%',
							flexDirection: 'column',
						}}>
							{renderInfoComponent()}
							{!showRecommended ?
								<>
									<GFIPagination
										className={'dark-paging'}
										pageIdx={pageIdx}
										toPage={(pageNum) => {toPage(pageNum)}}
										pageNums={pageNums()}
										onFormInput={(target) => {
											const t = target as HTMLTextAreaElement
											setPageFormInput(t.value)
										}}
										onPageBtnClicked={() => {onPageBtnClicked()}}
										maxPagingCount={3}
										needPadding={false}
									/>
								</> : <></>
							}
						</Container>
						{(width > 1000) ? <Container style={{
							maxWidth: '30%',
							marginTop: '30px',
						}}>
							<GFIDadaKanban onTagClicked={onKanbanClicked} />
						</Container> : <></>}
					</Col>
				</Row>
			</>
		)
	}

	return (
		<>
			<Container className={'single-page'}>
				<Row style={{
					marginBottom: alarmConfig.show? '-25px': '0',
					marginTop: alarmConfig.show? '25px': '0',
				}}>
					{alarmConfig.show ?
						<GFIAlarm
							title={alarmConfig.msg}
							onClose={() => {setAlarmConfig({show: false, msg: alarmConfig.msg})}}
						/> : <></>}
				</Row>
				<Row>
					<GFINotiToast
						show={showLoginMsg}
						userName={userName ? userName: 'visitor'}
						userAvatarUrl={userAvatarUrl}
						onClose={() => {
							setShowLoginMsg(false)
						}}
					/>
					<GFINotiToast
						show={showSearchMsg}
						userName={userName ? userName: 'visitor'}
						userAvatarUrl={userAvatarUrl}
						onClose={() => {
							setShowSearchMsg(false)
						}}
						context={'Searching Completed!'}
						buttonContext={'Display'}
						onClick={showSearchResult}
					/>
				</Row>
				{renderMainArea()}
				<Row style={{
					color: 'white',
					bottom: '0',
				}}>
					<GFICopyright />
				</Row>
			</Container>
			<Container style={{
				// backgroundImage: `url(${background})`,
				// backgroundSize: 'cover',
				// backgroundAttachment: 'fixed',
				width: width,
				maxWidth: width,
				height: height,
				position: 'fixed',
				top: '0',
				zIndex: '-1000',
			}} className={'background'} />
		</>
	)
}

interface InfoShowComponentProps {
	repoInfo?: {
		name?: string,
		owner?: string,
	},
	onRefresh: React.MouseEventHandler<HTMLButtonElement>,
	onRequestFailed: (msg: string) => void,
	isRecommended: boolean,
}

const InfoShowComponent = React.forwardRef((props: InfoShowComponentProps, ref) => {

	let expRef = useRef(null)

	const {repoInfo, onRefresh, onRequestFailed, isRecommended} = props

	let [issueIdList, setIssueIdList] = useState<any[]>([])
	useEffect(() => {
		setIssueIdList([])
		if (repoInfo && repoInfo.name) {
			getGFIByRepoName(repoInfo.name).then((res) => {
				if (Array.isArray(res)) {
					setIssueIdList(res)
				} else {
					onRequestFailed('Lost connection with server')
				}
			})
		}
	}, [repoInfo])

	const recommended = () => {
		return (
			<>
				<div style={{
					height: '30px',
					borderColor: '#ffffff',
					border: 'solid 1px white',
					borderRadius: '15px',
					boxSizing: 'border-box',
					marginRight: '20px',
					display: 'inline-block',
				}}>
					<div style={{
						display: 'flex',
						justifyContent: 'center',
						alignItems: 'flex-start',
					}}>
						<p style={{
							paddingLeft: '12px',
							marginTop: '1.5px',
							marginBottom: '0px',
							fontFamily: defaultFontFamily,
							fontWeight: 'bold',
							color: 'white',
						}}> Recommended </p>
						<Button variant={'outline-light'} onClick={onRefresh} className={'transparent'} style={{
							display: 'flex',
							justifyContent: 'center',
							borderRadius: '20px',
							width: '40px',
						}}>
							<ReloadOutlined style={{
								color: 'white',
							}} />
						</Button>
					</div>
				</div>
			</>
		)
	}

	return (
		<Container style={{
			padding: '15px',
			marginLeft: '0px',
			marginBottom: '2rem',
		}} className={'rounded-container largeRadius'}>
			<Row>
				<Col>
					{isRecommended ? recommended() : <></>}
					<div style={{
						fontFamily: defaultFontFamily,
						fontSize: '32px',
						fontWeight: 'bold',
						color: 'white',
						alignItems: 'center',
						justifyContent: 'flex-start',
						display: 'flex',
						// when using 'transparent' class, background color will show when mouse hovered
						backgroundColor: 'rgba(255, 255, 255, 0)',
						borderColor: 'rgba(255, 255, 255, 0)',
					}}>
						<u> {repoInfo && 'name' in repoInfo ? repoInfo.name : ''} </u>
					</div>
				</Col>
				{issueIdList && typeof Array.isArray(issueIdList) ? issueIdList.map((issueId, idx) => {
					return (
						<Row key={`gfi-card-${idx}`}>
							<GFIIssueDisplayCard
								issueId={issueId && checkIsNumber(issueId) ? Number(issueId) : ''}
								repoOwner={repoInfo && repoInfo.owner}
								repoName={repoInfo && repoInfo.name}
								onRequestFailed={(msg) => {
									onRequestFailed(msg)
								}}
							/>
						</Row>
					)
				}) : <></>}
			</Row>
		</Container>
	)
})

interface GFIIssueDisplayCardProps {
	repoName?: string,
	repoOwner?: string,
	issueId: number | string,
	onRequestFailed: (msg: string) => void,
}

const GFIIssueDisplayCard = forwardRef((props: GFIIssueDisplayCardProps, ref) => {

	const {repoName, repoOwner, issueId, onRequestFailed} = props

	let detailedRef = useRef(null)
	let detailTimeline = gsap.timeline()
	let [detailOnDisplay, setDetailOnDisplay] = useState(false)
	let [detailBtn, setDetailBtn] = useState(false)

	const defaultIssueData = {
		issueId: '',
		title: '',
		body: '',
		isClosed: false,
		hasResolved: false,
		htmlURL: '',
	}

	let [displayData, setDisplayData] = useState(defaultIssueData)

	const getIssueInfo = (name: string, owner?: string) => {
		getIssueByRepoInfo(name, owner, issueId).then((res) => {
			console.log(res)
			if (res.code === 200) {
				if ('number' in res.result && 'title' in res.result && 'state' in res.result
					&& 'active_lock_reason' in res.result && 'body' in res.result && 'html_url' in res.result) {
					setDisplayData({
						issueId: res.result.number,
						title: res.result.title,
						body: res.result.body,
						isClosed: res.result.state === 'closed',
						hasResolved: res.result.active_lock_reason === 'resolved',
						htmlURL: res.result.html_url,
					})
				}
			} else if (res.code === 403) {
				onRequestFailed('GitHub API rate limit exceeded, you may sign in using a GitHub account to continue')
			}
		})
	}

	useEffect(() => {
		setDisplayData(defaultIssueData)
		if (repoName && (!repoOwner || repoOwner === '')) {
			getRepoInfoByNameOrURL(repoName, '').then((res) => {
				if (res && 'owner' in res) {
					getIssueInfo(repoName, res.owner)
				}
			})
		} else if (repoName) {
			getIssueInfo(repoName, repoOwner)
		}

	}, [repoName, repoOwner, issueId])

	const detailOnShow = () => {
		detailTimeline
			.pause()
			.clear()
			.to(detailedRef.current, {
				duration: 0.3,
				autoAlpha: 1,
				height: 'fit-content'
			})
			.play()
		setDetailOnDisplay(true)
		setDetailBtn(true)
	}

	const detailOffShow = () => {
		setDetailBtn(false)
		detailTimeline
			.pause()
			.clear()
			.to(detailedRef.current, {
				duration: 0.3,
				autoAlpha: 0,
				height: 0,
			})
			.to(detailedRef.current, {
				duration: 0.3,
				height: 0,
			})
			.play()
			.eventCallback('onComplete', () => {
				setDetailOnDisplay(false)
			})
	}

	const issueLabel = (title: string) => {
		return (
			<button
				onClick={() => {
					if (displayData.htmlURL) {
						window.open(displayData.htmlURL)
					} else if (onRequestFailed) {
						onRequestFailed('Request failed, GitHub API rate limit exceeded or lost connection with GitHub server')
					}
				}}
				style={{
					border: 'none',
					backgroundColor: 'white',
					fontSize: '14px',
					padding: '3px',
					marginRight: '10px',
					marginLeft: '5px',
					borderRadius: '5px',
					color: '#707070',
					fontWeight: 'bold',
				}}
			>
				{title}
			</button>
		)
	}

	const displayBtn = () => {
		return (
			<>
				<Button
					className={'issue-card-btn on-display'}
					variant={'outline-light'}
					onClick={detailBtn ? detailOffShow : detailOnShow}
				>
					{detailBtn? <UpOutlined style={{fontSize: '14px'}}/> : <DownOutlined style={{fontSize: '14px'}}/>}
				</Button>
				<div style={{
					fontWeight: 'bold',
					marginRight: '10px',
				}}>
					{detailBtn ? 'Hide Details': 'Show Details'}
				</div>
			</>
		)
	}

	const details = () => {
		if (detailOnDisplay) {
			return (
				<>
					<Row>
						<Col style={{
							backgroundColor: 'rgba(255, 255, 255, 0.5)',
							margin: '15px',
							marginTop: '0px',
							borderRadius: '10px',
							padding: '10px',
							minWidth: '50%',
							color: '#373f49',
						}}>
							<ReactMarkdown
								children={displayData.body}
								remarkPlugins={[remarkGfm, remarkGemoji]}
								className={'markdown'}
							/>
						</Col>
					</Row>
					<Row style={{
						paddingBottom: '10px',
					}}>
						<Col>
							<div style={{
								display: 'flex',
								flexDirection: 'row-reverse',
								justifyContent: 'flex-start',
								alignItems: 'center',
							}}>
								{displayData.isClosed ? <GFIIssueStatusTag type={'Closed'} /> : <GFIIssueStatusTag type={'Open'} />}
								{displayData.hasResolved ? <GFIIssueStatusTag type={'Resolved'} /> : <></>}
							</div>
						</Col>
					</Row>
				</>
			)
		} else {
			return <></>
		}
	}

	const cardClicked = (e: React.MouseEvent<HTMLTextAreaElement | HTMLDivElement>) => {
		if (!detailBtn) {
			detailOnShow()
		}
	}

	return (
		<Container
			className={'rounded-container'}
			style={{
				margin: '10px',
				backgroundColor: 'transparent',
				fontFamily: defaultFontFamily,
				cursor: detailBtn ? 'default' : 'pointer',
			}}
			onClick={cardClicked}
		>
			<Row>
				<Col className={'issue-card-title'}>
					{issueLabel('#' + issueId)}
					<div>
						<ReactMarkdown
							children={displayData.title}
							remarkPlugins={[remarkGfm]}
							className={'issue-title'}
						/>
					</div>
				</Col>
			</Row>
			<div ref={detailedRef}>
				{details()}
			</div>
			<div style={{
				display: 'flex',
				flexDirection: 'row-reverse',
			}}>
				{displayBtn()}
			</div>
		</Container>
	)
})

interface GFIIssueStatusTag {
	type: 'Resolved' | 'Open' | 'Closed'
}

const GFIIssueStatusTag = (props: GFIIssueStatusTag) => {

	const {type} = props

	let status = 'open'
	if (type === 'Resolved') {
		status = 'resolved'
	} else if (type === 'Closed') {
		status = 'closed'
	}

	return (
		<>
			<div className={`status-tag ${status}`}>
				{type}
			</div>
		</>
	)
}

interface GFIDadaKanban {
	onTagClicked: React.MouseEventHandler<HTMLButtonElement>
}

const GFIDadaKanban = forwardRef((props: GFIDadaKanban, ref) => {

	const {onTagClicked} = props

	let [repoNum, setRepoNum] = useState(0)
	let [issueNum, setIssueNum] = useState(0)
	let [GFINum, setGFINum] = useState(0)
	let [langTags, setLangTags] = useState<any[]>([])

	useEffect(() => {

		getRepoNum('').then((res) => {
			if (res && checkIsNumber(res)) {
				setRepoNum(res)
			}
		})

		getLanguageTags().then((res) => {
			if (res && Array.isArray(res)) {
				setLangTags(res)
			}
		})

		getIssueNum().then((res) => {
			if (res && checkIsNumber(res)) {
				setIssueNum(res)
				setGFINum(Math.round(res * 0.05))
			}
		})
	}, [])

	const renderLanguageTags = () => {
		return langTags.map((val, index) => {
			return (
				<button
					className={'gfi-rounded'}
					key={`lang-tag ${index}`}
					onClick={onTagClicked}
				>
					{val}
				</button>
			)
		})
	}

	return (
		<>
			<div className={'gfi-wrapper kanban'} style={{
				fontFamily: defaultFontFamily
			}}>
				<div className={'kanban wrapper'} style={{
					margin: '7px',
				}}>

					<div className={'kanban'}>
						<div className={'kanban data'}>
							<div> Repos </div>
							<div> {repoNum} </div>
						</div>
					</div>

					<div className={'kanban'}>
						<div className={'kanban data'}>
							<div> Issues </div>
							<div> {issueNum} </div>
						</div>
					</div>

					<div className={'kanban'}>
						<div className={'kanban data'}>
							<div> GFIs </div>
							<div> {GFINum} </div>
						</div>
					</div>
				</div>

				<div className={'gfi-wrapper tags'}>
					<div>
						Languages
					</div>
					<div className={'tags wrapper'}>
						{renderLanguageTags()}
					</div>
				</div>
			</div>
		</>
	)
})
