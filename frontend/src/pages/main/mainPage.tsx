import React, {forwardRef, useEffect, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {useIsMobile, useWindowSize} from '../app/windowContext';
import {useDispatch, useSelector} from 'react-redux';

import {Container, Col, Row} from 'react-bootstrap';

import '../../style/gfiStyle.css'
import {checkIsNumber, defaultFontFamily} from '../../utils';

import {GFINotiToast} from '../login/GFILoginComponents';
import {GFIAlarm, GFICopyright, GFIPagination} from '../GFIComponents';
import {getRepoNum, getIssueNum, getLanguageTags, searchRepoInfoByNameOrURL, getPagedRepoDetailedInfo} from '../../api/api';
import {checkGithubLogin} from '../../api/githubApi';

import {checkIsGitRepoURL} from '../../utils';
import {createGlobalProgressBarAction, createLogoutAction, createPopoverAction} from '../../module/storage/reducers';
import {GFI_REPO_FILTER_NONE, GFIMainPageHeader} from './mainHeader';

import {GFIIssueMonitor, GFIRepoDisplayView, GFIRepoStaticsDemonstrator} from './GFIRepoDisplayView';
import {GFIRepoInfo} from '../../module/data/dataModel';
import {GFIRootReducers} from '../../module/storage/configureStorage';

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
	let [alarmConfig, setAlarmConfig] = useState({ show: false, msg: '' })

	const showAlarm = (msg: string) => {
		setAlarmConfig({ show: true, msg: msg })
	}

	interface LocationStateLoginType {
		state: {
			justLogin: boolean
		}
	}

	const location = useLocation() as LocationStateLoginType

	useEffect(() => {
		fetchRepoInfoList(1)
		getRepoNum(selectedTag).then((res) => {
			if (res && Number.isInteger(res)) {
				setTotalRepos(res)
			}
		})

		if ('state' in location && location.state && location.state.justLogin) {
			setShowLoginMsg(true)
		}
	}, [])

	const repoCapacity = 5
	let [pageIdx, setPageIdx] = useState(1)
	let [totalRepos, setTotalRepos] = useState(0)
	let [selectedTag, setSelectedTag] = useState<string>()
	let [selectedFilter, setSelectedFilter] = useState<string>()
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

	useEffect(() => {
		fetchRepoInfoList(1, selectedTag, selectedFilter)
	}, [selectedTag, selectedFilter])

	useEffect(() => {
		fetchRepoInfoList(pageIdx, selectedTag, selectedFilter)
	}, [pageIdx])

	const fetchRepoInfoList = (pageNum: number, tag?: string, filter?: string) => {
		let beginIdx = (pageNum - 1) * repoCapacity
		dispatch(createGlobalProgressBarAction({hidden: false}))
		getRepoNum(selectedTag).then((res) => {
			if (res && Number.isInteger(res)) {
				setTotalRepos(res)
			}
		})
		getPagedRepoDetailedInfo(beginIdx, repoCapacity, tag, filter).then((repoList) => {
			if (repoList && Array.isArray(repoList)) {
				const repoInfoList = repoList.map((repo, i) => {
					if ('name' in repo && 'owner' in repo) {
						return {
							name: repo.name,
							owner: repo.owner,
							description: 'description' in repo ? repo.description: undefined,
							topics: 'topics' in repo ? repo.topics : undefined,
							url: '',
						}
					} else {
						return emptyRepoInfo
					}
				})
				setDisplayRepoInfo(repoInfoList)
				dispatch(createGlobalProgressBarAction({hidden: true}))
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

	const handleSearchBtn = (s: string) => {
		let repoURL: string | undefined = s
		let repoName
		if (checkIsGitRepoURL(s)) {
			repoURL = undefined
			repoName = s
		}
		dispatch(createGlobalProgressBarAction({hidden: false}))
		searchRepoInfoByNameOrURL(repoName, repoURL).then((res) => {
			if (res) {
				setTotalRepos(1)
				setDisplayRepoInfo([res])
				setShowSearchMsg(true)
			} else {
				showAlarm('This repository hasn\'t been added to our database yet. Please connect with its maintainers.')
			}
			dispatch(createGlobalProgressBarAction({hidden: true}))
		})
	}

	const renderInfoComponent = () => {
		if (displayRepoInfo && displayRepoInfo.length) {
			return displayRepoInfo.map((item, _) => {
				return (
					<GFIRepoDisplayView
						key={`repo-display-main-${item.name}-${item.owner}`}
						repoInfo={item}
						tags={['GFI', 'Repo Data']}
						panels={[
							<GFIIssueMonitor repoInfo={item} />,
							<GFIRepoStaticsDemonstrator repoInfo={item} />
						]}
						style={{
							border: '1px solid var(--color-border-default)',
							borderRadius: '7px',
							marginBottom: '1rem',
						}}
					/>
				)
			})
		}
		return <></>
	}

	const renderMainArea = () => {
		return (
			<>
				<Row>
					<Col className={'flex-row align-items-start justify-content-start'}>
						<Container className={'flex-col'} style={{
							padding: '0px',
							marginLeft: '0px',
							width: isMobile ? '100%' : '60%',
						}}>
							{renderInfoComponent()}
							<GFIPagination
								pageIdx={pageIdx}
								toPage={(pageNum) => {
									toPage(pageNum)
								}}
								pageNums={pageNums()}
								onFormInput={(target) => {
									const t = target as HTMLTextAreaElement
									setPageFormInput(t.value)
								}}
								onPageBtnClicked={() => {
									onPageBtnClicked()
								}}
								maxPagingCount={3}
								needInputArea={true}
							/>
						</Container>
						{isMobile ? <Container style={{
							maxWidth: '30%',
						}}>
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
					marginBottom: alarmConfig.show? '-15px': '0',
					marginTop: alarmConfig.show? '15px': '0',
				}}>
					{alarmConfig.show ?
						<GFIAlarm
							title={alarmConfig.msg}
							onClose={() => {setAlarmConfig({show: false, msg: alarmConfig.msg})}}
						/> : <></>}
				</Row>
				<Row>
					<Col>
						<Container style={{
							padding: '0px',
							marginLeft: '0px',
							maxWidth: isMobile ? '100%' : '60%',
						}}>
							<GFIMainPageHeader
								onSearch={(s) => {
									handleSearchBtn(s)
								}}
								onTagSelected={(s) => {
									if (s !== selectedTag) {
										setSelectedTag(s !== GFI_REPO_FILTER_NONE ? s: undefined)
									}
								}}
								onFilterSelect={(s) => {
									if (s !== selectedFilter) {
										let str = s as string
										setSelectedFilter(str !== GFI_REPO_FILTER_NONE ? s: undefined)
									}
								}}
							/>
						</Container>
					</Col>
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
			if (res) {
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
