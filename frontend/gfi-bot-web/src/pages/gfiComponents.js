import {Container, Col, Row, Form, InputGroup, Button, Pagination} from 'react-bootstrap';
import React from 'react';
import {defaultFontFamily} from '../utils';

export const GFICopyright = () => {

    const copyright = 'Copyright ©2021 OSS Lab, Peking University'

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

export const GFISearchBar = (props) => {

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
                        <Col sm={calStyle(props.fieldStyle, false)}>
                            <Form.Control placeholder={props.description} />
                        </Col>
                        <Col/>
                        <Col sm={calStyle(props.fieldStyle, true)}>
                            <Button style={{float: 'right'}} onClick={() => {props.search()}}> {props.title} </Button>
                        </Col>
                    </InputGroup>
                </Form.Group>
            </Row>
        </Container>
    )
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
        if (!pageArray.includes(pageNums)) {
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
