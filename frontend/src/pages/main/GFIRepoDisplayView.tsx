import React, {
	createContext,
	forwardRef,
	MouseEventHandler,
	ReactElement,
	useContext,
	useEffect,
	useRef,
	useState
} from 'react';
import {Row, Col} from 'react-bootstrap';
import {useDispatch, useSelector} from 'react-redux';

import remarkGfm from 'remark-gfm';
import remarkGemoji from 'remark-gemoji';
import ReactMarkdown from 'react-markdown';

import '../../style/gfiStyle.css'
import {GFIOverlay, GFISimplePagination} from '../GFIComponents';
import {GFIRepoInfo} from '../../module/data/dataModel';
import {getIssueByRepoInfo} from '../../api/githubApi';
import {GFIRootReducers} from '../../module/storage/configureStorage';
import {createPopoverAction} from '../../module/storage/reducers';
import {getGFIByRepoName, getRepoDetailedInfoByName} from '../../api/api';
import {useIsMobile} from '../app/windowContext';
import {RepoGraphContainer} from '../repositories/repoDataDemonstrator';
import {GetRepoDetailedInfo} from '../../module/data/dataModel';

export interface RepoShouldDisplayPopoverState {
	shouldDisplayPopover?: boolean,
	popoverComponent?: ReactElement,
	popoverID?: string,
}

export interface GFIRepoBasicProp {
	repoInfo: GFIRepoInfo,
}

export interface GFIRepoDisplayView extends GFIRepoBasicProp {
	tags?: string[],
	panels?: ReactElement[],
	style?: any,
}

const RepoDisplayOverlayIDContext = createContext<string>({} as any)

const RepoDisplayOverlayIDProvider: React.FC<{children: React.ReactNode, id: string}> = ({children, id}) => {
	return (
		<RepoDisplayOverlayIDContext.Provider value={id}>
			{children}
		</RepoDisplayOverlayIDContext.Provider>
	)
}

const useOverlayID = () => {
	return useContext(RepoDisplayOverlayIDContext)
}

export const GFIRepoDisplayView = forwardRef((props: GFIRepoDisplayView, ref) => {

	const {repoInfo, tags, panels, style} = props

	const [selectedTag, setSelectedTag] = useState<number>(0)
	const [selectedTagList, setSelectedTagList] = useState<boolean[]>()

	// Not good, but 'position: fixed' in child components doesn't work here
	// wondering why...
	const overlayItem = useSelector<GFIRootReducers, RepoShouldDisplayPopoverState | undefined>(state => {
		return state.mainPopoverReducer
	})
	const overlayRef = useRef<HTMLDivElement>(null)
	const dispatch = useDispatch()
	const overlayID = `main-overlay-${repoInfo.name}-${repoInfo.owner}`

	const isMobile = useIsMobile()

	useEffect(() => {
		if (tags) {
			setSelectedTagList(tags.map((_, i) => {
				return !i;
			}))
		}
	}, [])

	const Info = () => {
		if (panels && tags && panels.length === tags.length) {
			return (
				panels.map((node, i) => {
					return (
						<div
							className={'flex-col'}
							style={i === selectedTag ? {} : {display: 'none'}}
						>
							<RepoDisplayOverlayIDProvider id={overlayID}>
								{node}
							</RepoDisplayOverlayIDProvider>
						</div>
					)
				})
			)
		} else {
			return <></>
		}
	}

	const Title = () => {

		const ProjectTags = () => {
			return repoInfo.topics?.map((item, i) => {
				return (
					<div className={'repo-display-info-repo-tag'}>
						{item}
					</div>
				)
			})
		}

		return (
			<div className={'flex-col justify-content-center repo-display-info'}>
				<div className={'repo-display-info-title flex-row'}>
					<p> {repoInfo.owner} </p>
					<p> {' / '} </p>
					<p> {repoInfo.name} </p>
				</div>
				<div> {repoInfo?.description} </div>
				<div className={'flex-row flex-wrap'}> {ProjectTags()} </div>
			</div>
		)
	}

	const Tags = () => {
		if (tags && selectedTagList?.length === tags.length) {
			return tags.map((item, i) => {
				return (
					<PanelTag
						name={item}
						id={i}
						onClick={(id) => {
							if (id !== selectedTag) {
								setSelectedTag(id)
								setSelectedTagList(tags?.map((_, i) => {
									return i === id
								}))
							}
						}}
						selected={selectedTagList[i]}
					/>
				)
			})
		} else {
			return <></>
		}
	}

	const renderOverlay = () => {
		let hidden = !(overlayItem && overlayItem.shouldDisplayPopover)
		if (overlayItem?.popoverID !== overlayID) {
			hidden = true
		}
	    return (
		    <GFIOverlay
			    id={overlayID}
			    direction={'right'}
			    width={isMobile ? '90%': '60%'}
			    hidden={hidden}
			    ref={overlayRef}
			    callback={() => {
					dispatch(createPopoverAction())
			    }}
			    animation={true}
		    >
			    {overlayItem?.popoverComponent}
		    </GFIOverlay>
	    )
	}

	return (
		<>
			{renderOverlay()}
			<div style={style} className={'flex-col repo-display'}>
				<div className={'flex-row repo-display-info-nav'}>
					{Tags()}
				</div>
				<Row>
					<Col>
						{Title()}
						{Info()}
					</Col>
				</Row>
			</div>
		</>
	)
})

const PanelTag = (props: {name: string, id: number, selected: boolean, onClick: (id: number) => void}) => {

	const {name, id, selected, onClick} = props
	const selectedClass = selected ? 'selected' : ''
	const first = id === 0 ? 'first' : ''
	const className = 'repo-display-info-panel-tag flex-row align-items-stretch align-center'
		+ ` ${selectedClass}` + ` ${first}`

	return (
		<div className={className}>
			<div
				className={'repo-display-info-tag flex-row flex-center hoverable' + ` ${selectedClass}`}
				onClick={() => {onClick(id)}}
			> <p className={'no-select'}> {name} </p>
			</div>
		</div>
	)
}

export interface GFIIssueMonitor extends GFIRepoBasicProp {
	issueList?: number[],
}

export const GFIIssueMonitor = forwardRef((props: GFIIssueMonitor, ref) => {

	const {repoInfo, issueList} = props
	const [displayIssueList, setDisplayIssueList] = useState<number[] | undefined>(issueList)

	useEffect(() => {
		if (!displayIssueList) {
			getGFIByRepoName(repoInfo.name).then((res) => {
				if (Array.isArray(res) && res.length) {
					setDisplayIssueList(res)
				} else {
					setDisplayIssueList(undefined)
				}
			})
		}
	}, [repoInfo])

	const render = () => {
		return displayIssueList?.map((issue, i) => {
			return (
				<GFIIssueListItem
					repoInfo={repoInfo}
					issue={issue}
					key={`gfi-issue-${repoInfo.name}-${issue}-${i}`}
				/>
			)
		})
	}

	return (
		<div className={'flex-col'}>
			{render()}
		</div>
	)
})

export interface GFIIssueListItem extends GFIRepoBasicProp {
	issue: number,
}

type IssueState = 'closed' | 'open' | 'resolved'
interface IssueDisplayData {
	issueId: number,
	title: string,
	body: string,
	state: IssueState,
	url: string,
}

const GFIIssueListItem = (props: GFIIssueListItem) => {

	const dispatch = useDispatch()
	const overlayID = useOverlayID()
	const {repoInfo, issue} = props
	const [displayData, setDisplayData] = useState<IssueDisplayData>()

	useEffect(() => {
		getIssueByRepoInfo(repoInfo.name, repoInfo.owner, issue).then((res) => {
			if (res.code === 200) {
				if ('number' in res.result && 'title' in res.result && 'state' in res.result
					&& 'active_lock_reason' in res.result && 'body' in res.result && 'html_url' in res.result) {
					let issueState = 'open'
					if (res.result.state === 'closed') {
						issueState = 'closed'
					}
					if (res.result.active_lock_reason === 'resolved') {
						issueState = 'resolved'
					}
					setDisplayData({
						issueId: res.result.number,
						title: res.result.title,
						body: res.result.body,
						state: issueState as IssueState,
						url: res.result.html_url,
					})
				}
			} else {

			}
		})
	}, [])

	const issueBtn = () => {
		return (
			<button
				className={`issue-display-item-btn ${displayData ? displayData.state: ''}`}
			>
				<a href={displayData ? displayData.url: ''}>
					{`#${issue}`}
				</a>
			</button>
		)
	}

	const onDetailShow: MouseEventHandler<HTMLDivElement> = (e) => {
		const callbackProp: RepoShouldDisplayPopoverState = {
			shouldDisplayPopover: true,
			popoverComponent: <IssueOverlayItem repoInfo={repoInfo}  issueBtn={issueBtn} displayData={displayData} />,
			popoverID: overlayID,
		}
		dispatch(createPopoverAction(callbackProp))
	}

	return (
		<>
			<div
				className={'issue-display-item flex-row align-center hoverable'}
				onClick={onDetailShow}
			>
				<div style={{
					width: '9%',
					minWidth: '70px',
				}}>
					{issueBtn()}
				</div>

				<div className={'flex-row flex-wrap text-break'}>
					{displayData ? displayData.title : ''}
				</div>
			</div>
		</>
	)
}

interface IssueOverlayItem extends GFIRepoBasicProp {
	issueBtn: () => ReactElement,
	displayData?: IssueDisplayData,
}

const IssueOverlayItem = (props: IssueOverlayItem) => {

	const {repoInfo, issueBtn, displayData} = props
	const isMobile = useIsMobile()
	const flexDirection = isMobile ? 'col': 'row'

	return (
		<div className={'flex-col repo-overlay-item'} style={{
			margin: '1rem 1.5rem',
		}}>
			<div className={`repo-display-info-title flex-${flexDirection}`}>
				<p> {repoInfo.owner} </p>
				{ !isMobile && <p> {' / '} </p> }
				<p style={{ margin: '0' }}> {repoInfo.name} </p>
			</div>
			<div style={{ fontFamily: 'var(--default-font-family)' }}>
				{repoInfo?.description}
			</div>
			<div className={'flex-row align-center'} style={{
				fontWeight: 'bold',
				fontSize: 'larger',
				margin: '1rem 0',
			}}>
				{issueBtn()}
				<div style={{
					marginLeft: '0.7rem',
				}}>
					{displayData?.title}
				</div>
			</div>
			<ReactMarkdown
				children={displayData ? displayData.body : ''}
				remarkPlugins={[remarkGfm, remarkGemoji]}
				className={'markdown'}
			/>
		</div>
	)
}

export interface GFIRepoStaticsDemonstrator extends GFIRepoBasicProp {}

export const GFIRepoStaticsDemonstrator = forwardRef((props: GFIRepoStaticsDemonstrator, ref) => {

	const {repoInfo} = props
	const [displayInfo, setDisplayInfo] = useState<GetRepoDetailedInfo>()

	type DataTag = 'monthly_stars' | 'monthly_commits' | 'monthly_issues' | 'monthly_pulls'
	type DisplayData = {[key in DataTag]?: any[]}
	const [displayData, setDisplayData] = useState<DisplayData>()
	const dataCategories = ['monthly_stars', 'monthly_commits', 'monthly_issues', 'monthly_pulls']
	const dataTitle = ['Monthly Stars', 'Monthly Commits', 'Monthly Issues', 'Monthly Pulls']

	const [selectedIdx, setSelectedIdx] = useState(0)

	useEffect(() => {
		getRepoDetailedInfoByName(repoInfo.name).then((res) => {
			const result = res as GetRepoDetailedInfo
			setDisplayInfo(result)
		})
	}, [])

	useEffect(() => {
		if (displayInfo) {
			let info: DisplayData = {}
			let key: keyof typeof displayInfo
			for (key in displayInfo) {
				if (dataCategories.includes(key)) {
					info[key as DataTag] = displayInfo[key] as any[]
				}
			}
			setDisplayData(info)
		}
	}, [displayInfo])

	const RenderGraphs = () => {
	    return dataCategories.map((item, idx) => {
		    if (displayData && Object.keys(displayData).includes(item)) {
			    return (
					<div style={idx === selectedIdx ? {}: {display: 'none'}}>
						<RepoGraphContainer
							title={dataTitle[idx]}
							info={displayData[item as DataTag]}
						/>
					</div>
			    )
		    } else {
				return <></>
		    }
	    })
	}

	return (
		<div className={'issue-demo-container'}>
			{RenderGraphs()}
			<div className={'flex-row page-footer-container'}>
				<GFISimplePagination
					nums={displayData ? Object.keys(displayData).length: 1}
					onClick={(idx) => {
						setSelectedIdx(idx)
					}}
					title={dataTitle}
				/>
			</div>
		</div>
	)
})
