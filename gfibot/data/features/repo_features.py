"""
Repo-level feature computation logic.

This module contains pure functions for computing repository features
from collected GitHub data. These functions have no side effects, no
database operations, and no API calls.

Features computed:
- Issue number references from text (commit messages, PR descriptions)
- Issue resolution detection (which commit/PR resolved which issue)
- Repository statistics (median issue close time)
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, NamedTuple
from datetime import datetime, timedelta
from collections import defaultdict


class IssueResolution(NamedTuple):
    """Result of issue resolution detection."""
    owner: str
    name: str
    number: int
    created_at: datetime
    resolved_at: datetime
    resolver: Optional[str]
    resolved_in: Optional[str]  # commit SHA or PR number
    resolver_commit_num: Optional[int]  # commits by resolver before resolution
    events: List[Any]


def match_issue_references(text: str) -> List[int]:
    """
    Extract referenced issue numbers from text.
    
    Matches GitHub's documented issue closing keywords:
    - close, closes, closed
    - fix, fixes, fixed
    - resolve, resolves, resolved
    
    References: https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
    
    Args:
        text: Text to search (e.g., commit message, PR description)
        
    Returns:
        List of issue numbers found (empty if none)
        
    Examples:
        >>> match_issue_references("Fixes #123 and closes #456")
        [123, 456]
        >>> match_issue_references("This is a regular commit")
        []
    """
    numbers = []
    # Match closing keywords followed by one or more issue references
    regex = r"(close[sd]?|fix(es|ed)?|resolve[sd]?)\s+((?:#\d+(?:\s*,\s*)?)+)"
    for match in re.finditer(regex, text.lower()):
        # Extract all issue numbers from the matched reference group
        issue_refs = re.findall(r"#(\d+)", match.group(3))
        numbers.extend(int(n) for n in issue_refs)
    return numbers


def compute_issue_close_time_median(issues: List[Any]) -> Optional[float]:
    """
    Compute median time to close issues.
    
    Args:
        issues: List of issue objects with:
            - state: 'open' or 'closed'
            - is_pull: True if pull request
            - created_at: datetime when created
            - closed_at: datetime when closed (None if open)
            
    Returns:
        Median close time in seconds, or None if no closed issues
        
    Examples:
        >>> class Issue:
        ...     def __init__(self, created, closed, state='closed', is_pull=False):
        ...         self.created_at = created
        ...         self.closed_at = closed
        ...         self.state = state
        ...         self.is_pull = is_pull
        >>> from datetime import datetime, timedelta
        >>> issues = [
        ...     Issue(datetime(2020, 1, 1), datetime(2020, 1, 2)),
        ...     Issue(datetime(2020, 2, 1), datetime(2020, 2, 3)),
        ... ]
        >>> median = compute_issue_close_time_median(issues)
        >>> median  # Between 86400 and 172800
        129600.0
    """
    closed_times = [
        (i.closed_at - i.created_at).total_seconds()
        for i in issues
        if i.state == "closed" and not i.is_pull and i.closed_at is not None
    ]
    
    if len(closed_times) == 0:
        return None
    
    return float(np.median(closed_times))


def detect_issue_resolutions(
    issues_dict: Dict[int, Any],
    commits_list: List[Any],
    prs_dict: Optional[Dict[int, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect which commits and PRs resolved which issues.
    
    Implements resolution detection with the following priority:
    1. Commits that reference issues (lower priority)
    2. PRs that reference issues (higher priority)
    
    Later commits/PRs take precedence (most recent resolver wins).
    
    Args:
        issues_dict: Dict[issue_number, issue_data]
            Required fields: number, created_at, closed_at
        commits_list: List of commits (sorted by authored_at)
            Required fields: sha, author, message, authored_at
        prs_dict: Optional dict[pr_number, pr_data] for PR-based resolution
            Required fields: number, user, title, body, comments, merged_at
            
    Returns:
        List of dicts with resolution info:
        {
            'owner': str,
            'name': str, 
            'number': int,
            'created_at': datetime,
            'resolved_at': datetime,
            'resolver': str,  # username
            'resolved_in': str,  # commit SHA or PR number
            'resolver_commit_num': int,  # commits by author before resolution
            'events': list
        }
        
    Note:
        This is a pure function - it doesn't read from DB or make API calls.
        Input data should be pre-fetched.
    """
    # Initialize resolution tracking
    resolutions = {}
    for issue_num in issues_dict.keys():
        resolutions[issue_num] = {
            "number": issue_num,
            "created_at": issues_dict[issue_num].created_at,
            "resolved_at": issues_dict[issue_num].closed_at,
            "resolver": None,
            "resolved_in": None,
            "resolver_commit_num": None,
            "events": [],
        }
    
    # Step 1: Detect resolutions via commits
    author_to_commits = defaultdict(list)
    for commit in commits_list:
        if commit.author:
            author_to_commits[commit.author].append(commit)
    
    closed_issue_numbers = set(issues_dict.keys())
    
    for commit in commits_list:
        if commit.author is None:
            continue
        
        # Count commits by this author before this commit
        commits_before = sum(
            1 for c in author_to_commits[commit.author]
            if c.authored_at < commit.authored_at
        )
        
        # Check which issues this commit references
        referenced_issues = match_issue_references(commit.message)
        
        for issue_num in referenced_issues:
            if issue_num not in closed_issue_numbers:
                continue
            
            # Update resolution (commits have lower priority than PRs)
            if resolutions[issue_num]["resolver"] is None:
                resolutions[issue_num]["number"] = issue_num
                resolutions[issue_num]["resolver"] = commit.author
                resolutions[issue_num]["resolved_in"] = commit.sha
                resolutions[issue_num]["resolver_commit_num"] = commits_before
    
    # Step 2: Detect resolutions via PRs (higher priority)
    if prs_dict:
        for pr_num, pr in prs_dict.items():
            # Check if PR references any closed issue
            pr_text = "\n".join(
                [pr.title, pr.body] + (pr.get("comments", []) or [])
            )
            referenced_issues = match_issue_references(pr_text)
            
            for issue_num in referenced_issues:
                if issue_num not in closed_issue_numbers:
                    continue
                
                # Count commits by PR author before PR merge
                commits_before = sum(
                    1 for c in author_to_commits.get(pr.user, [])
                    if c.authored_at < pr.merged_at - timedelta(days=1)
                    and c.sha not in pr.get("commits", [])
                )
                
                # Update resolution (PR takes precedence)
                resolutions[issue_num]["number"] = issue_num
                resolutions[issue_num]["resolver"] = pr.user
                resolutions[issue_num]["resolved_in"] = str(pr_num)
                resolutions[issue_num]["resolver_commit_num"] = commits_before
    
    return list(resolutions.values())
