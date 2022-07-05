import React, {
  createContext,
  ForwardedRef,
  forwardRef,
  MouseEventHandler,
  ReactElement,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Row, Col } from 'react-bootstrap';
import { useDispatch, useSelector } from 'react-redux';

import remarkGfm from 'remark-gfm';
import remarkGemoji from 'remark-gemoji';
import ReactMarkdown from 'react-markdown';

import '../../style/gfiStyle.css';
import {
  GFIOverlay,
  GFIPagination,
  GFISimplePagination,
} from '../GFIComponents';
import {
  GFIInfo,
  GFIRepoInfo,
  GetRepoDetailedInfo,
  GFITrainingSummary,
} from '../../module/data/dataModel';
import { getIssueByRepoInfo } from '../../api/githubApi';
import { GFIRootReducers } from '../../module/storage/configureStorage';
import { createPopoverAction } from '../../module/storage/reducers';
import {
  getGFIByRepoName,
  getRepoDetailedInfo,
  getTrainingSummary,
} from '../../api/api';
import { useIsMobile } from '../app/windowContext';
import { RepoGraphContainer } from '../repositories/repoDataDemonstrator';
import { checkHasUndefinedProperty, checkIsNumber } from '../../utils';

export interface RepoShouldDisplayPopoverState {
  shouldDisplayPopover?: boolean;
  popoverComponent?: ReactElement;
  popoverID?: string;
}

export interface GFIRepoBasicProp {
  repoInfo: GFIRepoInfo;
}

export interface GFIRepoDisplayView extends GFIRepoBasicProp {
  tags?: string[];
  panels?: ReactElement[];
  style?: any;
  className?: string;
}

const RepoDisplayOverlayIDContext = createContext<string>({} as any);

const RepoDisplayOverlayIDProvider: React.FC<{
  children: React.ReactNode;
  id: string;
}> = ({ children, id }) => {
  return (
    <RepoDisplayOverlayIDContext.Provider value={id}>
      {children}
    </RepoDisplayOverlayIDContext.Provider>
  );
};

const useOverlayID = () => {
  return useContext(RepoDisplayOverlayIDContext);
};

export const GFIRepoDisplayView = forwardRef(
  (props: GFIRepoDisplayView, ref: ForwardedRef<HTMLDivElement>) => {
    const { repoInfo, tags, panels, style, className } = props;
    const [selectedTag, setSelectedTag] = useState<number>(0);
    const [selectedTagList, setSelectedTagList] = useState<boolean[]>();

    // Not good, but 'position: fixed' in child components doesn't work here
    // wondering why...
    const overlayItem = useSelector<
      GFIRootReducers,
      RepoShouldDisplayPopoverState | undefined
    >((state) => {
      return state.mainPopoverReducer;
    });
    const overlayRef = useRef<HTMLDivElement>(null);
    const dispatch = useDispatch();
    const overlayID = `main-overlay-${repoInfo.name}-${repoInfo.owner}`;

    const isMobile = useIsMobile();

    useEffect(() => {
      if (tags) {
        setSelectedTagList(
          tags.map((_, i) => {
            return !i;
          })
        );
      }
    }, []);

    function Info() {
      if (panels && tags && panels.length === tags.length) {
        return panels.map((node, i) => {
          return (
            <div
              className="flex-col"
              style={i === selectedTag ? {} : { display: 'none' }}
            >
              <RepoDisplayOverlayIDProvider id={overlayID}>
                {node}
              </RepoDisplayOverlayIDProvider>
            </div>
          );
        });
      }
      return <></>;
    }

    function Title() {
      const ProjectTags = () => {
        return repoInfo.topics?.map((item, i) => {
          return <div className="repo-display-info-repo-tag">{item}</div>;
        });
      };

      return (
        <div className="flex-col justify-content-center repo-display-info flex-wrap">
          <div className="repo-display-info-title flex-row">
            <p> {repoInfo.owner} </p>
            <p> {' / '} </p>
            <p> {repoInfo.name} </p>
          </div>
          <div> {repoInfo?.description} </div>
          <div className="flex-row flex-wrap"> {ProjectTags()} </div>
        </div>
      );
    }

    function Tags() {
      if (tags && selectedTagList?.length === tags.length) {
        return tags.map((item, i) => {
          return (
            <PanelTag
              name={item}
              id={i}
              onClick={(id) => {
                if (id !== selectedTag) {
                  setSelectedTag(id);
                  setSelectedTagList(
                    tags?.map((_, i) => {
                      return i === id;
                    })
                  );
                }
              }}
              selected={selectedTagList[i]}
            />
          );
        });
      }
      return <></>;
    }

    const renderOverlay = () => {
      let hidden = !(overlayItem && overlayItem.shouldDisplayPopover);
      if (overlayItem?.popoverID !== overlayID) {
        hidden = true;
      }
      return (
        <GFIOverlay
          id={overlayID}
          direction="right"
          width={isMobile ? '90%' : '60%'}
          hidden={hidden}
          ref={overlayRef}
          callback={() => {
            dispatch(createPopoverAction());
          }}
          animation
        >
          {overlayItem?.popoverComponent}
        </GFIOverlay>
      );
    };

    return (
      <div className="repo-display-view-container" ref={ref}>
        {renderOverlay()}
        <div style={style} className={`flex-col repo-display ${className}`}>
          <div className="flex-row repo-display-info-nav">{Tags()}</div>
          <Row>
            <Col>
              {Title()}
              {Info()}
            </Col>
          </Row>
        </div>
      </div>
    );
  }
);

function PanelTag(props: {
  name: string;
  id: number;
  selected: boolean;
  onClick: (id: number) => void;
}) {
  const { name, id, selected, onClick } = props;
  const selectedClass = selected ? 'selected' : '';
  const first = id === 0 ? 'first' : '';
  const className =
    'repo-display-info-panel-tag flex-row align-items-stretch align-center' +
    ` ${selectedClass}` +
    ` ${first}`;

  return (
    <div className={className}>
      <div
        className={
          'repo-display-info-tag flex-row flex-center hoverable' +
          ` ${selectedClass}`
        }
        onClick={() => {
          onClick(id);
        }}
      >
        {' '}
        <p className="no-select"> {name} </p>
      </div>
    </div>
  );
}

export interface GFIIssueMonitor extends GFIRepoBasicProp {
  trainingSummary?: GFITrainingSummary;
  paging?: number;
}

export const GFIIssueMonitor = forwardRef((props: GFIIssueMonitor, ref) => {
  const { repoInfo, trainingSummary, paging } = props;
  const [displayIssueList, setDisplayIssueList] = useState<
    GFIInfo[] | undefined
  >();
  const maxPageItems = paging || 6;
  const [shouldDisplayPagination, setShouldDisplayPagination] = useState(false);
  const [currentPageIdx, setCurrentPageIdx] = useState(1);
  const [pageInput, setPageInput] = useState<string>();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!displayIssueList) {
      getGFIByRepoName(repoInfo.name, repoInfo.owner).then((res) => {
        if (Array.isArray(res) && res.length) {
          setDisplayIssueList(res);
          setShouldDisplayPagination(res.length > maxPageItems);
        } else {
          setDisplayIssueList(undefined);
          setIsLoading(false);
        }
      });
    }
  }, [repoInfo]);

  const render = () => {
    const pageLowerBound = (currentPageIdx - 1) * maxPageItems;
    const pageUpperBound = currentPageIdx * maxPageItems;
    return displayIssueList?.map((issue, i) => {
      if (pageLowerBound <= i && i < pageUpperBound) {
        return (
          <GFIIssueListItem
            repoInfo={repoInfo}
            issue={issue}
            key={`gfi-issue-${repoInfo.name}-${issue}-${i}`}
            useTips={!(i % maxPageItems)}
            trainingSummary={trainingSummary}
          />
        );
      }
      return <></>;
    });
  };

  return (
    <div className="flex-col">
      {render()}
      {displayIssueList ? (
        <></>
      ) : (
        <div className="gfi-issue-monitor-empty">
          {isLoading
            ? 'Loading GFIs...'
            : 'Currently no GFIs for this repository.'}
        </div>
      )}
      {shouldDisplayPagination && displayIssueList && (
        <div
          style={{
            marginRight: '0.7rem',
            marginLeft: '0.7rem',
            marginBottom: '0.3rem',
          }}
        >
          <GFIPagination
            maxPagingCount={3}
            pageNums={Math.ceil(displayIssueList.length / maxPageItems)}
            pageIdx={currentPageIdx}
            toPage={(page) => setCurrentPageIdx(page)}
            needInputArea
            onFormInput={(target) => {
              const t = target as HTMLTextAreaElement;
              setPageInput(t.value);
            }}
            onPageBtnClicked={() => {
              if (pageInput && checkIsNumber(pageInput)) {
                const page = parseInt(pageInput);
                if (
                  page > 0 &&
                  page <= Math.ceil(displayIssueList.length / maxPageItems)
                ) {
                  setCurrentPageIdx(parseInt(pageInput));
                }
              }
            }}
          />
        </div>
      )}
    </div>
  );
});

export interface GFIIssueListItem extends GFIRepoBasicProp {
  issue: GFIInfo;
  useTips: boolean;
  trainingSummary?: GFITrainingSummary;
}

type IssueState = 'closed' | 'open' | 'resolved';
interface IssueDisplayData {
  issueId: number;
  title: string;
  body: string;
  state: IssueState;
  url: string;
  gfi: GFIInfo;
}

function GFIIssueListItem(props: GFIIssueListItem) {
  const dispatch = useDispatch();
  const overlayID = useOverlayID();
  const { repoInfo, issue, useTips, trainingSummary } = props;
  const [displayData, setDisplayData] = useState<IssueDisplayData>();

  useEffect(() => {
    getIssueByRepoInfo(repoInfo.name, repoInfo.owner, issue.number).then(
      (res) => {
        if (res && res.status === 200) {
          if (res.data && !checkHasUndefinedProperty(res.data)) {
            let issueState = 'open';
            if (res.data.state === 'closed') {
              issueState = 'closed';
            }
            if (res.data.active_lock_reason === 'resolved') {
              issueState = 'resolved';
            }
            setDisplayData({
              issueId: res.data.number as number,
              title: res.data.title as string,
              body: res.data.body as string,
              state: issueState as IssueState,
              url: res.data.html_url as string,
              gfi: issue,
            });
          }
        } else {
        }
      }
    );
  }, []);

  const issueBtn = () => {
    return (
      <button
        className={`issue-display-item-btn ${
          displayData ? displayData.state : ''
        }`}
      >
        <a href={displayData ? displayData.url : ''}>{`#${issue.number}`}</a>
      </button>
    );
  };

  const onDetailShow: MouseEventHandler<HTMLDivElement> = (e) => {
    const callbackProp: RepoShouldDisplayPopoverState = {
      shouldDisplayPopover: true,
      popoverComponent: (
        <IssueOverlayItem
          repoInfo={repoInfo}
          issueBtn={issueBtn}
          displayData={displayData}
          trainingSummary={trainingSummary}
        />
      ),
      popoverID: overlayID,
    };
    dispatch(createPopoverAction(callbackProp));
  };

  return (
    <div
      className="issue-display-item flex-row align-center hoverable"
      onClick={onDetailShow}
    >
      <div
        style={{
          width: '9%',
          minWidth: '70px',
        }}
      >
        {issueBtn()}
      </div>
      <div className="flex-row flex-wrap text-break">
        {displayData ? displayData.title : ''}
      </div>
      {displayData && (
        <div
          style={{
            width: '6%',
            minWidth: '65px',
            marginLeft: 'auto',
            paddingLeft: '0.3rem',
          }}
          className="flex-row justify-content-center align-center"
        >
          <div
            className={`issue-display-item-prob-tag ${
              useTips ? 'tool-tips' : ''
            }`}
          >
            {`${(issue.probability * 100).toFixed(2)}%`}
            {useTips && (
              <div className="tool-tips-text-top flex-row align-center justify-content-center">
                GFI Probability
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface IssueOverlayItem extends GFIRepoBasicProp {
  issueBtn: () => ReactElement;
  displayData?: IssueDisplayData;
  trainingSummary?: GFITrainingSummary;
}

function IssueOverlayItem(props: IssueOverlayItem) {
  const { repoInfo, issueBtn, displayData, trainingSummary } = props;
  const isMobile = useIsMobile();
  const flexDirection = isMobile ? 'col' : 'row';
  const probability = displayData
    ? (displayData.gfi.probability * 100).toFixed(2)
    : 0;
  const simpleTrainDataProps: SimpleTrainInfoTagProp[] | [] = trainingSummary
    ? [
        {
          title: 'Issues Resolved',
          data: trainingSummary.n_resolved_issues,
        },
        {
          title: 'Resolved By Newcomers',
          data: trainingSummary.n_newcomer_resolved,
        },
        {
          title: 'AUC',
          data: trainingSummary.auc
            ? parseFloat(trainingSummary.auc.toFixed(2))
            : 0,
        },
        {
          title: 'ACC',
          data: trainingSummary.auc
            ? parseFloat(trainingSummary.auc.toFixed(2))
            : 0,
        },
      ]
    : [];

  return (
    <div
      className="flex-col repo-overlay-item"
      style={{
        margin: '1rem 1.5rem',
      }}
    >
      <div className="gfi-overlay-info-title">
        <div className={`repo-display-info-title flex-${flexDirection}`}>
          <p> {repoInfo.owner} </p>
          {!isMobile && <p> {' / '} </p>}
          <p style={{ margin: '0' }}> {repoInfo.name} </p>
        </div>
        <div style={{ fontFamily: 'var(--default-font-family)' }}>
          {repoInfo?.description}
        </div>
        <div
          className="flex-row align-center justify-content-start flex-wrap"
          style={{ marginBottom: '0.2rem' }}
        >
          {repoInfo.topics?.map((item) => (
            <div className="repo-display-info-repo-tag">{item}</div>
          ))}
        </div>
        {simpleTrainDataProps && (
          <div className="flex-row issue-demo-data-container-overlay">
            {simpleTrainDataProps.map((prop) => (
              <SimpleTrainInfoTag title={prop.title} data={prop.data} />
            ))}
          </div>
        )}
      </div>
      <div
        className="flex-row align-center"
        style={{
          margin: '1rem 0',
        }}
      >
        {issueBtn()}
        <div
          style={{
            fontWeight: 'bold',
            fontSize: 'larger',
            marginLeft: '0.7rem',
          }}
        >
          {displayData?.title}
        </div>
        <div className="gfi-issue-overlay-item-tag">
          Probability {`${probability}%`}
        </div>
      </div>
      {displayData && displayData.body && (
        <ReactMarkdown
          children={displayData.body}
          remarkPlugins={[remarkGfm, remarkGemoji]}
          className="markdown markdown-gfi-overlay"
        />
      )}
    </div>
  );
}

export interface GFIRepoStaticsDemonstrator extends GFIRepoBasicProp {
  trainingSummary?: GFITrainingSummary;
  paging?: boolean;
}

export const GFIRepoStaticsDemonstrator = forwardRef(
  (props: GFIRepoStaticsDemonstrator, ref) => {
    const { repoInfo, trainingSummary, paging } = props;
    const usePaging = !(paging === false && paging !== undefined);
    const [displayInfo, setDisplayInfo] = useState<GetRepoDetailedInfo>();
    const simpleTrainDataProps: SimpleTrainInfoTagProp[] | [] = trainingSummary
      ? [
          {
            title: 'Issues Resolved',
            data: trainingSummary.n_resolved_issues,
          },
          {
            title: 'Resolved By Newcomers',
            data: trainingSummary.n_newcomer_resolved,
          },
          {
            title: 'AUC',
            data: trainingSummary.auc
              ? parseFloat(trainingSummary.auc.toFixed(2))
              : 0,
          },
          {
            title: 'ACC',
            data: trainingSummary.auc
              ? parseFloat(trainingSummary.accuracy.toFixed(2))
              : 0,
          },
        ]
      : [];

    type DataTag =
      | 'monthly_stars'
      | 'monthly_commits'
      | 'monthly_issues'
      | 'monthly_pulls';
    type DisplayData = { [key in DataTag]?: any[] };
    const [displayData, setDisplayData] = useState<DisplayData>();
    const dataCategories = [
      'monthly_stars',
      'monthly_commits',
      'monthly_issues',
      'monthly_pulls',
    ];
    const dataTitle = [
      'Monthly Stars',
      'Monthly Commits',
      'Monthly Issues',
      'Monthly Pulls',
    ];
    const [title, setTitle] = useState<string[]>();
    const [selectedIdx, setSelectedIdx] = useState(0);

    useEffect(() => {
      getRepoDetailedInfo(repoInfo.name, repoInfo.owner).then((res) => {
        const result = res as GetRepoDetailedInfo;
        setDisplayInfo(result);
      });
    }, []);

    useEffect(() => {
      if (displayInfo) {
        const info: DisplayData = {};
        let key: keyof typeof displayInfo;
        const titles = [];
        for (key in displayInfo) {
          const displayInfoItem = displayInfo[key] as any[];
          if (dataCategories.includes(key) && displayInfoItem.length) {
            info[key as DataTag] = displayInfoItem;
            titles.push(dataTitle[dataCategories.indexOf(key)]);
          }
        }
        setTitle(titles);
        setDisplayData(info);
      }
    }, [displayInfo]);

    const RenderGraphs = () => {
      let availableIdx = -1;
      return dataCategories.map((item, idx) => {
        if (displayData && title && Object.keys(displayData).includes(item)) {
          availableIdx += 1;
          return (
            <div
              style={
                availableIdx === selectedIdx || !usePaging
                  ? {}
                  : { display: 'none' }
              }
            >
              <RepoGraphContainer
                title={dataTitle[idx]}
                info={displayData[item as DataTag]}
              />
            </div>
          );
        }
        return <></>;
      });
    };

    return (
      <>
        {simpleTrainDataProps && (
          <div className="flex-row issue-demo-data-container">
            {simpleTrainDataProps.map((prop) => (
              <SimpleTrainInfoTag title={prop.title} data={prop.data} />
            ))}
          </div>
        )}
        <div className="issue-demo-container">
          {RenderGraphs()}
          {usePaging && (
            <div className="flex-row page-footer-container">
              {displayData && Object.keys(displayData).length && (
                <GFISimplePagination
                  nums={Object.keys(displayData).length}
                  onClick={(idx) => {
                    setSelectedIdx(idx);
                  }}
                  title={title}
                />
              )}
            </div>
          )}
        </div>
      </>
    );
  }
);

interface SimpleTrainInfoTagProp {
  title: string;
  data: number;
}

function SimpleTrainInfoTag(props: SimpleTrainInfoTagProp) {
  const { title, data } = props;

  return (
    <div
      className="simple-train-info-tag flex-row align-items-stretch"
      style={{ marginRight: '0.4rem' }}
    >
      <div>{title}</div>
      <div>{data}</div>
    </div>
  );
}
