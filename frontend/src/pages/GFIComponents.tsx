import { Container, Col, Row, Form, Pagination, Alert } from 'react-bootstrap'
import React, {
	ChangeEvent,
	createRef,
	forwardRef,
	MutableRefObject,
	useEffect,
	useRef,
	useState,
} from 'react'
import { checkIsNumber, checkIsPercentage, defaultFontFamily } from '../utils'
import { gsap } from 'gsap'

import '../style/gfiStyle.css'
import { Variant as AlarmPanelVariants } from 'react-bootstrap/types'

export const GFICopyright = () => {
	const copyright =
		'Copyright © 2021 OSS Lab, Peking University. All rights reserved.'

	return (
		<Container
			style={{
				paddingTop: '20px',
				paddingBottom: '10px',
				fontFamily: defaultFontFamily,
				fontSize: '15px',
				fontWeight: '100',
				position: 'sticky',
				top: '100vh',
			}}
		>
			<Row>
				<Col style={{ textAlign: 'center' }}>{copyright}</Col>
			</Row>
		</Container>
	)
}

export interface GFIPaginationProps {
	maxPagingCount: number
	pageNums: number
	pageIdx: number
	onPageBtnClicked?: () => void
	toPage: (page: number) => void
	needInputArea?: boolean
	onFormInput?: (target: EventTarget) => void
	needPadding?: boolean
	className?: string
}

export const GFIPagination = (props: GFIPaginationProps) => {
	const maxPagingCount = props.maxPagingCount

	const toFirstPage = () => {
		props.toPage(1)
	}

	const toPrevPage = () => {
		if (props.pageIdx === 1) {
			toFirstPage()
		} else {
			props.toPage(props.pageIdx - 1)
		}
	}

	const toLastPage = () => {
		props.toPage(props.pageNums)
	}

	const toNextPage = () => {
		if (props.pageIdx === props.pageNums) {
			return
		}
		if (props.pageIdx === props.pageNums - 1) {
			toLastPage()
		} else {
			props.toPage(props.pageIdx + 1)
		}
	}

	const calRenderRange = (pageNums: number, selectedIdx: number) => {
		let pageArray: number[] = Array()
		let idx = Math.max(selectedIdx - maxPagingCount + 2, 1)
		for (let i = 0; i < maxPagingCount; i++, idx++) {
			pageArray.push(idx)
			if (idx + 1 > pageNums) {
				break
			}
		}
		return pageArray
	}

	const renderPagingItem = (pageNums: number, selectedIdx: number) => {
		let pageArray = calRenderRange(pageNums, selectedIdx)
		let renderedArray = pageArray.map((ele, idx) => {
			return (
				<Pagination.Item
					key={ele}
					active={ele === selectedIdx}
					onClick={() => props.toPage(ele)}
				>
					{' '}
					{ele}{' '}
				</Pagination.Item>
			)
		})

		if (!pageArray.includes(1)) {
			let showDot: boolean = !pageArray.includes(2)
			renderedArray.unshift(renderExpPagingItem(1, showDot))
		}
		if (!pageArray.includes(pageNums) && pageNums) {
			let showDot: boolean = !pageArray.includes(pageNums - 1)
			renderedArray.push(renderExpPagingItem(pageNums, showDot))
		}

		return renderedArray
	}

	const renderExpPagingItem = (pageNum: number, shotDot: boolean) => {
		let msg: string = pageNum.toString()
		if (shotDot) {
			msg = '.. ' + pageNum
		}
		return (
			<Pagination.Item
				key={pageNum}
				onClick={() => props.toPage(pageNum)}
			>
				{' '}
				{msg}{' '}
			</Pagination.Item>
		)
	}

	return (
		<Container
			style={
				props.needPadding
					? { overflow: 'hidden' }
					: { overflow: 'hidden', padding: '0' }
			}
			className={props.className}
		>
			<Row style={{ marginTop: '10px' }}>
				<Form.Group>
					<Col sm={8} style={{ float: 'left' }}>
						<Pagination style={{ margin: '0 auto' }}>
							<Pagination.Prev
								onClick={() => {
									toPrevPage()
								}}
							/>
							{renderPagingItem(props.pageNums, props.pageIdx)}
							<Pagination.Next
								onClick={() => {
									toNextPage()
								}}
							/>
						</Pagination>
					</Col>
					{props.needInputArea && (
						<Col sm={4} style={{ float: 'right' }}>
							<Form.Label
								style={{
									maxWidth: '80px',
									float: 'right',
								}}
							>
								<Form.Control
									placeholder={
										props.pageIdx + '/' + props.pageNums
									}
									onChange={(
										e: ChangeEvent<HTMLInputElement>
									) => {
										props.onFormInput &&
											props.onFormInput(e.target)
									}}
									onKeyDown={(e) => {
										if (
											e.key === 'Enter' &&
											props.onPageBtnClicked
										) {
											e.preventDefault()
											props.onPageBtnClicked()
										}
									}}
								/>
							</Form.Label>
						</Col>
					)}
				</Form.Group>
			</Row>
		</Container>
	)
}

export type GFIAlarmPanelVariants = AlarmPanelVariants
export interface GFIAlarmProps {
	onClose?: () => void
	title?: string
	variant?: AlarmPanelVariants
}

export class GFIAlarm extends React.Component<GFIAlarmProps> {
	private readonly selfRef: React.RefObject<any>

	constructor(props: GFIAlarmProps) {
		super(props)
		this.selfRef = createRef()
	}

	componentDidMount() {
		let alarmTimeline = gsap.timeline()
		alarmTimeline
			.from(this.selfRef.current, {
				duration: 0.4,
				autoAlpha: 0,
				y: -25,
			})
			.play()
	}

	alarmOnClose = () => {
		let timeline = gsap.timeline()
		timeline
			.to(this.selfRef.current, {
				duration: 0.4,
				autoAlpha: 0,
				y: -25,
			})
			.eventCallback('onComplete', () => {
				if (this.props.onClose) {
					this.props.onClose()
				}
			})
			.play()
	}

	render() {
		const { title } = this.props
		return (
			<Alert
				variant={this.props.variant ? this.props.variant : 'danger'}
				dismissible={true}
				ref={this.selfRef}
				onClick={this.alarmOnClose}
				style={{
					borderRadius: '5px',
				}}
			>
				{title}
			</Alert>
		)
	}
}

export interface GFIProgressBarProps {
	barWidth: string | number
	height: string
	onFinished: () => void
}

interface GFIProgressBarStates {
	barWidth: any
}

export class GFIProgressBar extends React.Component<
	GFIProgressBarProps,
	GFIProgressBarStates
> {
	private readonly barRef: React.RefObject<any>

	constructor(props: GFIProgressBarProps) {
		super(props)
		this.barRef = React.createRef()
		this.state = {
			barWidth: '0%',
		}
	}

	checkValidWidth = (width: any) => {
		return (
			(checkIsNumber(width.slice(0, -1)) && width.slice(-1) === '%') ||
			checkIsNumber(width)
		)
	}

	componentDidUpdate(
		prevProps: GFIProgressBarProps,
		prevState: GFIProgressBarStates,
		snapshot: any
	) {
		const { barWidth, onFinished } = this.props
		if (
			this.checkValidWidth(barWidth) &&
			this.checkValidWidth(prevProps.barWidth)
		) {
			if (barWidth === prevProps.barWidth) {
				return
			}

			gsap.to(this.barRef.current, {
				duration: 0.2,
				width: barWidth,
				paused: true,
			})
				.eventCallback('onComplete', () => {
					this.setState({
						barWidth: barWidth,
					})
				})
				.play()

			if (barWidth === '100%' || barWidth === window.innerWidth) {
				gsap.to(this.barRef.current, {
					duration: 0.2,
					autoAlpha: 0,
				})
					.eventCallback('onComplete', () => {
						if (onFinished) {
							onFinished()
						}
					})
					.play()
			}
		}
	}

	render() {
		const { height } = this.props
		return (
			<div
				style={{
					backgroundColor: '#85a5ff',
					height: height,
					width: this.state.barWidth,
					borderRadius: '2px',
				}}
				ref={this.barRef}
			/>
		)
	}
}

export interface GFIOverlay {
	width?: string
	height?: string
	direction: 'left' | 'right' | 'top' | 'bottom'
	children?: React.ReactNode
	hidden?: boolean
	id: string
	callback?: () => void
	animation?: boolean
}

export const GFIOverlay = forwardRef<HTMLDivElement, GFIOverlay>(
	(props: GFIOverlay, ref) => {
		const selfRef = useRef<HTMLDivElement>(null)

		const {
			id,
			width,
			height,
			direction,
			children,
			hidden,
			callback,
			animation,
		} = props
		const hide = hidden ? 'hidden' : ''

		const resizeHandler = () => {
			if (animation && selfRef.current && direction === 'right') {
				selfRef.current.style.left = ''
			}
		}

		useEffect(() => {
			window.addEventListener('resize', resizeHandler)
			return () => {
				window.removeEventListener('resize', resizeHandler)
			}
		}, [])

		useEffect(() => {
			const currentRef = (ref as MutableRefObject<HTMLDivElement>).current
			if (currentRef && !hidden) {
				document
					.getElementsByTagName('html')[0]
					.classList.add('scrollbar-hidden')
				currentRef.style.display = 'block'

				// animation
				// currently only for direction = right
				if (
					animation &&
					selfRef.current &&
					direction === 'right' &&
					width &&
					checkIsPercentage(width)
				) {
					selfRef.current.style.left = '100%'
					currentRef.style.overflowX = 'hidden'
					gsap.to(selfRef.current, {
						duration: 0.4,
						left: `${100 - parseFloat(width)}%`,
						ease: 'power3.out',
					}).play()
				}
			} else if (currentRef) {
				currentRef.style.display = 'none'
			}
		}, [hidden, children])

		return (
			<div
				id={id}
				className={`full-overlay ${hide}`}
				ref={ref}
				onClick={(e) => {
					e.stopPropagation()
					if (ref) {
						document
							.getElementsByTagName('html')[0]
							.classList.remove('scrollbar-hidden')
						const currentRef = (
							ref as MutableRefObject<HTMLDivElement>
						).current
						if (currentRef) {
							currentRef.style.display = 'none'
						}
						if (callback) {
							callback()
						}
					}
				}}
			>
				<div
					className={`full-overlay-${direction}`}
					style={{
						width: width ? width : '100%',
						height: height ? height : '100%',
					}}
					onClick={(e) => e.stopPropagation()}
					ref={selfRef}
				>
					{children}
				</div>
			</div>
		)
	}
)

export const GFISimplePagination = (props: {
	nums: number
	onClick: (idx: number) => void
	title?: string[]
}) => {
	const { nums, onClick, title } = props
	const [selectedIdx, setSelectedIdx] = useState<number>(0)
	let showTitle = ''
	let shouldShowTitle = false
	if (title && title.length === nums) {
		showTitle = '-title'
		shouldShowTitle = true
	}

	const render = () => {
		const List = []
		for (let i = 0; i < nums; i++) {
			List.push(i)
		}
		return List.map((i, idx) => {
			const isSelected = idx === selectedIdx ? 'page-selected' : ''
			const idRandom = Math.random() * 1000
			return (
				<div
					key={`simple-pagination-item-${title}-${idx}-${idRandom}`}
					className={`simple-pagination-item${showTitle} ${isSelected} hoverable`}
					onClick={() => {
						if (idx !== selectedIdx) {
							setSelectedIdx(idx)
							onClick(idx)
						}
					}}
				>
					{shouldShowTitle && title && title[idx]}
				</div>
			)
		})
	}

	return (
		<div
			className={
				'simple-pagination flex-row align-center justify-content-between'
			}
		>
			{render()}
		</div>
	)
}
