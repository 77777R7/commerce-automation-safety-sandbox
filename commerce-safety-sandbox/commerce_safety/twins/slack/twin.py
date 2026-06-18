from __future__ import annotations

from copy import deepcopy
from typing import Any

from ...models import to_plain
from .models import SlackChannel, SlackMessage


class SlackTwin:
    """A narrow, permissive Slack messaging twin for SaaS agent validation."""

    def __init__(self, scenario: dict[str, Any] | None = None):
        self.scenario = scenario or {}
        self.channels: dict[str, SlackChannel] = {}
        self.messages: list[SlackMessage] = []
        self.timeline: list[dict[str, Any]] = []
        self.bot_has_chat_write = True
        self._next_channel = 1
        self._next_message = 1
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        state = (
            self.scenario.get("initial_state", {}).get("slack")
            or self.scenario.get("slack")
            or {}
        )
        self.bot_has_chat_write = bool(state.get("bot_has_chat_write", True))
        for channel in state.get("channels", []):
            item = SlackChannel(**channel)
            self.channels[item.channel_id] = item
        for message in state.get("messages", []):
            self.messages.append(SlackMessage(**message))
        self._advance_counters()

    def _advance_counters(self) -> None:
        for channel_id in self.channels:
            if channel_id.startswith("C") and channel_id[1:].isdigit():
                self._next_channel = max(self._next_channel, int(channel_id[1:]) + 1)
        for message in self.messages:
            if message.message_id.startswith("slack_msg_"):
                suffix = message.message_id.removeprefix("slack_msg_")
                if suffix.isdigit():
                    self._next_message = max(self._next_message, int(suffix) + 1)

    def _next_channel_id(self) -> str:
        channel_id = f"C{self._next_channel:06d}"
        self._next_channel += 1
        return channel_id

    def _next_message_id(self) -> str:
        message_id = f"slack_msg_{self._next_message:06d}"
        self._next_message += 1
        return message_id

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

    def create_channel(
        self,
        *,
        name: str,
        channel_id: str | None = None,
        is_private: bool = False,
        bot_is_member: bool = True,
        actor: str = "external_agent",
    ) -> SlackChannel:
        channel = SlackChannel(
            channel_id=channel_id or self._next_channel_id(),
            name=name,
            is_private=is_private,
            bot_is_member=bot_is_member,
        )
        self.channels[channel.channel_id] = channel
        self._record(
            actor=actor,
            operation="conversations.create",
            message=f"Created Slack channel {channel.name}.",
            details=to_plain(channel),
        )
        return channel

    def join_channel(
        self,
        channel_id: str,
        *,
        actor: str = "external_agent",
    ) -> SlackChannel:
        channel = self.get_channel(channel_id)
        channel.bot_is_member = True
        self._record(
            actor=actor,
            operation="conversations.join",
            message=f"Joined Slack channel {channel_id}.",
            details=to_plain(channel),
        )
        return channel

    def get_channel(self, channel_id: str) -> SlackChannel:
        try:
            return self.channels[channel_id]
        except KeyError as error:
            raise ValueError(f"Unknown Slack channel: {channel_id}") from error

    def open_conversation(
        self,
        *,
        channel_id: str | None = None,
        name: str | None = None,
        is_private: bool = False,
        actor: str = "external_agent",
    ) -> SlackChannel:
        if channel_id and channel_id in self.channels:
            return self.channels[channel_id]
        if name:
            for channel in self.channels.values():
                if channel.name == name:
                    return channel
        if not name and not channel_id:
            raise ValueError("channel_id or name is required")
        return self.create_channel(
            name=name or channel_id or "conversation",
            channel_id=channel_id,
            is_private=is_private,
            bot_is_member=True,
            actor=actor,
        )

    def post_message(
        self,
        *,
        channel_id: str,
        text: str,
        thread_ts: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> SlackMessage:
        delivered = True
        error = None
        channel = self.channels.get(channel_id)
        if not self.bot_has_chat_write:
            delivered = False
            error = "missing_scope"
        elif channel is None:
            delivered = False
            error = "channel_not_found"
        elif channel.archived:
            delivered = False
            error = "channel_archived"
        elif channel.is_private and not channel.bot_is_member:
            delivered = False
            error = "not_in_channel"

        message = SlackMessage(
            message_id=self._next_message_id(),
            channel_id=channel_id,
            text=text,
            delivered=delivered,
            error=error,
            thread_ts=thread_ts,
            metadata=metadata or {},
            actor=actor,
        )
        self.messages.append(message)
        self._record(
            actor=actor,
            operation="chat.postMessage",
            message=(
                f"Posted Slack message {message.message_id}."
                if delivered
                else f"Slack message {message.message_id} failed with {error}."
            ),
            details=to_plain(message),
        )
        return message

    def delivered_messages(self, kind: str | None = None) -> list[SlackMessage]:
        return [
            message
            for message in self.messages
            if message.delivered and self._matches_kind(message, kind)
        ]

    def failed_messages(self, kind: str | None = None) -> list[SlackMessage]:
        return [
            message
            for message in self.messages
            if not message.delivered and self._matches_kind(message, kind)
        ]

    def has_delivered_message_kind(self, kind: str) -> bool:
        return bool(self.delivered_messages(kind))

    def has_success_message(self) -> bool:
        return bool(self.success_messages())

    def success_messages(self) -> list[SlackMessage]:
        return [
            message
            for message in self.messages
            if message.delivered
            and (
                message.metadata.get("kind") == "success_notification"
                or self._text_looks_successful(message.text)
            )
        ]

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            "service": "slack",
            "channels": {
                key: to_plain(value) for key, value in self.channels.items()
            },
            "messages": [to_plain(message) for message in self.messages],
            "timeline": deepcopy(self.timeline),
            "counts": {
                "channels": len(self.channels),
                "messages": len(self.messages),
                "delivered_messages": len(self.delivered_messages()),
                "failed_messages": len(self.failed_messages()),
                "billing_failure_alerts_delivered": len(
                    self.delivered_messages("billing_failure_alert")
                ),
                "billing_failure_alerts_failed": len(
                    self.failed_messages("billing_failure_alert")
                ),
            },
            "signals": {
                "has_success_message": self.has_success_message(),
                "has_billing_failure_alert": self.has_delivered_message_kind(
                    "billing_failure_alert"
                ),
            },
        }

    def compact_state(self) -> dict[str, Any]:
        snapshot = self.snapshot_summary()
        return {
            "counts": snapshot["counts"],
            "signals": snapshot["signals"],
        }

    def _matches_kind(self, message: SlackMessage, kind: str | None) -> bool:
        if kind is None:
            return True
        return message.metadata.get("kind") == kind

    def _text_looks_successful(self, text: str) -> bool:
        normalized = text.lower()
        return any(
            phrase in normalized
            for phrase in (
                "success",
                "upgrade complete",
                "pro plan active",
                "subscription active",
            )
        )
