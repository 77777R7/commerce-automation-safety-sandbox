from __future__ import annotations

import hmac
import ipaddress


class LiveSecurityError(ValueError):
    """Raised when a live-agent server configuration is unsafe to start."""


SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def normalize_api_token(api_token: str | None) -> str | None:
    if api_token is None:
        return None
    stripped = api_token.strip()
    return stripped or None


def is_loopback_host(host: str) -> bool:
    normalized = (host or "").strip().lower()
    if normalized in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def constant_time_token_matches(provided: str, expected: str | None) -> bool:
    normalized_expected = normalize_api_token(expected)
    if normalized_expected is None:
        return False
    return hmac.compare_digest(provided, normalized_expected)


def validate_live_server_security(host: str, api_token: str | None) -> None:
    """Reject unsafe live server configs before binding a socket."""

    if is_loopback_host(host):
        return
    if normalize_api_token(api_token):
        return
    raise LiveSecurityError(
        "Refusing to bind the live HTTP server to a non-loopback host without "
        "an api token. Use --api-token or COMMERCE_SAFETY_API_TOKEN."
    )

