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
import KeepAlive from 'react-activation';

import { gsap } from 'gsap';

import '../../style/gfiStyle.css';
import { useDispatch, useSelector } from 'react-redux';
import {
  createAccountNavStateAction,
  createGlobalProgressBarAction,
} from '../../module/storage/reducers';
import { GFIRootReducers } from '../../module/storage/configureStorage';
import { checkIsGitRepoURL } from '../../utils';

import importTips from '../../assets/git-add-demo.png';
import { checkHasRepoPermissions } from '../../api/githubApi';
import { GFIAlarm, GFIAlarmPanelVariants } from '../GFIComponents';
import { addRepoToGFIBot, getAddRepoHistory } from '../../api/api';
import {
  GFIRepoInfo,
  GFIUserSearchHistoryItem,
} from '../../module/data/dataModel';
import {
  GFIIssueMonitor,
  GFIRepoDisplayView,
  GFIRepoStaticsDemonstrator,
} from '../main/GFIRepoDisplayView';
import { GFIRepoSearchingFilterType } from '../main/mainHeader';

export interface GFIPortal {}

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
      return <></>;
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

  const [addedRepos, setAddedRepos] = useState<GFIUserSearchHistoryItem[]>();
  const fetchAddedRepos = (onComplete?: () => void) => {
    getAddRepoHistory().then((res) => {
      const finishedQueries: GFIUserSearchHistoryItem[] | undefined =
        res?.finished_queries?.map((info) => {
          return {
            pending: false,
            repo: info,
          };
        });
      const pendingQueries: GFIUserSearchHistoryItem[] | undefined =
        res?.queries?.map((info) => {
          return {
            pending: true,
            repo: info,
          };
        });

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
    });
  };

  useEffect(() => {
    fetchAddedRepos();
  }, []);

  const [intervalID, setIntervalId] = useState<NodeJS.Timeout>();
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
  }, [addedRepos]);

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
    useState<{
      show: boolean;
      info?: GFIRepoInfo;
    }>({ show: false });

  type FilterType = GFIRepoSearchingFilterType;
  const [filterSelected, setFilterSelected] = useState<FilterType>('None');
  const filters: FilterType[] = [
    'None',
    'Popularity',
    'Activity',
    'Recommended',
    'Time',
  ];

  const onRepoHistoryClicked = (repoInfo: GFIRepoInfo) => {
    if (repoInfo !== addedRepoDisplayPanelConfig.info) {
      setAddedRepoDisplayPanelConfig({
        show: true,
        info: repoInfo,
      });
    } else {
      setAddedRepoDisplayPanelConfig({
        show: !addedRepoDisplayPanelConfig.show,
        info: repoInfo,
      });
    }
  };

  const renderRepoHistory = () => {
    if (addedRepos) {
      return addedRepos.map((item) => {
        return (
          <RepoHistoryTag
            pending={item.pending}
            repoInfo={item.repo}
            available
            onClick={item.pending ? () => {} : onRepoHistoryClicked}
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
        }}
        available={false}
      />
    );
  };

  const onFilterSelected = (filter: FilterType) => {
    setFilterSelected(filter);
  };

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
          <strong>Notice: </strong> We'll register the repository to our
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
                  // @ts-ignore
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
      {addedRepoDisplayPanelConfig.info && (
        <GFIRepoDisplayView
          key={`added-repo-panel-${addedRepoDisplayPanelConfig.info.owner}-${addedRepoDisplayPanelConfig.info.name}`}
          repoInfo={addedRepoDisplayPanelConfig.info}
          tags={['GFI', 'Repo Data']}
          panels={[
            <GFIIssueMonitor repoInfo={addedRepoDisplayPanelConfig.info} />,
            <GFIRepoStaticsDemonstrator
              repoInfo={addedRepoDisplayPanelConfig.info}
            />,
          ]}
          style={{
            border: '1px solid var(--color-border-default)',
            borderRadius: '7px',
            marginBottom: '0.5rem',
            transition: '0.2s',
            display: addedRepoDisplayPanelConfig.show ? '' : 'none',
          }}
          ref={repoInfoPanelRef}
        />
      )}
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
  repoInfo: GFIRepoInfo;
  available: boolean;
  onClick?: (repoInfo: GFIRepoInfo) => void;
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
