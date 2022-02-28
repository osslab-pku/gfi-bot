import React from 'react';
import {Col, Container, Row} from 'react-bootstrap';
import ReactECharts from 'echarts-for-react';

export const RepoGraphContainer = ({info, title}) => {

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
        if (info && info.length) {
            return (
                <Container>
                    <Row>
                        <Col style={{
                            textAlign: 'left',
                            fontWeight: 'bolder',
                            fontSize: 'larger',
                            marginBottom: '10px',
                            marginLeft: '40px',
                        }}>
                            {title}
                        </Col>
                    </Row>
                    <Row>
                        <Col>
                            {renderData(info)}
                        </Col>
                    </Row>
                </Container>
            )
        } else {
            return <></>
        }
    }

    return render()
}

const RepoDataGraph = ({xData, yData}) => {

    let options = {
        grid: { top: 10, right: 10, bottom: 50, left: 40 },
        xAxis: {
            type: 'category',
            data: xData,
        },
        yAxis: {
            type: 'value',
        },
        series: [{
            data: yData,
            type: 'line',
            smooth: 'true',
            animation: false,
        }],
        tooltip: {
            trigger: 'axis',
        },
        animation: false,
    }

    return (
        <Container>
            <ReactECharts option={options} />
        </Container>
    )
}
