import { GFIRepoSearchingFilterType } from './pages/main/mainHeader';
import { RepoSort } from './model/api';

export const checkIsNumber = (val: string | number | undefined) => {
  const reg = /^\d+.?\d*/;
  if (typeof val === 'number') {
    val = val.toString();
  }
  if (val) {
    return reg.test(val);
  }
  return false;
};

export const checkIsPercentage = (val: string) => {
  return /^\d+(\.\d+)?%$/.test(val);
};

// export const checkIsGitRepoURL = (val: string) => {
//   const isGitUrl = require('is-git-url');
//   return isGitUrl(val);
// };

// ↑ above shouldn't work with browsers
export const checkIsGitRepoURL = (val: string) => {
  return /((git|ssh|http(s)?)|(git@[\w\.]+))(:(\/\/)?)([\w\.@\:/\-~]+)(\.git)?(\/)?/.test(
    val
  );
};

export const defaultFontFamily =
  '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen,Ubuntu,Cantarell,Fira Sans,Droid Sans,Helvetica Neue,sans-serif';

export const monospaceFontFamily = 'Consolas, monaco, monospace';

export const checkHasUndefinedProperty = (obj: any) => {
  for (const key in obj) {
    if (obj[key] === undefined) return true;
  }
  return false;
};

const filterNames = {
  'popularity': 'Number of Stars',
  'median_issue_resolve_time': 'Issue Resolution Time',
  'newcomer_friendly': '% of Issues Resolved by New Contributors',
  'gfis': '# of Predicted Good First Issues',
};

const nameToFilter = Object.keys(filterNames).reduce((acc, cur) => {
  acc[filterNames[cur]] = cur;
  return acc;
}, {} as { [key: string]: string });

/** convert semantic filter names -> backend args */
export const convertFilter = (s: string): RepoSort | undefined => {
  if (Object.keys(filterNames).includes(s)) {
    return s as RepoSort;
  } else if (Object.keys(nameToFilter).includes(s)) {
    return nameToFilter[s] as RepoSort;
  } else {
    console.error('invalid filter name', s, nameToFilter, filterNames);
    return undefined;
  }
};

export const checkIsValidUrl = (url: string) => {
  try {
    return Boolean(new URL(url));
  } catch (e) {
    return false;
  }
};
