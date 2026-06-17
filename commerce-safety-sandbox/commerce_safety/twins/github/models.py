from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GitHubRepo:
    owner: str
    name: str
    default_branch: str = "main"


@dataclass
class GitHubPullRequest:
    pull_number: int
    repo: str
    head_sha: str
    title: str


@dataclass
class GitHubCheckRun:
    check_run_id: str
    name: str
    repo: str
    head_sha: str
    status: str
    conclusion: str | None
    output_summary: str
    details_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubIssue:
    issue_id: str
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    state: str = "open"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubPRComment:
    comment_id: str
    pull_number: int
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
