import React from 'react'
import {
	GFIIssueMonitor,
	GFIRepoDisplayView,
} from '../../pages/main/GFIRepoDisplayView'
import { GFIRepoInfo } from './dataModel'
import { Repositories } from '../../pages/repositories/repositories'

export const MockedRepoInfo: GFIRepoInfo = {
	name: 'scikit-learn',
	owner: 'scikit-learn',
	description: 'scikit-learn: machine learning in Python',
	topics: ['python', 'data-science', 'machine-learning'],
}
