import React, {forwardRef, MouseEventHandler, useEffect, useState} from 'react';
import {Container, Col, Form, Button, Dropdown} from 'react-bootstrap';
import {SearchOutlined} from '@ant-design/icons';

import './mainPage.css'
import '../../style/gfiStyle.css'
import {getLanguageTags} from '../../api/api';

export type GFIRepoSearchingFilterType = 'None' | 'Popularity' | 'Activity' | 'Recommended' | 'Time'
export const GFI_REPO_FILTER_NONE: GFIRepoSearchingFilterType & string = 'None'

export interface GFIMainPageHeader {
	onSearch?: (s: string) => void,
	onFilterSelect?: (s: GFIRepoSearchingFilterType) => void,
	onTagSelected?: (s: string) => void,
}

export const GFIMainPageHeader = forwardRef((props: GFIMainPageHeader, ref) => {

	const {onSearch, onFilterSelect, onTagSelected} = props

	const [search, setSearch] = useState<string | undefined>()
	const [filterSelected, setFilterSelected] = useState<GFIRepoSearchingFilterType>('None')

	const sortedBy: GFIRepoSearchingFilterType[] = [
		'None',
		'Popularity',
		'Activity',
		'Recommended',
		'Time',
	]

	const renderDropDownItem = (onClick: MouseEventHandler<HTMLElement>, title: string) => {
		return (
			<Dropdown.Item
				onClick={onClick}
				style={{
					fontSize: 'small',
				}}
			>
				{title}
			</Dropdown.Item>
		)
	}

	const renderDefaultDropDownItems = () => {
		return sortedBy.map((value, index, array) => {
			return (
				renderDropDownItem(
					(e)=> {
						setFilterSelected(value)
						if (onFilterSelect) {
							onFilterSelect(value)
						}
					},
					value as string
				)
			)
		})
	}

	const [tagArray, setTagArray] = useState<string[]>(['None'])
	const [tagSelected, setTagSelected] = useState('None')
	useEffect(() => {
		getLanguageTags().then((res) => {
			if (res) {
				setTagArray(['None', ...res])
			}
		})
	}, [])

	const renderTagMenu = () => {
		return tagArray.map((value, index, array) => {
			return renderDropDownItem(
				(e) => {
					setTagSelected(value)
					if (onTagSelected) {
						onTagSelected(value)
					}
				},
				value
			)
		})
	}

	return (
		<Container className={'main-header-container flex-wrap flex-col'}>
			<div className={'flex-row align-center full warp'} id={'main-header-container-wrapper'}>
				<Col className={'flex-row'} style={{ padding: '0' }}>
					<div className={'flex-col full wrap'}>
						<div className={'flex-row'}>
							<Form id={'main-header-input'}>
								<Form.Control
									className={'main-header-form'}
									placeholder={'GitHub URL or Repo Name'}
									aria-describedby={'append-icon'}
									onChange={(e) => {
										setSearch(e.target.value)
									}}
									onKeyDown={(e) => {
										if (e.key === 'Enter') {
											e.preventDefault()
											if (search && onSearch) {
												onSearch(search)
											}
										}
									}}
									id={'main-header-input-text'}
								>
								</Form.Control>
							</Form>
							<Button
								className={'flex-row flex-center'}
								onClick={() => {
									if (search && onSearch) {
										onSearch(search)
									}
								}}
								id={'main-header-search'}
							>
								<SearchOutlined />
							</Button>
						</div>
						<div className={'flex-row align-center'} style={{
							marginTop: '0.5rem',
						}}>
							<div className={'flex-row align-center'}>
								<div className={'main-dropdown-tags'}>
									Sorted By
								</div>
								<Dropdown style={{
									marginRight: '1rem',
								}}>
									<Dropdown.Toggle variant={'light'} className={'main-header-dropdown'}>
										{filterSelected}
									</Dropdown.Toggle>
									<Dropdown.Menu variant={'dark'} style={{
										minWidth: '7rem',
									}}>
										{renderDefaultDropDownItems()}
									</Dropdown.Menu>
								</Dropdown>
							</div>

							<div className={'flex-row align-center'}>
								<div className={'main-dropdown-tags'}>
									Tags
								</div>
								<Dropdown>
									<Dropdown.Toggle variant={'light'} className={'main-header-dropdown'}>
										{tagSelected}
									</Dropdown.Toggle>
									<Dropdown.Menu variant={'dark'} style={{
										minWidth: '7rem',
									}}>
										{renderTagMenu()}
									</Dropdown.Menu>
								</Dropdown>
							</div>
						</div>
					</div>
				</Col>
			</div>
		</Container>
	)
})
