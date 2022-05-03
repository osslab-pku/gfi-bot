import React, {useEffect, useState} from 'react';
import {Alert, Badge, Col, Container, ListGroup, Row} from 'react-bootstrap';
import '../../style/gfiStyle.css'

import {checkIsNumber} from '../../utils';
import {GFICopyright, GFIAlarm, GFIPagination, GFIProgressBar} from '../GFIComponents';
import {RepoGraphContainer} from './repoDataDemonstrator';

import {getRepoNum, getRepoDetailedInfo} from '../../api/api';
// @ts-ignore
import Fade from 'react-reveal/Fade'
import {useDispatch} from 'react-redux';
import {createAccountNavStateAction, createGlobalProgressBarAction} from '../../module/storage/reducers';

export const Repositories = () => {

    const repoListCapacity = 5

    let [pageIdx, setPageIdx] = useState<number>(1)

    let [totalRepos, setTotalRepos] = useState<number>(0)
    let [showAlarm, setShowAlarm] = useState<boolean>(false)

    const dispatch = useDispatch()
    useEffect(() => {
        dispatch(createAccountNavStateAction({ show: true }))
    }, [])

    useEffect(() => {
        getRepoNum().then((num) => {
            if (num && Number.isInteger(num)) {
                setTotalRepos(num)
            } else {
                setTotalRepos(0)
                setShowAlarm(true)
            }
        })
    }, [pageIdx])

    let [infoList, setInfoList] = useState<any[]>([])
    useEffect(() => {
        let beginIdx = (pageIdx - 1) * repoListCapacity
        dispatch(createGlobalProgressBarAction({ hidden: false }))
        dispatch(createAccountNavStateAction({ show: true }))
        getRepoDetailedInfo(beginIdx, repoListCapacity).then((repoList) => {
            if (repoList && Array.isArray(repoList)) {
                setInfoList(repoList)
            } else {
                setInfoList([])
                setShowAlarm(true)
            }
        }).then(() => {
            setActiveCardIdx(0)
            dispatch(createGlobalProgressBarAction({ hidden: true }))
        })
    }, [pageIdx])

    let [activeCardIdx, setActiveCardIdx] = useState<number>(0)
    let [pageFormInput, setPageFormInput] = useState<string>('0')

    const projectCardOnClick = (idx: number) => {
        setActiveCardIdx(idx)
    }

    const projectsInfos = (info: any, index: number) => {
        return (
            <RepoInfoCard
                key={'infoCard' + index}
                initInfo={info}
                index={index}
                nowActive={activeCardIdx}
                callback={projectCardOnClick}
            />
        )
    }

    const renderProjectsInfos = (infoArray?: any[]) => {
        if (infoArray && Array.isArray(infoArray)) {
            return (infoArray.map((info, idx) => {
                return projectsInfos(JSON.parse(info), idx)
            }))
        }
    }

    const pageNums = () => {
        if (totalRepos % repoListCapacity === 0) {
            return Math.floor(totalRepos / repoListCapacity)
        } else {
            return Math.floor(totalRepos / repoListCapacity) + 1
        }
    }

    const toPage = (i: number) => {
        if (1 <= i && i <= pageNums()) {
            setPageIdx(i)
        }
    }

    const onFormInput = (target: EventTarget) => {
        const t = target as HTMLTextAreaElement
        setPageFormInput(t.value)
    }

    const onPageBtnClicked = () => {
        if (checkIsNumber(pageFormInput)) {
            const pageInput = parseInt(pageFormInput)
            if (pageInput > 0 && pageInput <= pageNums()) {
                toPage(pageInput)
            } else {
                window.alert('Out of page index, max page number is ' + pageNums())
            }
        } else {
            window.alert('Please input a number')
        }
    }

    // a little trick

    type CardInfoList = {
        monthly_stars?: any[],
        monthly_issues?: any[],
        monthly_commits?: any[],
    }

    let [showCards, setShowCards] = useState<boolean>(false)
    let [cardInfoList, setCardInfoList] = useState<CardInfoList>({})
    let [cardInfoListToDisplay, setCardInfoListToDisplay] = useState<CardInfoList>({})

    useEffect(() => {
        if (infoList.length && activeCardIdx < infoList.length) {
            setShowCards(false)
            setCardInfoListToDisplay({})
            let parsedInfoList = JSON.parse(infoList[activeCardIdx])
            if (parsedInfoList) {
                setCardInfoList(parsedInfoList)
                if (showAlarm) {
                    setShowAlarm(false)
                }
            } else {
                setCardInfoList({})
            }
        } else {
            setCardInfoList({})
        }
    }, [activeCardIdx, infoList])

    useEffect(() => {
        setTimeout(() => {
            setShowCards(true)
            setCardInfoListToDisplay(cardInfoList)
        }, 200)
    }, [cardInfoList])

    const renderAlarmInfo = () => {
        if (showAlarm) {
            return (
                <Row style={{
                    marginTop: '-15px',
                }}>
                    <Col>
                        <GFIAlarm title={'Lost connection with server'} onClose={() => {setShowAlarm(false)}} />
                    </Col>
                </Row>
            )
        } else {
            return <></>
        }
    }

    return (
        <>
            <Container className={'single-page account-page-sub-container'}>
                {renderAlarmInfo()}
                <Row>
                    <Col sm={4} style={{
                        minWidth: '330px',
                    }}>
                        <Row>
                            <Col>
                                <Alert variant={'success'}>
                                    <Alert.Heading> Data from {totalRepos} different GitHub repositories </Alert.Heading>
                                </Alert>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <ListGroup style={{
                                    marginBottom: '10px',
                                }}>
                                    {renderProjectsInfos(infoList)}
                                </ListGroup>
                            </Col>
                        </Row>
                        <Row>
                            <GFIPagination
                                pageIdx={pageIdx}
                                toPage={(pageNum) => toPage(pageNum)}
                                pageNums={pageNums()}
                                onFormInput={(target) => onFormInput(target)}
                                onPageBtnClicked={() => onPageBtnClicked()}
                                maxPagingCount={3}
                                needPadding={true}
                            />
                        </Row>
                    </Col>
                    <Col sm={8}>
                        <Fade top delay={0} distance={'7%'} when={showCards} force={true}>
                            <RepoGraphContainer
                                info={'monthly_stars' in cardInfoListToDisplay ? cardInfoListToDisplay.monthly_stars: []}
                                title={'Stars By Month'}
                            />
                        </Fade>
                        <Fade top delay={100} distance={'7%'} when={showCards} force={true}>
                            <RepoGraphContainer
                                info={'monthly_issues' in cardInfoListToDisplay ? cardInfoListToDisplay.monthly_issues: []}
                                title={'Issues By Month'}
                            />
                        </Fade>
                        <Fade top delay={200} distance={'7%'} when={showCards} force={true}>
                            <RepoGraphContainer
                                info={'monthly_commits' in cardInfoListToDisplay ? cardInfoListToDisplay.monthly_commits: []}
                                title={'Commits By Month'}
                            />
                        </Fade>
                    </Col>
                </Row>
                <Row>
                    <GFICopyright />
                </Row>
            </Container>
        </>
    )
}

interface RepoInfoCardProps {
    initInfo: {
        language?: string,
        name?: string,
        owner?: string,
        monthly_stars: any[],
    }
    nowActive: number,
    index: number,
    callback: (idx: number) => void,
}

const RepoInfoCard = (props: RepoInfoCardProps) => {

    let [isActive, setIsActive] = useState(false)
    const [idx] = useState(props.index)

    useEffect(() => {
        setIsActive(props.nowActive === idx)
    }, [props.nowActive, idx])

    const getStars = (monthly_stars: any[]) => {
        let counter = 0
        monthly_stars.forEach((value => {
            if (value.count && checkIsNumber(value.count)) {
                counter += Number(value.count)
            }
        }))
        return counter
    }

    return (
        <ListGroup.Item action as={'button'} onClick={() => props.callback(idx)} variant={isActive ? 'primary': 'light'}>
            <Row>
                <Col style={{fontWeight: 'bold', textDecoration: isActive? 'underline': 'none'}} sm={9}> {props.initInfo.name} </Col>
                <Col sm={3}>
                    <Badge pill style={{position: 'absolute', right: '5px', top: '5px'}}> Stars: {getStars(props.initInfo.monthly_stars)} </Badge>
                </Col>
            </Row>
            <Row>
                <Col sm={9}> Language: {props.initInfo.language} </Col>
            </Row>
            <Row>
                <Col sm={9}> Owner: {props.initInfo.owner} </Col>
            </Row>
        </ListGroup.Item>
    )
}
