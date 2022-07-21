import React, { ForwardedRef, forwardRef, useEffect, useState } from 'react';
import type { GFITrainingSummary } from '../../model/api';
import { getGFINum, getTrainingSummary } from '../../api/api';

import '../../style/gfiStyle.css';
import { Group } from '@visx/group';
import { scaleLinear } from '@visx/scale';
import { Bar, LinePath } from '@visx/shape';
import { curveNatural } from '@visx/curve';
import {
  GradientLightgreenGreen,
  GradientOrangeRed,
  GradientTealBlue,
  GradientPurpleTeal,
  GradientPinkBlue,
} from '@visx/gradient';

export interface GFITrainingSummaryDisplayView {}

interface TrainingSummary {
  issueNumTest: number;
  issueNumTrain: number;
  repoNum: number;
  avgAuc: number;
  avgAcc: number;
  issueResolved: number;
  issueResolvedByNewcomers: number;
}

type ActivityTagType = '7Days' | '1Month' | '3Months' | '1Year' | 'Older';
const ActivityTags: ActivityTagType[] = [
  '7Days',
  '1Month',
  '3Months',
  '1Year',
  'Older',
];
interface RepoActivity {
  time: ActivityTagType;
  num: number;
}

const getActivityTime: (timeStr: string) => ActivityTagType[] = (
  timeStr: string
) => {
  const date = new Date(timeStr).getTime();
  const now = new Date().getTime();
  const day = 24 * 3600 * 1000;
  const week = 7 * day;
  const month = 31 * day;
  const year = 365 * day;
  if (now - week <= date) {
    return ActivityTags.slice(0);
  }
  if (now - month <= date) {
    return ActivityTags.slice(1);
  }
  if (now - 3 * month <= date) {
    return ActivityTags.slice(2);
  }
  if (now - year <= day) {
    return ActivityTags.slice(3);
  }
  return ActivityTags.slice(4);
};

export const GFITrainingSummaryDisplayView = forwardRef(
  (props, ref: ForwardedRef<HTMLDivElement>) => {
    const [originTrainingSummary, setOriginTrainingSummary] =
      useState<GFITrainingSummary[]>();
    const fullChartDefaultHeight = 75;
    const fullChartDefaultHorizontalMargin = 8;
    const [fullChartHeight, setFullChartHeight] = useState(
      fullChartDefaultHeight
    );
    const [gfiNum, setGfiNum] = useState(0);
    const [fullChartWidth, setFullChartWidth] = useState(0);
    const [halfChartWidth, setHalfChartWidth] = useState(0);
    const [displayedSummary, setDisplayedSummary] = useState<TrainingSummary>();
    const [repoActivitySummary, setRepoActivitySummary] = useState<
      RepoActivity[]
    >(
      ActivityTags.map((item) => ({
        time: item,
        num: 0,
      }))
    );
    const indexMapping: { [key in ActivityTagType]: number } = {
      '7Days': 0,
      '1Month': 1,
      '3Months': 2,
      '1Year': 3,
      Older: 4,
    };

    useEffect(() => {
      getTrainingSummary().then((res) => {
        if (res) {
          setOriginTrainingSummary(res);
        }
      });
      getGFINum().then((res) => {
        if (res) {
          setGfiNum(res);
        }
      });
    }, []);

    useEffect(() => {
      if (originTrainingSummary && originTrainingSummary.length) {
        const repoNum = originTrainingSummary.length;
        let issueNumTest = 0;
        let issueNumTrain = 0;
        let totalAcc = 0;
        let totalAuc = 0;
        let resolved = 0;
        let resolvedByNewcomers = 0;
        const repoActivity: RepoActivity[] = ActivityTags.map((item) => ({
          time: item,
          num: 0,
        }));
        for (const summary of originTrainingSummary) {
          issueNumTest += summary.issues_test;
          issueNumTrain += summary.issues_train;
          totalAcc += summary.accuracy * summary.issues_train;
          totalAuc += summary.auc * summary.issues_train;
          resolved += summary.n_resolved_issues;
          resolvedByNewcomers += summary.n_newcomer_resolved;
          getActivityTime(summary.last_updated).forEach((value) => {
            repoActivity[indexMapping[value]].num += 1;
          });
        }
        setRepoActivitySummary(repoActivity);
        setDisplayedSummary({
          issueNumTest,
          issueNumTrain,
          repoNum,
          avgAcc: totalAcc / issueNumTrain,
          avgAuc: totalAuc / issueNumTrain,
          issueResolved: resolved,
          issueResolvedByNewcomers: resolvedByNewcomers,
        });
      }
    }, [originTrainingSummary]);

    return (
      <>
        {displayedSummary && (
          <div
            className="gfi-training-summary-container flex-col no-select"
            ref={(el) => {
              if (el !== null) {
                setFullChartWidth(
                  el.clientWidth - 2 * fullChartDefaultHorizontalMargin
                );
                setHalfChartWidth(
                  (el.clientWidth - 3 * fullChartDefaultHorizontalMargin) / 2.0
                );
              }
            }}
          >
            <div
              className="flex-row justify-content-between align-center flex-wrap"
              style={{
                marginLeft: `${fullChartDefaultHorizontalMargin}px`,
                marginRight: `${fullChartDefaultHorizontalMargin}px`,
                marginBottom: '0.5rem',
              }}
            >
              <div className="flex-row gfi-training-nums-displayer-item">
                <NumInfoDisplayer
                  width={halfChartWidth}
                  height={60}
                  gradient={
                    (
                      <GradientOrangeRed id="g-red-info" />
                    ) as unknown as Element
                  }
                  gradientId="g-red-info"
                  num={displayedSummary.repoNum}
                  title="Repositories"
                />
              </div>
              <div className="flex-row gfi-training-nums-displayer-item">
                <NumInfoDisplayer
                  width={halfChartWidth}
                  height={60}
                  gradient={
                    (
                      <GradientLightgreenGreen id="g-green-info" />
                    ) as unknown as Element
                  }
                  gradientId="g-green-info"
                  num={
                    displayedSummary.issueNumTest +
                    displayedSummary.issueNumTrain
                  }
                  title="Issues"
                />
              </div>
              <div className="flex-row gfi-training-nums-displayer-item">
                <NumInfoDisplayer
                  width={halfChartWidth}
                  height={60}
                  gradient={
                    (
                      <GradientPurpleTeal id="g-purple-info" />
                    ) as unknown as Element
                  }
                  gradientId="g-purple-info"
                  num={gfiNum}
                  title="Good First Issues"
                />
              </div>
              <div className="flex-row gfi-training-nums-displayer-item">
                <NumInfoDisplayer
                  width={halfChartWidth}
                  height={60}
                  gradient={
                    (
                      <GradientPinkBlue id="g-pink-blue-teal-info" />
                    ) as unknown as Element
                  }
                  gradientId="g-pink-blue-teal-info"
                  num={displayedSummary.issueResolved}
                  title="Issues Resolved"
                />
              </div>
            </div>
            <div className="flex-row justify-content-center">
              <AucAccBarDisplayer
                width={fullChartWidth}
                height={fullChartHeight}
                data={[
                  { name: 'AUC', value: displayedSummary.avgAuc },
                  { name: 'ACC', value: displayedSummary.avgAcc },
                ]}
              />
            </div>
            <div
              className="flex-row justify-content-center"
              style={{ marginTop: '0.5rem' }}
            >
              <ActivityDisplayer
                width={fullChartWidth}
                height={120}
                data={repoActivitySummary}
              />
            </div>
          </div>
        )}
      </>
    );
  }
);

function NumInfoDisplayer(props: {
  width: number;
  height: number;
  gradient: Element;
  gradientId: string;
  num: number;
  title: string;
}) {
  const { width, height, gradient, gradientId, num, title } = props;

  return (
    <>
      {/*
       // @ts-ignore */}
      <svg
        width={width}
        height={height}
        className="flex-row justify-content-center align-center"
      >
        {gradient}
        <rect
          width={width}
          height={height}
          fill={`url(#${gradientId})`}
          rx={7}
          ry={7}
        />
        <text
          x="50%"
          y="40%"
          dominantBaseline="middle"
          textAnchor="middle"
          className="gfi-training-num-info-num"
        >
          {num}
        </text>
        <text x="50%" y="75%" className="gfi-training-num-info-title">
          {title}
        </text>
      </svg>
    </>
  );
}

function AucAccBarDisplayer(props: {
  width: number;
  height: number;
  data: { name: 'AUC' | 'ACC'; value: number }[];
}) {
  const { width, height, data } = props;
  const barWidth = 25;
  const paddingTop = 33;
  const margin = (height - barWidth * data.length) / (data.length + 1.0);

  const yScale = scaleLinear<number>({
    domain: [0, 1],
    range: [0, width],
    nice: true,
  });

  return (
    <svg width={width} height={height + paddingTop}>
      <GradientTealBlue id="teal" />
      <rect
        width={width}
        height={height + paddingTop}
        fill="url(#teal)"
        rx={7}
        ry={7}
      />
      <text className="gfi-training-auc-displayer-label-title" y={26} x={12}>
        Average AUC & ACC
      </text>
      <Group>
        {data.map((d, idx) => {
          return (
            <>
              <Bar
                x={10}
                y={margin + idx * (barWidth + margin) + paddingTop}
                width={yScale(d.value)}
                height={barWidth}
                fill="rgba(23, 233, 217, .5)"
                rx={10}
                ry={10}
              />
              <text
                x={20}
                y={margin + idx * (barWidth + margin) + 14 + paddingTop}
                className="gfi-training-auc-displayer-label"
                dominantBaseline="middle"
              >
                {d.name}
              </text>
              <text
                x={yScale(d.value) - 35}
                y={margin + idx * (barWidth + margin) + 14 + paddingTop}
                className="gfi-training-auc-displayer-label-val"
                dominantBaseline="middle"
              >
                {Math.round(d.value * 100) / 100}
              </text>
            </>
          );
        })}
      </Group>
    </svg>
  );
}

function ActivityDisplayer(props: {
  width: number;
  height: number;
  data: RepoActivity[];
}) {
  const { width, height, data } = props;

  const getMaxY = () => {
    let maxNum = 0;
    for (const d of data) {
      maxNum = Math.max(maxNum, d.num);
    }
    return maxNum;
  };

  const graphWidth = width * 0.9;
  const graphHeight = height * 0.6;

  const yScale = scaleLinear<number>({
    domain: [0, getMaxY()],
    range: [graphHeight, 0],
  });

  const marginX = (width - graphWidth * 0.8) / 2.0;
  const marginY = (height - graphHeight) / 2.0 - 4;

  return (
    <svg width={width} height={height}>
      <g className="flex-row align-center justify-content-center">
        <GradientLightgreenGreen id="gradient-act-green" />
        <rect
          width={width}
          height={height}
          fill="url(#gradient-act-green)"
          rx={7}
          ry={7}
        />
        <text
          className="gfi-training-activity-displayer-title"
          dominantBaseline="middle"
          textAnchor="end"
          x="90%"
          y="67%"
        >
          Repo Last Activities
        </text>
        <Group>
          {data.map((d, idx) => (
            <circle
              r={3}
              cx={(graphWidth / data.length) * idx + marginX}
              cy={yScale(d.num) + marginY}
              fill="white"
            />
          ))}
          <LinePath<RepoActivity>
            curve={curveNatural}
            data={data}
            x={(d, i) => (graphWidth / data.length) * i + marginX}
            y={(d) => yScale(d.num) + marginY}
            stroke="white"
            strokeWidth={1.5}
            strokeOpacity={1}
          />
          {data.map((d, idx) => (
            <text
              x={(graphWidth / data.length) * idx + marginX}
              y={yScale(0) + marginY + 14}
              fill="white"
              textAnchor="middle"
              dominantBaseline="middle"
              className="gfi-training-activity-displayer-label"
            >
              {' '}
              {d.time}{' '}
            </text>
          ))}
        </Group>
      </g>
    </svg>
  );
}
