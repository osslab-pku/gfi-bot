import React from 'react';
import {Container, Col, Row, Form, InputGroup, Button, Pagination} from 'react-bootstrap';

import '../style/gfiStyle.css'
import {SearchOutlined} from '@ant-design/icons';
import {defaultFontFamily} from '../utils';

export const MainPage = (props) => {

    return (
        <Container className={'singlePage'}>
            <Row style={{marginTop: '7px', marginBottom: '7px'}}>
                <Col sm={1}/>
                <Col style={{
                    fontSize: 'xx-large',
                    fontWeight: 'bold',
                    fontFamily: defaultFontFamily,
                }}>
                    GFI BOT
                </Col>
                <Col sm={1}/>
            </Row>
            <Row>
                <Col sm={1}/>
                <Col>
                    <Form.Group>
                        <InputGroup>
                            <Form.Control
                                placeholder={'Github URL'}
                                style={{
                                    minWidth: '270px',
                                }}
                                aria-describedby={'append-icon'}
                            />
                            <Button>
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
                <Col sm={1}/>
            </Row>
        </Container>
    )
}