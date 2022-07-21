import React from 'react';
import {
  GFIIssueMonitor,
  GFIRepoDisplayView,
} from '../../pages/main/GFIRepoDisplayView';
import { Repositories } from '../../pages/repositories/repositories';
import {RepoBrief} from "../api";

export const MockedRepoInfo: RepoBrief = {
  name: 'scikit-learn',
  owner: 'scikit-learn',
  language: 'Python',
  description: 'scikit-learn: machine learning in Python',
  topics: ['python', 'data-science', 'machine-learning'],
};
