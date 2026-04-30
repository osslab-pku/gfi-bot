"""
Tests for repo-level feature computation (repo_features.py).

These tests verify that feature computation logic produces correct results
independently of database and API operations.
"""

import pytest
from datetime import datetime, timedelta, timezone
from gfibot.data.features.repo_features import (
    match_issue_references,
    compute_issue_close_time_median,
    detect_issue_resolutions,
)


class MockIssue:
    """Mock issue object for testing."""
    def __init__(self, number, created_at, closed_at=None, state="open", is_pull=False):
        self.number = number
        self.created_at = created_at
        self.closed_at = closed_at
        self.state = state
        self.is_pull = is_pull


class MockCommit:
    """Mock commit object for testing."""
    def __init__(self, sha, author, message, authored_at):
        self.sha = sha
        self.author = author
        self.message = message
        self.authored_at = authored_at


class MockPR:
    """Mock pull request object for testing."""
    def __init__(self, number, user, title, body, merged_at, commits=None, comments=None):
        self.number = number
        self.user = user
        self.title = title
        self.body = body
        self.merged_at = merged_at
        self.commits = commits or []
        self.comments = comments or []


# ============================================================================
# Tests for match_issue_references
# ============================================================================

class TestMatchIssueReferences:
    """Tests for issue reference pattern matching."""

    def test_single_fix_keyword(self):
        """Match single fix keyword."""
        assert match_issue_references("Fixes #123") == [123]

    def test_multiple_close_keywords(self):
        """Match multiple closing keywords."""
        assert match_issue_references("Closes #456 and fixes #789") == [456, 789]

    def test_all_keyword_variants(self):
        """Test all supported keywords and variants."""
        variants = [
            ("close #1", [1]),
            ("closes #2", [2]),
            ("closed #3", [3]),
            ("fix #4", [4]),
            ("fixes #5", [5]),
            ("fixed #6", [6]),
            ("resolve #7", [7]),
            ("resolves #8", [8]),
            ("resolved #9", [9]),
        ]
        for text, expected in variants:
            assert match_issue_references(text) == expected, f"Failed for: {text}"

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert match_issue_references("FIXES #123") == [123]
        assert match_issue_references("Fixes #456") == [456]
        assert match_issue_references("fixes #789") == [789]

    def test_no_match_without_hash(self):
        """Should not match issue without hash symbol."""
        assert match_issue_references("fixes 123") == []
        assert match_issue_references("close 456") == []

    def test_no_match_for_irrelevant_text(self):
        """Should not match irrelevant text."""
        assert match_issue_references("This is a regular commit") == []
        assert match_issue_references("Issue #123 was reported") == []

    def test_multiline_text(self):
        """Should work with multiline text."""
        text = "Fix bug in parser\n\nCloses #123\nResolves #456"
        assert match_issue_references(text) == [123, 456]

    def test_duplicate_references(self):
        """Should handle duplicate references."""
        result = match_issue_references("Fixes #123 and fixes #123")
        assert result == [123, 123]  # Duplicates are preserved

    def test_large_issue_numbers(self):
        """Should handle large issue numbers."""
        assert match_issue_references("Fixes #999999") == [999999]


# ============================================================================
# Tests for compute_issue_close_time_median
# ============================================================================

class TestComputeIssueCloseTimeMedian:
    """Tests for median issue close time computation."""

    def test_single_closed_issue(self):
        """Compute median for single issue."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issue = MockIssue(1, base, base + timedelta(days=1))
        result = compute_issue_close_time_median([issue])
        assert result == 86400.0  # 1 day in seconds

    def test_multiple_closed_issues(self):
        """Compute median for multiple issues."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issues = [
            MockIssue(1, base, base + timedelta(hours=1)),  # 3600s
            MockIssue(2, base, base + timedelta(hours=2)),  # 7200s
            MockIssue(3, base, base + timedelta(hours=3)),  # 10800s
        ]
        result = compute_issue_close_time_median(issues)
        assert result == 7200.0  # Median is middle value

    def test_no_closed_issues(self):
        """Return None when no closed issues."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issue = MockIssue(1, base, state="open")
        result = compute_issue_close_time_median([issue])
        assert result is None

    def test_ignores_pull_requests(self):
        """Should ignore pull requests."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issues = [
            MockIssue(1, base, base + timedelta(days=1), is_pull=True),  # Ignored
            MockIssue(2, base, base + timedelta(days=2)),  # Counted
        ]
        result = compute_issue_close_time_median(issues)
        assert result == 172800.0  # Only issue 2 counted

    def test_ignores_open_issues(self):
        """Should ignore open issues."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issues = [
            MockIssue(1, base, state="open"),  # Ignored
            MockIssue(2, base, base + timedelta(days=2)),  # Counted
        ]
        result = compute_issue_close_time_median(issues)
        assert result == 172800.0

    def test_empty_list(self):
        """Return None for empty list."""
        result = compute_issue_close_time_median([])
        assert result is None

    def test_even_number_of_issues(self):
        """Median with even count (average of middle two)."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        issues = [
            MockIssue(1, base, base + timedelta(hours=1)),  # 3600s
            MockIssue(2, base, base + timedelta(hours=2)),  # 7200s
        ]
        result = compute_issue_close_time_median(issues)
        assert result == 5400.0  # (3600 + 7200) / 2


# ============================================================================
# Tests for detect_issue_resolutions
# ============================================================================

class TestDetectIssueResolutions:
    """Tests for issue resolution detection."""

    def test_single_commit_resolution(self):
        """Detect single issue resolved by commit."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issue = MockIssue(123, base, base + timedelta(days=1))
        commit = MockCommit("abc123", "alice", "Fixes #123", base + timedelta(hours=12))
        
        issues_dict = {123: issue}
        commits_list = [commit]
        
        result = detect_issue_resolutions(issues_dict, commits_list)
        
        assert len(result) == 1
        assert result[0]["resolver"] == "alice"
        assert result[0]["resolved_in"] == "abc123"
        assert result[0]["resolver_commit_num"] == 0

    def test_multiple_issues_same_commit(self):
        """Detect multiple issues in single commit."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issues_dict = {
            123: MockIssue(123, base, base + timedelta(days=1)),
            456: MockIssue(456, base, base + timedelta(days=1)),
        }
        commit = MockCommit(
            "abc123", "alice", "Fixes #123 and resolves #456", base + timedelta(hours=12)
        )
        
        result = detect_issue_resolutions(issues_dict, [commit])
        
        assert len(result) == 2
        assert result[0]["resolver"] == "alice"
        assert result[1]["resolver"] == "alice"

    def test_commits_before_resolution(self):
        """Count commits by author before resolution."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issue = MockIssue(123, base, base + timedelta(days=10))
        commits = [
            MockCommit("aaa", "alice", "First", base + timedelta(days=0)),
            MockCommit("bbb", "alice", "Second", base + timedelta(days=2)),
            MockCommit("ccc", "alice", "Fixes #123", base + timedelta(days=10)),
        ]
        
        result = detect_issue_resolutions({123: issue}, commits)
        
        assert result[0]["resolver_commit_num"] == 2

    def test_no_resolution_if_issue_not_referenced(self):
        """No resolution if issue not referenced."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issue = MockIssue(123, base, base + timedelta(days=1))
        commit = MockCommit("abc123", "alice", "Random commit", base + timedelta(hours=12))
        
        result = detect_issue_resolutions({123: issue}, [commit])
        
        assert result[0]["resolver"] is None

    def test_no_resolution_for_open_issues(self):
        """Should not match issues not in the provided dict."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issues_dict = {}  # Empty - issue 123 not provided
        commit = MockCommit("abc123", "alice", "Fixes #123", base)
        
        result = detect_issue_resolutions(issues_dict, [commit])
        assert len(result) == 0

    def test_pr_resolution_priority(self):
        """PR-based resolution takes priority over commit-based."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issue = MockIssue(123, base, base + timedelta(days=10))
        
        # Commit resolves it first
        commit = MockCommit("aaa", "alice", "Fixes #123", base + timedelta(days=5))
        
        # Then PR also references it (should override)
        pr = MockPR(456, "bob", "Feature", "Resolves #123", base + timedelta(days=8))
        prs_dict = {456: pr}
        
        result = detect_issue_resolutions({123: issue}, [commit], prs_dict)
        
        # PR resolution should override commit resolution
        assert result[0]["resolver"] == "bob"
        assert result[0]["resolved_in"] == "456"

    def test_null_author_ignored(self):
        """Commits with null author should be ignored."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issue = MockIssue(123, base, base + timedelta(days=1))
        commit = MockCommit("abc123", None, "Fixes #123", base)
        
        result = detect_issue_resolutions({123: issue}, [commit])
        
        assert result[0]["resolver"] is None

    def test_multiple_authors(self):
        """Handle multiple authors correctly."""
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        issues_dict = {
            123: MockIssue(123, base, base + timedelta(days=5)),
            456: MockIssue(456, base, base + timedelta(days=5)),
        }
        commits = [
            MockCommit("aaa", "alice", "Work", base + timedelta(days=1)),
            MockCommit("bbb", "bob", "Fixes #456", base + timedelta(days=3)),
            MockCommit("ccc", "alice", "Fixes #123", base + timedelta(days=4)),
        ]
        
        result = detect_issue_resolutions(issues_dict, commits)
        
        resolved_123 = [r for r in result if r["number"] == 123][0]
        resolved_456 = [r for r in result if r["number"] == 456][0]
        
        assert resolved_123["resolver"] == "alice"
        assert resolved_456["resolver"] == "bob"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
