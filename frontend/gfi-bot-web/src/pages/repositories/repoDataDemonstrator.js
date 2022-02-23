import React from 'react';
import {Col, Container, Row} from 'react-bootstrap';
import ReactECharts from 'echarts-for-react';

export const RepoGraphContainer = (props) => {

    const dataMonthParser = (info) => {
        return info.map((item, _) => {
            return item.month
        })
    }

    const dataCountParser = (info) => {
        return info.map((item, _) => {
            return item.count
        })
    }

    const issueDataParser = (info) => {
        if (typeof info !== 'undefined') {
            return info.map((tempInfo, i) => {
                return {
                    count: tempInfo.count,
                    month: tempInfo.month.slice(0, 7),
                }
            })
        } else return []
    }

    const renderData = (info) => {
        if (info.length) {
            let detailedInfo = issueDataParser(info)
            let xData = dataMonthParser(detailedInfo)
            let yData = dataCountParser(detailedInfo)
            return (
                <RepoDataGraph xData={xData} yData={yData} />
            )
        }
    }

    const render = () => {
        if (props && props.info && props.info.length) {
            return (
                <Container>
                    <Row>
                        <Col className={'float-end'}
                             style={{
                                 textAlign: 'right',
                                 fontWeight: 'bolder',
                                 fontSize: 'larger',
                                 marginBottom: '10px',
                        }}>
                            {props.title}
                        </Col>
                    </Row>
                    <Row>
                        <Col>
                            {renderData(props.info)}
                        </Col>
                    </Row>
                </Container>
            )
        } else {
            return <Container />
        }
    }

    return render()
}

const RepoDataGraph = (props) => {
    let options = {
        grid: { top: 10, right: 10, bottom: 50, left: 30 },
        xAxis: {
            type: 'category',
            data: props.xData,
        },
        yAxis: {
            type: 'value',
        },
        series: [{
            data: props.yData,
            type: 'line',
            smooth: 'true',
        }],
        tooltip: {
            trigger: 'axis',
        },
    }

    return (
        <Container>
            <ReactECharts option={options} />
        </Container>
    )
}
