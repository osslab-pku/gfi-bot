import React, { MouseEventHandler, useEffect, useRef, useState } from 'react';
import {
  Button,
  Col,
  Container,
  Dropdown,
  Form,
  ListGroup,
  Nav,
  Overlay,
  Popover,
  Row,
} from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { withRouter } from 'react-router-dom';
// rollup compatibility issue see:https://github.com/vitejs/vite/issues/2139#issuecomment-1024852072
import { KeepAlive } from 'react-activation';

import '../../style/gfiStyle.css';
import { useDispatch, useSelector } from 'react-redux';
import {
  createAccountNavStateAction,
  createGlobalProgressBarAction,
} from '../../storage/reducers';
import { GFIRootReducers } from '../../storage/configureStorage';
import { checkIsGitRepoURL, convertFilter } from '../../utils';

import importTips from '../../assets/git-add-demo.png';
import { checkHasRepoPermissions } from '../../api/githubApi';
import { GFIAlarm, GFIAlarmPanelVariants, GFIOverlay } from '../GFIComponents';
import { addRepoToGFIBot, getAddRepoHistory } from '../../api/api';
import type { RepoBrief } from '../../model/api';
import {
  GFIIssueMonitor,
  GFIRepoDisplayView,
  GFIRepoStaticsDemonstrator,
} from '../main/GFIRepoDisplayView';
import { GFIRepoSearchingFilterType } from '../main/mainHeader';
import { useIsMobile } from '../app/windowContext';
import { SearchHistory } from './SearchHistory';
import { RepoSetting } from './RepoSetting';

export interface GFIPortal {}
type GFIUserQueryHistoryItem = {
  pending: boolean;
  repo: RepoBrief;
};

type SubPanelIDs = 'Add Project' | 'Search History' | 'My Account';
const SubPanelTitles: SubPanelIDs[] & string[] = [
  'Add Project',
  'Search History',
  'My Account',
];

export function GFIPortal(props: GFIPortal) {
  const dispatch = useDispatch();
  useEffect(() => {
    dispatch(createAccountNavStateAction({ show: true }));
  }, []);

  const [currentPanelID, setCurrentPanelID] = useState<SubPanelIDs & string>(
    'Add Project'
  );

  const renderSubPanel = () => {
    if (currentPanelID === 'Add Project') {
      return (
        <KeepAlive>
          <AddProjectComponent />
        </KeepAlive>
      );
    }
    if (currentPanelID === 'Search History') {
      return <SearchHistory />;
    }
    if (currentPanelID === 'My Account') {
      return <></>;
    }
  };

  return (
    <Container className="account-page-sub-container">
      <Row className="account-page-sub-container-row">
        <Col sm={3}>
          <AccountSideBar
            actionList={SubPanelTitles}
            onClick={(i) => {
              setCurrentPanelID(SubPanelTitles[i]);
            }}
          />
        </Col>
        <Col sm={9}> {renderSubPanel()} </Col>
      </Row>
    </Container>
  );
}

export const GFIPortalPageNav = withRouter((props: { id?: string }) => {
  return (
    <Nav
      variant="pills"
      className="flex-row justify-content-center align-center"
      id={props?.id}
      style={{ marginTop: '10px' }}
    >
      <Nav.Item className="account-nav-container">
        <LinkContainer to="/portal">
          <Nav.Link eventKey={1} className="account-nav">
            Dashboard
          </Nav.Link>
        </LinkContainer>
      </Nav.Item>
      <Nav.Item className="account-nav-container">
        <LinkContainer to="/repos">
          <Nav.Link eventKey={2} className="account-nav" active={false}>
            Repo Data
          </Nav.Link>
        </LinkContainer>
      </Nav.Item>
    </Nav>
  );
});

interface AccountSideBar {
  actionList: string[];
  onClick?: (i: number) => void;
}

function AccountSideBar(props: AccountSideBar) {
  const { actionList, onClick } = props;
  const [selectedList, setSelectedList] = useState(
    actionList.map((_, i) => {
      return !i;
    })
  );

  const userName = useSelector((state: GFIRootReducers) => {
    if ('name' in state.loginReducer) return state.loginReducer.name;
    return undefined;
  });

  const userAvatar = useSelector((state: GFIRootReducers) => {
    if ('avatar' in state.loginReducer) return state.loginReducer.avatar;
    return undefined;
  });

  const renderItems = () => {
    return actionList.map((title, i) => {
      return (
        <ListGroup.Item
          action
          as="button"
          onClick={() => {
            setSelectedList(
              selectedList.map((_, idx) => {
                return idx === i;
              })
            );
            if (onClick) {
              onClick(i);
            }
          }}
          variant={selectedList[i] ? 'primary' : 'light'}
          key={i}
        >
          {title}
        </ListGroup.Item>
      );
    });
  };

  return (
    <div className="flex-col flex-wrap" id="portal-side-bar">
      <div className="flex-row align-center portal-side-bar-userinfo">
        <div className="flex-col portal-side-bar-userinfo-name">
          <div> Hello, </div>
          <div> {userName} </div>
        </div>
        <img src={userAvatar} alt="" />
      </div>
      <ListGroup>{renderItems()}</ListGroup>
    </div>
  );
}

function AddProjectComponent() {
  const [projectURL, setProjectURL] = useState<string>();
  const [showAlarmMsg, setShowAlarmMsg] = useState(false);

  type AlarmConfig = {
    show: boolean;
    msg: string;
    variant?: GFIAlarmPanelVariants;
  };

  const [mainAlarmConfig, setMainAlarmConfig] = useState<AlarmConfig>({
    show: false,
    msg: '',
    variant: 'danger',
  });
  const [addRepoAlarmConfig, setAddRepoAlarmConfig] = useState<AlarmConfig>({
    show: false,
    msg: '',
    variant: 'success',
  });

  const dispatch = useDispatch();
  const showProgressBar = () => {
    dispatch(createGlobalProgressBarAction({ hidden: false }));
  };
  const hideProgressBar = () => {
    dispatch(createGlobalProgressBarAction({ hidden: true }));
  };

  const overlayRef = useRef<HTMLDivElement>(null);
  const [addedRepos, setAddedRepos] = useState<GFIUserQueryHistoryItem[]>();
  const [addedRepoIncrement, setAddedRepoIncrement] = useState(false);
  const fetchAddedRepos = (onComplete?: () => void) => {
    getAddRepoHistory(convertFilter(filterSelected)).then((res) => {
      const finishedQueries: GFIUserQueryHistoryItem[] | undefined =
        res?.finished_queries?.map((info) => ({
          pending: false,
          repo: info,
        }));
      let pendingQueries: GFIUserQueryHistoryItem[] | undefined =
        res?.queries?.map((info) => ({
          pending: true,
          repo: info,
        }));
      if (!Array.isArray(pendingQueries)) {
        pendingQueries = [];
      }

      let completeQueries = '';
      if (finishedQueries && addedRepos) {
        for (const finishedQuery of finishedQueries) {
          for (const reposAdded of addedRepos) {
            if (
              reposAdded.pending &&
              reposAdded.repo.owner === finishedQuery.repo.owner &&
              reposAdded.repo.name === finishedQuery.repo.name
            ) {
              completeQueries += `${finishedQuery.repo.owner}/${finishedQuery.repo.name} `;
            }
          }
        }
        if (completeQueries !== '') {
          setAddRepoAlarmConfig({
            show: true,
            msg: `Repos: ${completeQueries}have been successfully added`,
            variant: 'success',
          });
        }
      }

      setAddedRepos(
        finishedQueries
          ? finishedQueries.concat(pendingQueries)
          : pendingQueries
      );
      if (onComplete) {
        onComplete();
      }
      setAddedRepoIncrement(!addedRepoIncrement);
    });
  };

  useEffect(() => {
    fetchAddedRepos();
  }, []);

  const [intervalID, setIntervalId] = useState<number>();
  useEffect(() => {
    if (intervalID) {
      clearInterval(intervalID);
    }
    setIntervalId(setInterval(fetchAddedRepos, 10000));
    return () => {
      if (intervalID) {
        clearInterval(intervalID);
      }
    };
  }, [addedRepos, addedRepoIncrement]);

  const addGFIRepo = () => {
    let shouldDisplayAlarm = true;
    if (projectURL && checkIsGitRepoURL(projectURL)) {
      const urls = projectURL.split('/');
      const repoName = urls[urls.length - 1].split('.git')[0];
      const repoOwner = urls[urls.length - 2];
      if (repoName && repoOwner) {
        showProgressBar();
        checkHasRepoPermissions(repoName, repoOwner).then((res) => {
          if (res) {
            addRepoToGFIBot(repoName, repoOwner).then((result?: string) => {
              if (result) {
                setMainAlarmConfig({
                  show: true,
                  msg: `Query ${repoOwner}/${repoName} ${result}`,
                  variant: 'success',
                });
                fetchAddedRepos(() => {
                  hideProgressBar();
                });
              } else {
                setMainAlarmConfig({
                  show: true,
                  msg: `Connection Lost`,
                  variant: 'danger',
                });
                hideProgressBar();
              }
            });
          } else {
            setMainAlarmConfig({
              show: true,
              msg: `You\'re not a maintainer of ${repoOwner}/${repoName} or this is a private repository`,
              variant: 'danger',
            });
            hideProgressBar();
          }
        });
        shouldDisplayAlarm = false;
      }
    }
    setShowAlarmMsg(shouldDisplayAlarm);
  };

  const [overlayTarget, setOverlayTarget] = useState<EventTarget>();
  const [showOverlay, setShowOverlay] = useState(false);
  const overlayContainer = useRef(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const onErrorTipClick: MouseEventHandler<HTMLDivElement> = (e) => {
    setOverlayTarget(e.target);
    setShowOverlay(!showOverlay);
  };
  const checkIfClosePopover = (e: MouseEvent) => {
    if (!popoverRef?.current?.contains(e.target as Node)) {
      setShowOverlay(false);
    }
  };

  useEffect(() => {
    if (showOverlay) {
      document.addEventListener('mousedown', checkIfClosePopover);
    } else {
      document.removeEventListener('mousedown', checkIfClosePopover);
    }
    return () => {
      document.removeEventListener('mousedown', checkIfClosePopover);
    };
  }, [showOverlay]);

  const repoInfoPanelRef = useRef<HTMLDivElement>(null);
  const [addedRepoDisplayPanelConfig, setAddedRepoDisplayPanelConfig] =
    useState<RepoBrief>();
  const [showPopover, setShowPopover] = useState(false);

  type FilterType = GFIRepoSearchingFilterType;
  const [filterSelected, setFilterSelected] = useState<FilterType>('Alphabetical');
  const filters: FilterType[] = [
    'Alphabetical',
    'Number of Stars',
    'Issue Resolution Time',
    '% of Issues Resolved by New Contributors',
    '# of Predicted Good First Issues',
  ];

  const onRepoHistoryClicked = (repoInfo: RepoBrief) => {
    setAddedRepoDisplayPanelConfig(repoInfo);
    setShowPopover(true);
  };

  const renderRepoHistory = () => {
    if (addedRepos && addedRepos.length) {
      return addedRepos.map((item, i) => {
        return (
          <RepoHistoryTag
            pending={item.pending}
            repoInfo={item.repo}
            available
            onClick={item.pending ? () => {} : onRepoHistoryClicked}
            key={i}
          />
        );
      });
    }
    return (
      <RepoHistoryTag
        pending
        repoInfo={{
          name: 'None',
          owner: 'Try to add your projects!',
          description: '',
          language: '',
          topics: [],
        }}
        available={false}
      />
    );
  };

  const onFilterSelected = (filter: FilterType) => {
    if (filter !== filterSelected) {
      setFilterSelected(filter);
    }
  };

  useEffect(() => {
    fetchAddedRepos();
  }, [filterSelected]);

  const isMobile = useIsMobile();

  return (
    <div className="flex-col">
      {mainAlarmConfig.show ? (
        <GFIAlarm
          title={mainAlarmConfig.msg}
          onClose={() =>
            setMainAlarmConfig({
              show: false,
              msg: '',
            })
          }
          variant={mainAlarmConfig?.variant}
        />
      ) : (
        <></>
      )}
      <div className="account-page-panel-title project-add-comp-title">
        Add Your Project To GFI-Bot
      </div>
      <div className="project-add-comp-tips">
        <p>
          {' '}
          <strong>Notice: </strong> We&apos;ll register the repository to our
          database and use it for data training and predictions.{' '}
        </p>
        <p>
          {' '}
          Make sure that you are one of the maintainers of the repository.{' '}
        </p>
      </div>
      <div className="project-adder">
        <Form className="flex-col project-adder-form">
          <Form.Label className="project-adder-label">
            {' '}
            Please input a GitHub Repo URL{' '}
          </Form.Label>
          <Form.Control
            placeholder="GitHub URL"
            onChange={(e) => {
              setProjectURL(e.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                addGFIRepo();
              }
            }}
          />
          <div
            className="flex-row align-center"
            style={{ marginTop: '0.5rem' }}
          >
            {showAlarmMsg && (
              <div ref={overlayContainer}>
                <div
                  className="hoverable project-add-alarm"
                  onClick={onErrorTipClick}
                >
                  Please input a correct GitHub Repo URL
                </div>
                <Overlay
                  show={showOverlay}
                  target={overlayTarget}
                  container={overlayContainer}
                  placement="bottom-start"
                >
                  <Popover className="fit" ref={popoverRef}>
                    <Popover.Body className="fit">
                      <img
                        src={importTips}
                        alt=""
                        className="project-add-overlay-warn-tip"
                      />
                    </Popover.Body>
                  </Popover>
                </Overlay>
              </div>
            )}
            <Button
              size="sm"
              variant="outline-primary"
              style={{ marginLeft: 'auto' }}
              onClick={() => {
                addGFIRepo();
              }}
            >
              {' '}
              Add Project{' '}
            </Button>
          </div>
        </Form>
      </div>
      <div className="flex-row align-center project-add-comp-added">
        <div className="account-page-panel-title">Projects Added</div>
        <div className="flex-row align-center" style={{ marginLeft: 'auto' }}>
          <div style={{ fontSize: 'small', marginRight: '0.7rem' }}>
            {' '}
            Sorted By{' '}
          </div>
          <Dropdown>
            <Dropdown.Toggle variant="light" style={{ fontSize: 'small' }}>
              {filterSelected}
            </Dropdown.Toggle>
            <Dropdown.Menu align="end" variant="dark">
              {filters.map((item) => {
                return (
                  <Dropdown.Item
                    onClick={(e) => {
                      onFilterSelected(item);
                    }}
                    style={{ fontSize: 'small' }}
                    key={item}
                  >
                    {item as string}
                  </Dropdown.Item>
                );
              })}
            </Dropdown.Menu>
          </Dropdown>
        </div>
      </div>
      {addRepoAlarmConfig.show ? (
        <div style={{ marginBottom: '-15px', marginTop: '5px' }}>
          <GFIAlarm
            title={addRepoAlarmConfig.msg}
            onClose={() => {
              setAddRepoAlarmConfig({
                show: false,
                msg: '',
                variant: 'success',
              });
            }}
            variant={addRepoAlarmConfig.variant}
          />
        </div>
      ) : (
        <></>
      )}
      <div
        className="flex-row flex-wrap align-center"
        style={{ marginTop: '0.7rem' }}
      >
        {renderRepoHistory()}
      </div>

      <GFIOverlay
        className="gfi-portal-overlay"
        callback={() => setShowPopover(false)}
        hidden={!showPopover}
        ref={overlayRef}
        width={isMobile ? '90%' : '40%'}
        id="gfi-portal-overlay"
        direction="right"
        animation
      >
        {addedRepoDisplayPanelConfig && (
          <GFIRepoDisplayView
            className="gfi-portal-overlay-panel"
            key={`added-repo-panel-${addedRepoDisplayPanelConfig.owner}-${addedRepoDisplayPanelConfig.name}`}
            repoInfo={addedRepoDisplayPanelConfig}
            tags={['Settings', 'GFI', 'Repo Data']}
            panels={[
              <RepoSetting repoInfo={addedRepoDisplayPanelConfig} key={1} />,
              <GFIIssueMonitor
                repoInfo={addedRepoDisplayPanelConfig}
                key={2}
              />,
              <GFIRepoStaticsDemonstrator
                repoInfo={addedRepoDisplayPanelConfig}
                paging={false}
                key={3}
              />,
            ]}
            style={{
              marginBottom: '0.5rem',
              transition: '0.2s',
              display: showPopover ? '' : 'none',
            }}
            ref={repoInfoPanelRef}
          />
        )}
      </GFIOverlay>
      <div className="account-page-panel-title project-add-comp-tutorial">
        Tutorial
      </div>
      <div className="account-page-panel-tutorial">
        <p> To Be Completed. </p>
        <p>
          {' '}
          We describe our envisioned use cases for GFI-Bot in this{' '}
          <a href="https://github.com/osslab-pku/gfi-bot/blob/main/USE_CASES.md">
            documentation
          </a>
          .{' '}
        </p>
      </div>
    </div>
  );
}

function RepoHistoryTag(props: {
  pending: boolean;
  repoInfo: RepoBrief;
  available: boolean;
  onClick?: (repoInfo: RepoBrief) => void;
}) {
  const { pending, repoInfo, available, onClick } = props;
  const isPending = available
    ? pending
      ? 'query-pending'
      : 'query-succeed'
    : 'query-none';
  const stateMsg = available ? (pending ? 'Pending' : 'Succeed') : '';
  return (
    <div
      className={`repo-history-tag ${isPending} hoverable`}
      onClick={() => {
        if (onClick) {
          onClick(repoInfo);
        }
      }}
    >
      <div>
        {' '}
        {repoInfo.owner} {available ? '|' : ''} {stateMsg}{' '}
      </div>
      <div> {repoInfo.name} </div>
    </div>
  );
}
