import React, {forwardRef, Key, useEffect, useRef, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {useIsMobile, useWindowSize} from '../app/windowContext';
import {useDispatch, useSelector} from 'react-redux';

import {Container, Col, Row, Form, InputGroup, Button} from 'react-bootstrap';
import {gsap} from 'gsap';
import {ReloadOutlined, UpOutlined, DownOutlined} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkGemoji from 'remark-gemoji';

import gfiLogo from '../../assets/gfi-logo.png';

import '../../style/gfiStyle.css'
import {checkIsNumber, defaultFontFamily} from '../../utils';

import {GFINotiToast} from '../login/welcomePage';
import {GFIAlarm, GFICopyright, GFIPagination} from '../gfiComponents';
import {
	getRecommendedRepoInfo,
	getGFIByRepoName,
	getRepoNum,
	getIssueNum,
	getLanguageTags,
	getRepoInfoByNameOrURL, getRepoDetailedInfo, getProcessingSearches
} from '../../api/api';
import {checkGithubLogin, getIssueByRepoInfo, userInfo} from '../../api/githubApi';
import type {LoginState} from '../../module/storage/reducers';

import {checkIsGitRepoURL} from '../../utils';
import {useSucceedQuery} from '../app/processStatusProvider';
import {createLogoutAction, createPopoverAction} from '../../module/storage/reducers';
import {GFIMainPageHeader} from './mainHeader';

import {GFIIssueDisplayView} from './GFIIssueDisplayView';
import {GFIIssueMonitor, GFIRepoDisplayView} from './GFIRepoDisplayView';
import {GFIRepoInfo} from '../../module/data/dataModel';
import {GFIRootReducers, store} from '../../module/storage/configureStorage';

// TODO: MSKYurina
// Animation & Searching History

export const MainPage = () => {

	const dispatch = useDispatch()
	useEffect(() => {
		checkGithubLogin().then((res) => {
			if (!res) {
				dispatch(createLogoutAction())
			}
		})
		dispatch(createPopoverAction())
	}, [])

	let [showLoginMsg, setShowLoginMsg] = useState(false)
	let [showSearchMsg, setShowSearchMsg] = useState(false)

	const succeedQuery = useSucceedQuery()
	useEffect(() => {
		checkGithubLogin().then((res) => {

		})
	}, [succeedQuery])

	const isMobile = useIsMobile()
	const {width, height} = useWindowSize()

	const userName = useSelector((state: GFIRootReducers) => {
		return state.loginReducer?.name
	})

	const userAvatarUrl = useSelector((state: GFIRootReducers) => {
		return state.loginReducer?.avatar
	})

	const emptyRepoInfo: GFIRepoInfo = {
		name: '',
		owner: '',
		description: '',
		url: '',
		topics: [],
	}

	let [displayRepoInfo, setDisplayRepoInfo] = useState<GFIRepoInfo[] | undefined>([emptyRepoInfo])

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

	interface LocationStateLoginType {
		state: {
			justLogin: boolean
		}
	}

	const location = useLocation() as LocationStateLoginType

	useEffect(() => {
		fetchRepoInfoList(1)
		getRepoNum().then((res) => {
			if (res && Number.isInteger(res)) {
				setTotalRepos(res)
			}
		})

		if ('state' in location && location.state && location.state.justLogin) {
			setShowLoginMsg(true)
		}
	}, [])

	const repoCapacity = 4
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
		setDisplayRepoInfo([])
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
					if ('name' in parsedRepo && 'owner' in parsedRepo) {
						return {
							name: parsedRepo.name,
							owner: parsedRepo.owner,
							description: 'description' in parsedRepo ? parsedRepo.description: undefined,
							topics: 'topics' in parsedRepo ? parsedRepo.topics : undefined,
							url: '',
						}
					} else {
						return emptyRepoInfo
					}
				})
				setDisplayRepoInfo(repoInfoList)
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

	let [searchURL, setSearchURL] = useState('')
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
			// if (repoInfo !== searchedRepoInfo) {
			// 	setSearchedRepoInfo(repoInfo)
			// }
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
		}
	}

	const renderInfoComponent = () => {
		if (displayRepoInfo && displayRepoInfo.length) {
			return displayRepoInfo.map((item, _) => {
				return (
					<GFIRepoDisplayView
						repoInfo={item}
						tags={['GFI']}
						panels={[<GFIIssueMonitor repoInfo={item} />]}
						style={{
							border: '1px solid var(--color-border-default)',
							borderRadius: '7px',
							marginBottom: '1rem',
						}}
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
					<Col className={'flex-row align-items-start justify-content-start'}>
						<Container className={'flex-col'} style={{
							padding: '0px',
							marginLeft: '0px',
							maxWidth: isMobile ? '100%' : '60%',
						}}>
							{renderInfoComponent()}
							<GFIPagination
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
						</Container>
						{(width > 1000) ? <Container style={{
							maxWidth: '30%',
						}}>
							{/*<GFIDadaKanban onTagClicked={onKanbanClicked} />*/}
						</Container> : <></>}
					</Col>
				</Row>
			</>
		)
	}

	return (
		<>
			<GFIMainPageHeader />
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
					color: 'black',
					bottom: '0',
				}}>
					<GFICopyright />
				</Row>
			</Container>
			<Container style={{
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
