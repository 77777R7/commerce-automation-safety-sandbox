from __future__ import annotations

from commerce_safety.twins.github import GitHubTwin


def _github_scenario() -> dict:
    return {
        "initial_state": {
            "github": {
                "repos": [{"owner": "acme", "name": "billing-agent"}],
                "pull_requests": [
                    {
                        "pull_number": 42,
                        "repo": "acme/billing-agent",
                        "head_sha": "abc123",
                        "title": "Billing agent",
                    }
                ],
            }
        }
    }


def test_github_twin_records_check_runs_and_success_signal():
    twin = GitHubTwin(_github_scenario())

    check_run = twin.create_check_run(
        owner="acme",
        repo_name="billing-agent",
        head_sha="abc123",
        conclusion="success",
        output_summary="All billing validations passed.",
    )

    assert twin.latest_check_run(head_sha="abc123") == check_run
    assert twin.has_success_check() is True
    assert twin.snapshot_summary()["counts"]["success_check_runs"] == 1


def test_github_twin_records_issue_and_pr_feedback():
    twin = GitHubTwin(_github_scenario())

    issue = twin.create_issue(
        owner="acme",
        repo_name="billing-agent",
        title="Payment failed",
        body="Initial payment failed; manual recovery needed.",
        labels=["billing", "agent-review"],
    )
    comment = twin.comment_on_pr(
        owner="acme",
        repo_name="billing-agent",
        pull_number=42,
        body="Policy check requires billing recovery before merge.",
    )

    assert issue.labels == ["billing", "agent-review"]
    assert comment.pull_number == 42
    assert twin.has_pr_feedback() is True
    assert twin.snapshot_summary()["counts"]["issues"] == 1
