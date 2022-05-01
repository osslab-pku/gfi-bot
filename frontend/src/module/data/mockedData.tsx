import React from 'react';
import {GFIIssueMonitor, GFIRepoDisplayView} from '../../pages/main/GFIRepoDisplayView';
import {GFIRepoInfo} from './dataModel';
import {Repositories} from '../../pages/repositories/repositories';

export const MockedRepoInfo: GFIRepoInfo = {
	name: 'scikit-learn',
	owner: 'scikit-learn',
	description: 'scikit-learn: machine learning in Python',
	topics: ['python', 'data-science', 'machine-learning'],
}

export const MockedGFIList = [1354, 4006, 13315, 12018, 23253, 23231]

export const MockedGFIIssueMonitorProp: GFIIssueMonitor = {
	repoInfo: MockedRepoInfo,
	issueList: MockedGFIList,
}

export const MockedDisplayViewProp: GFIRepoDisplayView = {
	repoInfo: MockedRepoInfo,
	tags: ['GFI', 'Repo Data'],
	panels: [
		<GFIIssueMonitor repoInfo={MockedRepoInfo} issueList={MockedGFIList} />,
		<div> Hello World </div>,
	],
}