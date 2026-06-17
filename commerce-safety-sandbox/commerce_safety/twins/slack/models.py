from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SlackChannel:
    channel_id: str
    name: str
    is_private: bool = False
    bot_is_member: bool = True
    archived: bool = False


@dataclass
class SlackMessage:
    message_id: str
    channel_id: str
    text: str
    delivered: bool
    error: str | None = None
    thread_ts: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    actor: str = "external_agent"
