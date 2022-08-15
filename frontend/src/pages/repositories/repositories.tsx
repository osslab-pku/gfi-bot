import React, { useEffect, useState } from 'react';
import { Alert, Badge, Col, Container, ListGroup, Row } from 'react-bootstrap';
import '../../style/gfiStyle.css';

import { useDispatch } from 'react-redux';
import { checkIsNumber } from '../../utils';
import { GFIAlarm, GFIPagination } from '../GFIComponents';
import { RepoGraphContainer } from './repoDataDemonstrator';

import { getRepoNum, getPagedRepoDetailedInfo } from '../../api/api';

import {
  createAccountNavStateAction,
  createGlobalProgressBarAction,
} from '../../storage/reducers';

export function Repositories() {
  const repoListCapacity = 5;

  const [pageIdx, setPageIdx] = useState<number>(1);

  const [totalRepos, setTotalRepos] = useState<number>(0);
  const [showAlarm, setShowAlarm] = useState<boolean>(false);

  const dispatch = useDispatch();
  useEffect(() => {
    dispatch(createAccountNavStateAction({ show: true }));
  }, []);

  useEffect(() => {
    getRepoNum().then((num) => {
      if (num && Number.isInteger(num)) {
        setTotalRepos(num);
      } else {
        setTotalRepos(0);
        setShowAlarm(true);
      }
    });
  }, [pageIdx]);

  const [infoList, setInfoList] = useState<any[]>([]);
  useEffect(() => {
    const beginIdx = (pageIdx - 1) * repoListCapacity;
    dispatch(createGlobalProgressBarAction({ hidden: false }));
    dispatch(createAccountNavStateAction({ show: true }));
    getPagedRepoDetailedInfo(beginIdx, repoListCapacity)
      .then((repoList) => {
        if (repoList && Array.isArray(repoList)) {
          setInfoList(repoList);
        } else {
          setInfoList([]);
          setShowAlarm(true);
        }
      })
      .then(() => {
        setActiveCardIdx(0);
        dispatch(createGlobalProgressBarAction({ hidden: true }));
      });
  }, [pageIdx]);

  const [activeCardIdx, setActiveCardIdx] = useState<number>(0);
  const [pageFormInput, setPageFormInput] = useState<string>('0');

  const projectCardOnClick = (idx: number) => {
    setActiveCardIdx(idx);
  };

  const projectsInfos = (info: any, index: number) => {
    return (
      <RepoInfoCard
        key={`infoCard${index}`}
        initInfo={info}
        index={index}
        nowActive={activeCardIdx}
        callback={projectCardOnClick}
      />
    );
  };

  const renderProjectsInfos = (infoArray?: any[]) => {
    if (infoArray && Array.isArray(infoArray)) {
      return infoArray.map((info, idx) => {
        return projectsInfos(info, idx);
      });
    }
  };

  const pageNums = () => {
    if (totalRepos % repoListCapacity === 0) {
      return Math.floor(totalRepos / repoListCapacity);
    }
    return Math.floor(totalRepos / repoListCapacity) + 1;
  };

  const toPage = (i: number) => {
    if (i >= 1 && i <= pageNums()) {
      setPageIdx(i);
    }
  };

  const onFormInput = (target: EventTarget) => {
    const t = target as HTMLTextAreaElement;
    setPageFormInput(t.value);
  };

  const onPageBtnClicked = () => {
    if (checkIsNumber(pageFormInput)) {
      const pageInput = parseInt(pageFormInput);
      if (pageInput > 0 && pageInput <= pageNums()) {
        toPage(pageInput);
      } else {
        window.alert(`Out of page index, max page number is ${pageNums()}`);
      }
    } else {
      window.alert('Please input a number');
    }
  };

  // a little trick

  type CardInfoList = {
    monthly_stars?: any[];
    monthly_issues?: any[];
    monthly_commits?: any[];
  };

  const [showCards, setShowCards] = useState<boolean>(false);
  const [cardInfoList, setCardInfoList] = useState<CardInfoList>({});
  const [cardInfoListToDisplay, setCardInfoListToDisplay] =
    useState<CardInfoList>({});

  useEffect(() => {
    if (infoList.length && activeCardIdx < infoList.length) {
      setShowCards(false);
      setCardInfoListToDisplay({});
      const parsedInfoList = infoList[activeCardIdx];
      if (parsedInfoList) {
        setCardInfoList(parsedInfoList);
        if (showAlarm) {
          setShowAlarm(false);
        }
      } else {
        setCardInfoList({});
      }
    } else {
      setCardInfoList({});
    }
  }, [activeCardIdx, infoList]);

  useEffect(() => {
    setTimeout(() => {
      setShowCards(true);
      setCardInfoListToDisplay(cardInfoList);
    }, 200);
  }, [cardInfoList]);

  const renderAlarmInfo = () => {
    if (showAlarm) {
      return (
        <Row
          style={{
            marginTop: '-15px',
          }}
        >
          <Col>
            <GFIAlarm
              title="Lost connection with server"
              onClose={() => {
                setShowAlarm(false);
              }}
            />
          </Col>
        </Row>
      );
    }
    return <></>;
  };

  return (
    <Container className="single-page account-page-sub-container">
      {renderAlarmInfo()}
      <Row>
        <Col
          sm={4}
          style={{
            minWidth: '330px',
          }}
        >
          <Row>
            <Col>
              <Alert variant="success">
                <Alert.Heading>
                  {' '}
                  Data from {totalRepos} different GitHub repositories{' '}
                </Alert.Heading>
              </Alert>
            </Col>
          </Row>
          <Row>
            <Col>
              <ListGroup
                style={{
                  marginBottom: '10px',
                }}
              >
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
              needPadding
              needInputArea
            />
          </Row>
        </Col>
        <Col sm={8}>
          <RepoGraphContainer
            info={
              'monthly_stars' in cardInfoListToDisplay
                ? cardInfoListToDisplay.monthly_stars
                : []
            }
            title="Stars By Month"
          />
          <RepoGraphContainer
            info={
              'monthly_issues' in cardInfoListToDisplay
                ? cardInfoListToDisplay.monthly_issues
                : []
            }
            title="Issues By Month"
          />
          <RepoGraphContainer
            info={
              'monthly_commits' in cardInfoListToDisplay
                ? cardInfoListToDisplay.monthly_commits
                : []
            }
            title="Commits By Month"
          />
        </Col>
      </Row>
    </Container>
  );
}

interface RepoInfoCardProps {
  initInfo: {
    language?: string;
    name?: string;
    owner?: string;
    monthly_stars: any[];
  };
  nowActive: number;
  index: number;
  callback: (idx: number) => void;
}

function RepoInfoCard(props: RepoInfoCardProps) {
  const [isActive, setIsActive] = useState(false);
  const [idx] = useState(props.index);

  useEffect(() => {
    setIsActive(props.nowActive === idx);
  }, [props.nowActive, idx]);

  const getStars = (monthly_stars: any[]) => {
    let counter = 0;
    monthly_stars.forEach((value) => {
      if (value.count && checkIsNumber(value.count)) {
        counter += Number(value.count);
      }
    });
    return counter;
  };

  return (
    <ListGroup.Item
      action
      as="button"
      onClick={() => props.callback(idx)}
      variant={isActive ? 'primary' : 'light'}
    >
      <Row>
        <Col
          style={{
            fontWeight: 'bold',
            textDecoration: isActive ? 'underline' : 'none',
          }}
          sm={9}
        >
          {' '}
          {props.initInfo.name}{' '}
        </Col>
        <Col sm={3}>
          <Badge
            pill
            style={{ position: 'absolute', right: '5px', top: '5px' }}
          >
            {' '}
            Stars: {getStars(props.initInfo.monthly_stars)}{' '}
          </Badge>
        </Col>
      </Row>
      <Row>
        <Col sm={9}> Language: {props.initInfo.language} </Col>
      </Row>
      <Row>
        <Col sm={9}> Owner: {props.initInfo.owner} </Col>
      </Row>
    </ListGroup.Item>
  );
}
