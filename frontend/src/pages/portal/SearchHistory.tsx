import React, { useEffect, useRef, useState } from 'react';

import { ListGroup } from 'react-bootstrap';
import { DeleteOutlined } from '@ant-design/icons';
import type { RepoBrief, SearchedRepo } from '../../model/api';
import { deleteUserSearch, getRepoInfo, getUserSearches } from '../../api/api';

import '../../style/gfiStyle.css';
import {
  GFIIssueMonitor,
  GFIRepoDisplayView,
  GFIRepoStaticsDemonstrator,
} from '../main/GFIRepoDisplayView';
import { GFIOverlay } from '../GFIComponents';
import { useIsMobile } from '../app/windowContext';

export function SearchHistory() {
  const [searchHistory, setSearchHistory] = useState<SearchedRepo[]>();
  const [showPopover, setShowPopover] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  const setSearchRes = (res: SearchedRepo[]) => {
    const res_reversed = res.reverse();
    setSearchHistory(res_reversed);
    setSelectedList(res_reversed.map((_, idx) => !idx));
  };

  useEffect(() => {
    getUserSearches().then((res) => {
      if (res) {
        setSearchRes(res);
      }
    });
  }, []);

  const [selectedList, setSelectedList] = useState<boolean[]>();
  const [repoDisplay, setRepoDisplay] = useState<RepoBrief>();

  const onItemClicked = (name: string, owner: string, idx: number) => {
    if (repoDisplay?.name !== name || repoDisplay?.owner !== owner) {
      getRepoInfo(name, owner).then((res) => {
        if (res) {
          setRepoDisplay(res);
          setShowPopover(true);
        }
      });
    } else if (repoDisplay) {
      setShowPopover(true);
    }
    setSelectedList(selectedList?.map((item, i) => i === idx));
  };

  const deleteSearch = (name: string, owner: string, id: number) => {
    deleteUserSearch(name, owner, id).then((res) => {
      if (res) {
        setSearchRes(res);
      }
    });
  };

  const render = () => {
    if (searchHistory && selectedList) {
      return searchHistory.map((item, idx) => {
        let numTag = '';
        if (!idx) {
          numTag += ' gfi-list-first';
        }
        if (idx === searchHistory.length - 1) {
          numTag += ' gfi-list-last';
        }
        return (
          <div className="flex-row align-center" key={idx}>
            <ListGroup.Item
              className={`gfi-search-history-item-wrapper ${numTag}`}
              id={`gfi-search-history-item-${item.owner}-${item.name}-${idx}`}
              action
              as="button"
              variant={selectedList[idx] ? 'primary' : 'light'}
              onClick={() => {
                onItemClicked(item.name, item.owner, idx);
              }}
            >
              <div className="gfi-search-history-item flex-row">
                <div className="flex-row">
                  <div> {item.owner} </div>
                  <div> {' / '} </div>
                  <div style={{ fontWeight: 'bold' }}> {item.name} </div>
                </div>
                <div>{item.created_at}</div>
              </div>
            </ListGroup.Item>
            <DeleteOutlined
              style={{ fontSize: '120%', marginLeft: '0.7rem' }}
              className="hoverable"
              onClick={() => {
                deleteSearch(item.name, item.owner, item.increment);
              }}
            />
          </div>
        );
      });
    }
  };

  return (
    <>
      <ListGroup className="gfi-search-history-container">
        {searchHistory && render()}
      </ListGroup>
      <GFIOverlay
        className="gfi-search-history-overlay"
        callback={() => setShowPopover(false)}
        hidden={!showPopover}
        ref={overlayRef}
        width={isMobile ? '90%' : '40%'}
        id="gfi-search-history-overlay"
        direction="right"
        animation
      >
        {repoDisplay && (
          <GFIRepoDisplayView
            className="gfi-portal-overlay-panel"
            key={`added-repo-panel-${repoDisplay.owner}-${repoDisplay.name}`}
            repoInfo={repoDisplay}
            tags={['GFI', 'Repo Data']}
            panels={[
              <GFIIssueMonitor repoInfo={repoDisplay} paging={14} key={1} />,
              <GFIRepoStaticsDemonstrator
                repoInfo={repoDisplay}
                paging={false}
                key={2}
              />,
            ]}
            style={{
              marginBottom: '0.5rem',
              transition: '0.2s',
              display: showPopover ? '' : 'none',
            }}
          />
        )}
      </GFIOverlay>
    </>
  );
}
