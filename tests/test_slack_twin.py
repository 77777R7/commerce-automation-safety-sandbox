from __future__ import annotations

from commerce_safety.twins.slack import SlackTwin


def test_slack_twin_delivers_message_to_reachable_channel():
    twin = SlackTwin()
    channel = twin.create_channel(name="incidents")

    message = twin.post_message(
        channel_id=channel.channel_id,
        text="Billing failure for customer account.",
        metadata={"kind": "billing_failure_alert"},
    )

    assert message.delivered is True
    assert message.error is None
    assert twin.has_delivered_message_kind("billing_failure_alert") is True
    assert twin.snapshot_summary()["counts"]["delivered_messages"] == 1


def test_slack_twin_records_private_channel_permission_failure():
    twin = SlackTwin(
        {
            "initial_state": {
                "slack": {
                    "channels": [
                        {
                            "channel_id": "C_PRIVATE",
                            "name": "billing-private",
                            "is_private": True,
                            "bot_is_member": False,
                        }
                    ]
                }
            }
        }
    )

    message = twin.post_message(
        channel_id="C_PRIVATE",
        text="Billing failure for customer account.",
        metadata={"kind": "billing_failure_alert"},
    )

    assert message.delivered is False
    assert message.error == "not_in_channel"
    assert twin.failed_messages("billing_failure_alert") == [message]
    assert twin.snapshot_summary()["counts"]["billing_failure_alerts_failed"] == 1
