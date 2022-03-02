import {Container, Col, Row, Form, InputGroup, Button, Pagination, Alert} from 'react-bootstrap';
import React, {createRef} from 'react';
import {checkIsNumber, defaultFontFamily} from '../utils';
import {gsap} from 'gsap';
import PropTypes from 'prop-types';

export const GFICopyright = () => {

    const copyright = 'Copyright © 2021 OSS Lab, Peking University. All rights reserved.'

    return (
        <Container style={{
            marginTop:'20px',
            marginBottom: '10px',
            fontFamily: defaultFontFamily,
            fontSize: '15px',
            fontWeight: '100',
        }}>
            <Row>
                <Col style={{textAlign: 'center'}}>
                    {copyright}
                </Col>
            </Row>
        </Container>
    )
}

export const GFISearchBar = ({fieldStyle, search, title, description}) => {

    const calStyle = (fieldStyle, isBtn) => {
        if (isBtn === true) {
            if (fieldStyle === 'large') {
                return 2
            } else {
                return 1
            }
        } else {
            if (fieldStyle === 'large') {
                return 10
            } else {
                return 4
            }
        }
    }

    return (
        <Container>
            <Row style={{marginTop: '20px', marginBottom: '20px'}}>
                <Form.Group>
                    <InputGroup>
                        <Col sm={calStyle(fieldStyle, false)}>
                            <Form.Control placeholder={description} />
                        </Col>
                        <Col/>
                        <Col sm={calStyle(fieldStyle, true)}>
                            <Button style={{float: 'right'}} onClick={() => {search()}}> {title} </Button>
                        </Col>
                    </InputGroup>
                </Form.Group>
            </Row>
        </Container>
    )
}

GFISearchBar.propTypes = {
    fieldStyle: PropTypes.oneOf(['large', '']),
    search: PropTypes.func,
    title: PropTypes.string,
    description: PropTypes.string,
}

export const GFIPagination = (props) => {

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
        if (props.pageIdx === props.pageNums - 1) {
            toLastPage()
        } else {
            props.toPage(props.pageIdx + 1)
        }
    }

    const calRenderRange = (pageNums: Number, selectedIdx: Number) => {
        let pageArray: Array = Array()
        let idx = Math.max(selectedIdx - maxPagingCount + 1, 1)
        for (let i = 0; i < maxPagingCount; i++, idx++) {
            pageArray.push(idx)
            if (idx + 1 > pageNums) {
                break
            }
        }
        return pageArray
    }

    const renderPagingItem = (pageNums: Number, selectedIdx: Number) => {
        let pageArray = calRenderRange(pageNums, selectedIdx)
        let renderedArray = pageArray.map((ele, idx) => {
            return (
                <Pagination.Item
                    key={ele}
                    active={ele === selectedIdx}
                    onClick={() => props.toPage(ele)}
                > {ele} </Pagination.Item>
            )
        })

        if (!pageArray.includes(1)) {
            let showDot: Boolean = !pageArray.includes(2)
            renderedArray.unshift(renderExpPagingItem(1, showDot))
        }
        if (!pageArray.includes(pageNums) && pageNums) {
            let showDot: Boolean = !pageArray.includes(pageNums - 1)
            renderedArray.push(renderExpPagingItem(pageNums, showDot))
        }

        return renderedArray
    }

    const renderExpPagingItem = (pageNum: Number, shotDot: Boolean) => {
        let msg = pageNum
        if (shotDot) {
            msg = '.. ' + pageNum
        }
        return (
            <Pagination.Item
                key={pageNum}
                onClick={() => props.toPage(pageNum)}
            > {msg} </Pagination.Item>
        )
    }

    return (
        <Container style={{ overflow: 'hidden' }}>
            <Row style={{ marginTop: '10px' }}>
                <Form.Group>
                    <Col sm={8} style={{ float: 'left' }}>
                        <Pagination style={{ margin: '0 auto' }}>
                            <Pagination.Prev onClick={() => {toPrevPage()}} />
                            {renderPagingItem(props.pageNums, props.pageIdx)}
                            <Pagination.Next onClick={() => {toNextPage()}} />
                        </Pagination>
                    </Col>
                    <Col sm={4} style={{ float: 'right', }}>
                        <Form.Label style={{
                            maxWidth: '80px',
                            float: 'right',
                        }}>
                            <Form.Control placeholder={props.pageIdx + '/' + props.pageNums}
                                          onChange={(e) => {props.onFormInput(e.target)}}
                                          onKeyDown={(e) => {
                                              if (e.key === 'Enter') {
                                                  e.preventDefault()
                                                  props.onPageBtnClicked()
                                              }
                                          }}
                            />
                        </Form.Label>
                    </Col>
                </Form.Group>
            </Row>
        </Container>
    )
}

GFIPagination.propTypes = {
    maxPagingCount: PropTypes.number,
    pageNums: PropTypes.number,
    pageIdx: PropTypes.number,
    onPageBtnClicked: PropTypes.func,
    toPage: PropTypes.func,
    onFormInput: PropTypes.func,
}

export class GFIAlarm extends React.Component {
    constructor(props) {
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
        const {onClose} = this.props
        let timeline = gsap.timeline()
        timeline
            .to(this.selfRef.current, {
                duration: 0.4,
                autoAlpha: 0,
                y: -25,
            })
            .eventCallback('onComplete', () => {
                if (onClose) {
                    onClose()
                }
            })
            .play()
    }

    render() {
        const {title} = this.props
        return (
            <Alert
                variant={'danger'}
                dismissible={true}
                ref={this.selfRef}
                onClick={this.alarmOnClose}
            >
                {title}
            </Alert>
        );
    }
}

GFIAlarm.propTypes = {
    title: PropTypes.string,
    onClose: PropTypes.func,
}

export class GFIProgressBar extends React.Component {
    constructor(props) {
        super(props)
        this.barRef = React.createRef()
        this.state = {
            barWidth: '0%',
        }
    }

    checkValidWidth = (width: String) => {
        return (checkIsNumber(width.slice(0, -1)) && width.slice(-1) === '%')
            || checkIsNumber(width)
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        const {barWidth, onFinished} = this.props
        if (this.checkValidWidth(barWidth)
            && this.checkValidWidth(prevProps.barWidth)) {

            if (barWidth === prevProps.barWidth) {
                return
            }

            gsap
                .to(this.barRef.current, {
                    duration: 0.2,
                    width: barWidth,
                    paused: true
                })
                .eventCallback('onComplete', () => {
                    this.setState({
                        barWidth: barWidth,
                    })
                })
                .play()

            if (barWidth === '100%' || barWidth === window.innerWidth) {
                gsap
                    .to(this.barRef.current, {
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
        const {height} = this.props
        return (
            <div style={{
                backgroundColor: '#85a5ff',
                height: height,
                width: this.state.barWidth,
                borderRadius: '2px',
            }} ref={this.barRef} />
        )
    }
}

GFIProgressBar.propTypes = {
    barWidth: PropTypes.string,
    onFinished: PropTypes.func,
    height: PropTypes.string,
}
