import { GFIRepoSearchingFilterType } from './pages/main/mainHeader';

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

const repoFilters = [
  'popularity',
  'median_issue_resolve_time',
  'newcomer_friendly',
  'gfis',
];

export const convertFilter = (filter: string | undefined) => {
  let filterConverted: string | undefined;
  if (filter) {
    switch (filter as GFIRepoSearchingFilterType) {
      case 'Popularity':
        filterConverted = repoFilters[0];
        break;
      case 'Median Issue Resolve Time':
        filterConverted = repoFilters[1];
        break;
      case 'Newcomer Friendliness':
        filterConverted = repoFilters[2];
        break;
      case 'GFIs':
        filterConverted = repoFilters[3];
        break;
      default:
        break;
    }
  }
  return filterConverted;
};

export const checkIsValidUrl = (url: string) => {
  try {
    return Boolean(new URL(url));
  } catch (e) {
    return false;
  }
};
