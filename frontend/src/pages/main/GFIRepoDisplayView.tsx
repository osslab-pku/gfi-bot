import React, {forwardRef, MouseEventHandler, ReactElement, ReactNode, useEffect, useRef, useState} from 'react';
import {Row, Col} from 'react-bootstrap';

import '../../style/gfiStyle.css'
import {GFIRepoInfo} from '../../module/data/dataModel';
import {getIssueByRepoInfo} from '../../api/githubApi';
import remarkGfm from 'remark-gfm';
import remarkGemoji from 'remark-gemoji';
import ReactMarkdown from 'react-markdown';
import {GFIOverlay} from '../gfiComponents';
import {useDispatch, useSelector} from 'react-redux';
import {GFIRootReducers} from '../../module/storage/configureStorage';
import {createPopoverAction} from '../../module/storage/reducers';
import {getGFIByRepoName} from '../../api/api';

export interface RepoShouldDisplayPopoverState {
	shouldDisplayPopover?: boolean,
	popoverComponent?: ReactElement,
}
type RepoDisplayChildClickedCallback = (p?: RepoShouldDisplayPopoverState) => void
type RepoDisplayPanelBasicProp = {panelCallback?: RepoDisplayChildClickedCallback}

export interface GFIRepoDisplayView {
	repoInfo: GFIRepoInfo,
	tags?: string[],
	panels?: ReactElement<RepoDisplayPanelBasicProp>[],
	style?: any,
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

	useEffect(() => {
		if (tags) {
			setSelectedTagList(tags.map((_, i) => {
				return !i;
			}))
			setSelectedTag(0)
		}
	}, [tags])

	const Info = () => {
		if (panels && tags && panels.length === tags.length) {
			return (
				panels.map((node, i) => {
					return (
						<div
							className={'flex-col'}
							style={i === selectedTag ? {} : {display: 'none'}}
						>
							{node}
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
	    return (
		    <GFIOverlay
			    id={'main-overlay'}
			    direction={'right'}
			    width={'60%'}
			    hidden={hidden}
			    ref={overlayRef}
			    callback={() => {
					dispatch(createPopoverAction())
			    }}
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

export interface GFIIssueMonitor extends RepoDisplayPanelBasicProp {
	repoInfo: GFIRepoInfo,
	issueList?: number[],
}

export const GFIIssueMonitor = forwardRef((props: GFIIssueMonitor, ref) => {

	const {repoInfo, issueList, panelCallback} = props
	const [displayIssueList, setDisplayIssueList] = useState<number[] | undefined>(issueList)

	useEffect(() => {
		console.log(displayIssueList, repoInfo)
		if (!displayIssueList) {
			getGFIByRepoName(repoInfo.name).then((res) => {
				console.log(res)
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
					panelCallback={panelCallback}
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

export interface GFIIssueListItem extends RepoDisplayPanelBasicProp {
	repoInfo: GFIRepoInfo,
	issue: number,
}

const GFIIssueListItem = (props: GFIIssueListItem) => {

	const dispatch = useDispatch()

	const {repoInfo, issue} = props
	type IssueState = 'closed' | 'open' | 'resolved'
	type IssueDisplayData = {
		issueId: number,
		title: string,
		body: string,
		state: IssueState,
		url: string,
	}
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

	const overlayItem = () => {
		return (
			<div className={'flex-col repo-overlay-item'} style={{
				margin: '1rem 1.5rem',
			}}>
				<div className={'repo-display-info-title flex-row'}>
					<p> {repoInfo.owner} </p>
					<p> {' / '} </p>
					<p> {repoInfo.name} </p>
				</div>
				<div> {repoInfo?.description} </div>
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

	const onDetailShow: MouseEventHandler<HTMLDivElement> = (e) => {
		const callbackProp: RepoShouldDisplayPopoverState = {
			shouldDisplayPopover: true,
			popoverComponent: overlayItem()
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