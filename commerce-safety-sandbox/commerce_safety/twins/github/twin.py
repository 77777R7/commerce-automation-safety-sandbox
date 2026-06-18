from __future__ import annotations

from copy import deepcopy
from typing import Any

from ...models import to_plain
from .models import (
    GitHubCheckRun,
    GitHubIssue,
    GitHubPRComment,
    GitHubPullRequest,
    GitHubRepo,
)


class GitHubTwin:
    """A narrow, permissive GitHub PR/check twin for SaaS agent validation."""

    def __init__(self, scenario: dict[str, Any] | None = None):
        self.scenario = scenario or {}
        self.repos: dict[str, GitHubRepo] = {}
        self.pull_requests: dict[str, GitHubPullRequest] = {}
        self.check_runs: dict[str, GitHubCheckRun] = {}
        self.issues: dict[str, GitHubIssue] = {}
        self.pr_comments: dict[str, GitHubPRComment] = {}
        self.timeline: list[dict[str, Any]] = []
        self._next_check_run = 1
        self._next_issue = 1
        self._next_comment = 1
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        state = (
            self.scenario.get("initial_state", {}).get("github")
            or self.scenario.get("github")
            or {}
        )
        for repo in state.get("repos", []):
            item = GitHubRepo(**repo)
            self.repos[self._repo_key(item.owner, item.name)] = item
        for pull_request in state.get("pull_requests", []):
            item = GitHubPullRequest(**pull_request)
            key = self._pull_request_key(item.repo, item.pull_number)
            self.pull_requests[key] = item
        for check_run in state.get("check_runs", []):
            item = GitHubCheckRun(**check_run)
            self.check_runs[item.check_run_id] = item
        for issue in state.get("issues", []):
            item = GitHubIssue(**issue)
            self.issues[item.issue_id] = item
        for comment in state.get("pr_comments", []):
            item = GitHubPRComment(**comment)
            self.pr_comments[item.comment_id] = item
        self._advance_counters()

    def _advance_counters(self) -> None:
        self._next_check_run = self._next_numeric_suffix(
            self.check_runs, "check_"
        )
        self._next_issue = self._next_numeric_suffix(self.issues, "issue_")
        self._next_comment = self._next_numeric_suffix(
            self.pr_comments, "comment_"
        )

    def _next_numeric_suffix(self, values: dict[str, Any], prefix: str) -> int:
        next_value = 1
        for key in values:
            if key.startswith(prefix):
                suffix = key.removeprefix(prefix)
                if suffix.isdigit():
                    next_value = max(next_value, int(suffix) + 1)
        return next_value

    def _next_id(self, prefix: str) -> str:
        if prefix == "check":
            value = self._next_check_run
            self._next_check_run += 1
        elif prefix == "issue":
            value = self._next_issue
            self._next_issue += 1
        elif prefix == "comment":
            value = self._next_comment
            self._next_comment += 1
        else:
            raise ValueError(f"Unsupported GitHub id prefix: {prefix}")
        return f"{prefix}_{value:06d}"

    def _record(
        self,
        *,
        actor: str,
        operation: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.timeline.append(
            {
                "step": len(self.timeline) + 1,
                "actor": actor,
                "operation": operation,
                "message": message,
                "details": details or {},
            }
        )

    def get_repo_context(self, *, owner: str, name: str) -> dict[str, Any]:
        repo = self._require_repo(owner, name)
        repo_key = self._repo_key(owner, name)
        return {
            "repo": to_plain(repo),
            "pull_requests": [
                to_plain(pr)
                for pr in self.pull_requests.values()
                if pr.repo == repo_key
            ],
            "check_runs": [
                to_plain(check)
                for check in self.check_runs.values()
                if check.repo == repo_key
            ],
            "issues": [to_plain(issue) for issue in self.issues.values()],
        }

    def create_check_run(
        self,
        *,
        owner: str,
        repo_name: str,
        head_sha: str,
        name: str = "agent-policy/saas-validation",
        status: str = "completed",
        conclusion: str | None = None,
        output_summary: str = "",
        details_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> GitHubCheckRun:
        repo = self._require_repo(owner, repo_name)
        check_run = GitHubCheckRun(
            check_run_id=self._next_id("check"),
            name=name,
            repo=self._repo_key(repo.owner, repo.name),
            head_sha=head_sha,
            status=status,
            conclusion=conclusion,
            output_summary=output_summary,
            details_url=details_url,
            metadata=metadata or {},
        )
        self.check_runs[check_run.check_run_id] = check_run
        self._record(
            actor=actor,
            operation="checks.create",
            message=f"Created GitHub check run {check_run.name}.",
            details=to_plain(check_run),
        )
        return check_run

    def update_check_run(
        self,
        check_run_id: str,
        *,
        status: str | None = None,
        conclusion: str | None = None,
        output_summary: str | None = None,
        actor: str = "external_agent",
    ) -> GitHubCheckRun:
        check_run = self._require_check_run(check_run_id)
        before = to_plain(check_run)
        if status is not None:
            check_run.status = status
        if conclusion is not None:
            check_run.conclusion = conclusion
        if output_summary is not None:
            check_run.output_summary = output_summary
        self._record(
            actor=actor,
            operation="checks.update",
            message=f"Updated GitHub check run {check_run_id}.",
            details={"before": before, "after": to_plain(check_run)},
        )
        return check_run

    def create_issue(
        self,
        *,
        owner: str,
        repo_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> GitHubIssue:
        self._require_repo(owner, repo_name)
        issue = GitHubIssue(
            issue_id=self._next_id("issue"),
            title=title,
            body=body,
            labels=labels or [],
            metadata=metadata or {},
        )
        self.issues[issue.issue_id] = issue
        self._record(
            actor=actor,
            operation="issues.create",
            message=f"Created GitHub issue {issue.issue_id}.",
            details=to_plain(issue),
        )
        return issue

    def comment_on_pr(
        self,
        *,
        owner: str,
        repo_name: str,
        pull_number: int,
        body: str,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> GitHubPRComment:
        repo_key = self._repo_key(owner, repo_name)
        self._require_pull_request(repo_key, pull_number)
        comment = GitHubPRComment(
            comment_id=self._next_id("comment"),
            pull_number=pull_number,
            body=body,
            metadata=metadata or {},
        )
        self.pr_comments[comment.comment_id] = comment
        self._record(
            actor=actor,
            operation="pulls.comment",
            message=f"Commented on GitHub PR #{pull_number}.",
            details=to_plain(comment),
        )
        return comment

    def latest_check_run(
        self,
        *,
        name: str | None = None,
        head_sha: str | None = None,
    ) -> GitHubCheckRun | None:
        matches = [
            check
            for check in self.check_runs.values()
            if (name is None or check.name == name)
            and (head_sha is None or check.head_sha == head_sha)
        ]
        return matches[-1] if matches else None

    def has_success_check(self) -> bool:
        return any(
            check.status == "completed" and check.conclusion == "success"
            for check in self.check_runs.values()
        )

    def success_check_runs(self) -> list[GitHubCheckRun]:
        return [
            check
            for check in self.check_runs.values()
            if check.status == "completed" and check.conclusion == "success"
        ]

    def has_pr_feedback(self) -> bool:
        return bool(self.pr_comments)

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            "service": "github",
            "repos": {key: to_plain(value) for key, value in self.repos.items()},
            "pull_requests": {
                key: to_plain(value) for key, value in self.pull_requests.items()
            },
            "check_runs": {
                key: to_plain(value) for key, value in self.check_runs.items()
            },
            "issues": {key: to_plain(value) for key, value in self.issues.items()},
            "pr_comments": {
                key: to_plain(value) for key, value in self.pr_comments.items()
            },
            "timeline": deepcopy(self.timeline),
            "counts": {
                "repos": len(self.repos),
                "pull_requests": len(self.pull_requests),
                "check_runs": len(self.check_runs),
                "issues": len(self.issues),
                "pr_comments": len(self.pr_comments),
                "success_check_runs": len(self.success_check_runs()),
            },
            "signals": {
                "has_success_check": self.has_success_check(),
                "has_pr_feedback": self.has_pr_feedback(),
            },
        }

    def compact_state(self) -> dict[str, Any]:
        snapshot = self.snapshot_summary()
        return {
            "counts": snapshot["counts"],
            "signals": snapshot["signals"],
        }

    def _repo_key(self, owner: str, name: str) -> str:
        return f"{owner}/{name}"

    def _pull_request_key(self, repo: str, pull_number: int) -> str:
        return f"{repo}#{pull_number}"

    def _require_repo(self, owner: str, name: str) -> GitHubRepo:
        key = self._repo_key(owner, name)
        try:
            return self.repos[key]
        except KeyError as error:
            raise ValueError(f"Unknown GitHub repo: {key}") from error

    def _require_pull_request(
        self, repo: str, pull_number: int
    ) -> GitHubPullRequest:
        key = self._pull_request_key(repo, pull_number)
        try:
            return self.pull_requests[key]
        except KeyError as error:
            raise ValueError(f"Unknown GitHub pull request: {key}") from error

    def _require_check_run(self, check_run_id: str) -> GitHubCheckRun:
        try:
            return self.check_runs[check_run_id]
        except KeyError as error:
            raise ValueError(f"Unknown GitHub check run: {check_run_id}") from error
