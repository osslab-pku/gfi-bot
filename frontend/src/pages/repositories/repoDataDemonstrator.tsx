import React from 'react';
import { Col, Container, Row } from 'react-bootstrap';
import ReactECharts from 'echarts-for-react';

export interface RepoGraphContainerProps {
  info?: any[];
  title?: string;
}

export const RepoGraphContainer = (props: RepoGraphContainerProps) => {
  const dataMonthParser = (info: any[]) => {
    return info.map((item, _) => {
      return item.month;
    });
  };

  const dataCountParser = (info: any[]) => {
    return info.map((item, _) => {
      return item.count;
    });
  };

  // desciption for ISO date format
  // https://www.w3schools.com/js/js_date_methods.asp
  const dateDescriptor = (date: string) =>
    new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric',
    });

  const issueDataParser = (info: any[] | undefined) => {
    if (typeof info !== 'undefined') {
      return info.map((tempInfo, i) => {
        return {
          count: tempInfo.count,
          month: dateDescriptor(tempInfo.month),
        };
      });
    }
    return [];
  };

  const renderData = (info: any[] | undefined) => {
    if (info && info.length) {
      const detailedInfo = issueDataParser(info);
      const xData = dataMonthParser(detailedInfo);
      const yData = dataCountParser(detailedInfo);
      return <RepoDataGraph xData={xData} yData={yData} />;
    }
  };

  const render = () => {
    if (props.info && props.info.length) {
      return (
        <Container>
          <Row>
            <Col
              style={{
                textAlign: 'left',
                fontWeight: 'bolder',
                fontSize: 'larger',
                marginBottom: '10px',
                marginLeft: '40px',
              }}
            >
              {props.title}
            </Col>
          </Row>
          <Row>
            <Col>{renderData(props.info)}</Col>
          </Row>
        </Container>
      );
    }
    return <></>;
  };

  return render();
};

interface RepoDataGraphProps {
  xData: any[];
  yData: any[];
}

function RepoDataGraph(props: RepoDataGraphProps) {
  const options = {
    grid: { top: 10, right: 10, bottom: 50, left: 40 },
    xAxis: {
      type: 'category',
      data: props.xData,
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        data: props.yData,
        type: 'line',
        smooth: 'true',
        animation: false,
      },
    ],
    tooltip: {
      trigger: 'axis',
    },
    animation: false,
  };

  return <ReactECharts option={options} />;
}
