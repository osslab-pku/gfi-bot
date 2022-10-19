import React, {
  forwardRef,
  MouseEventHandler,
  useEffect,
  useState,
} from 'react';
import { Container, Col, Form, Button, Dropdown } from 'react-bootstrap';
import { SearchOutlined } from '@ant-design/icons';

import './mainPage.css';
import '../../style/gfiStyle.css';
import { useSelector } from 'react-redux';
import { getLanguageTags } from '../../api/api';
import { GFIRootReducers } from '../../storage/configureStorage';
import { MainPageLangTagSelectedState } from '../../storage/reducers';

export type GFIRepoSearchingFilterType =
  | 'Alphabetical'
  | 'Number of Stars'
  | 'Issue Resolution Time'
  | '% of Issues Resolved by New Contributors'
  | '# of Predicted Good First Issues';

export const GFI_REPO_FILTER_NONE: GFIRepoSearchingFilterType & string = 'Alphabetical';

export interface GFIMainPageHeader {
  onSearch?: (s: string) => void;
  onFilterSelect?: (s: GFIRepoSearchingFilterType) => void;
  onTagSelected?: (s: string) => void;
}

export const GFIMainPageHeader = forwardRef((props: GFIMainPageHeader, ref) => {
  const { onSearch, onFilterSelect, onTagSelected } = props;

  const [search, setSearch] = useState<string | undefined>();
  const [filterSelected, setFilterSelected] =
    useState<GFIRepoSearchingFilterType>('Alphabetical');

  const sortedBy: GFIRepoSearchingFilterType[] = [
    'Alphabetical',
    'Number of Stars',
    'Issue Resolution Time',
    '% of Issues Resolved by New Contributors',
    '# of Predicted Good First Issues',
  ];

  const renderDropDownItem = (
    onClick: MouseEventHandler<HTMLElement>,
    title: string
  ) => {
    return (
      <Dropdown.Item
        onClick={onClick}
        style={{
          fontSize: 'small',
        }}
        key={title}
      >
        {title}
      </Dropdown.Item>
    );
  };

  const renderDefaultDropDownItems = () => {
    return sortedBy.map((value, index, array) => {
      return renderDropDownItem((e) => {
        setFilterSelected(value);
        if (onFilterSelect) {
          onFilterSelect(value);
        }
      }, value as string);
    });
  };

  const [tagArray, setTagArray] = useState<string[]>(['All']);
  const [tagSelected, setTagSelected] = useState('All');
  useEffect(() => {
    getLanguageTags().then((res) => {
      if (res) {
        setTagArray(['All', ...res]);
      }
    });
  }, []);

  const globalSelectedTag = useSelector<
    GFIRootReducers,
    MainPageLangTagSelectedState
  >((state) => {
    return state.mainPageLangTagSelectedStateReducer;
  });

  useEffect(() => {
    if (
      globalSelectedTag &&
      globalSelectedTag.tagSelected &&
      tagArray.includes(globalSelectedTag.tagSelected)
    ) {
      setTagSelected(globalSelectedTag.tagSelected);
    }
  }, [globalSelectedTag]);

  const renderTagMenu = () => {
    return tagArray.map((value, index, array) => {
      return renderDropDownItem((e) => {
        setTagSelected(value);
        if (onTagSelected) {
          onTagSelected(value);
        }
      }, value);
    });
  };

  return (
    <Container className="main-header-container flex-wrap flex-col">
      <div
        className="flex-row align-center full warp"
        id="main-header-container-wrapper"
      >
        <Col className="flex-row" style={{ padding: '0' }}>
          <div className="flex-col full wrap">
            <div className="flex-row">
              <Form className="main-header-input">
                <Form.Control
                  className="main-header-form main-header-input-text"
                  placeholder="GitHub URL or Repo Name"
                  aria-describedby="append-icon"
                  onChange={(e) => {
                    setSearch(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (search && onSearch) {
                        onSearch(search);
                      }
                    }
                  }}
                />
              </Form>
              <Button
                className="flex-row flex-center main-header-search"
                onClick={() => {
                  if (search && onSearch) {
                    onSearch(search);
                  }
                }}
              >
                <SearchOutlined />
              </Button>
            </div>
            <div
              className="flex-row align-center"
              style={{
                marginTop: '0.5rem',
              }}
            >
              <div className="flex-row align-center">
                <div className="main-dropdown-tags">Sort by</div>
                <Dropdown
                  style={{
                    marginRight: '1rem',
                  }}
                >
                  <Dropdown.Toggle
                    variant="light"
                    className="main-header-dropdown"
                  >
                    {filterSelected}
                  </Dropdown.Toggle>
                  <Dropdown.Menu
                    variant="dark"
                    style={{
                      minWidth: '7rem',
                    }}
                  >
                    {renderDefaultDropDownItems()}
                  </Dropdown.Menu>
                </Dropdown>
              </div>

              <div className="flex-row align-center">
                <div className="main-dropdown-tags">Language</div>
                <Dropdown>
                  <Dropdown.Toggle
                    variant="light"
                    className="main-header-dropdown"
                  >
                    {tagSelected}
                  </Dropdown.Toggle>
                  <Dropdown.Menu
                    variant="dark"
                    style={{
                      minWidth: '7rem',
                    }}
                  >
                    {renderTagMenu()}
                  </Dropdown.Menu>
                </Dropdown>
              </div>
            </div>
          </div>
        </Col>
      </div>
    </Container>
  );
});

GFIMainPageHeader.displayName = 'GFIMainPageHeader';
