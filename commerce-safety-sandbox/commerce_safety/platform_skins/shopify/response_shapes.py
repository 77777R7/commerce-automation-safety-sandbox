from __future__ import annotations

from typing import Any


def shopify_fulfillment_gid(fulfillment_id: str) -> str:
    return f"gid://shopify/Fulfillment/{fulfillment_id}"


def fulfillment_create_success(
    fulfillment: dict[str, Any],
    *,
    session_id: str,
) -> dict[str, Any]:
    internal_id = str(fulfillment["fulfillment_id"])
    return {
        "data": {
            "fulfillmentCreate": {
                "fulfillment": {
                    "id": shopify_fulfillment_gid(internal_id),
                    "legacyResourceId": internal_id,
                    "status": "SUCCESS",
                },
                "userErrors": [],
            }
        },
        "extensions": {
            "_commerce_twin": {
                "skin": "shopify_like",
                "session_id": session_id,
                "internal_fulfillment_id": internal_id,
            },
            "cost": {
                "requestedQueryCost": 10,
                "actualQueryCost": 10,
                "throttleStatus": {
                    "maximumAvailable": 1000.0,
                    "currentlyAvailable": 990,
                    "restoreRate": 50.0,
                },
            },
        },
    }


def fulfillment_create_timeout(
    *,
    session_id: str,
    fulfillment_id: str,
) -> dict[str, Any]:
    return {
        "data": None,
        "errors": [
            {
                "message": "timeout_after_commit",
                "extensions": {"code": "COMMERCE_TWIN_TIMEOUT_AFTER_COMMIT"},
            }
        ],
        "extensions": {
            "_commerce_twin": {
                "skin": "shopify_like",
                "session_id": session_id,
                "error": "timeout_after_commit",
                "fulfillment_id": fulfillment_id,
                "committed_before_timeout": True,
            }
        },
    }


def unsupported_mutation_response(mutation_name: str | None) -> dict[str, Any]:
    display_name = mutation_name or "unknown mutation"
    return {
        "data": None,
        "errors": [
            {
                "message": (
                    f"{display_name} is not implemented by Shopify-like Skin V0."
                ),
                "extensions": {"code": "COMMERCE_TWIN_UNSUPPORTED_MUTATION"},
            }
        ],
        "extensions": {
            "_commerce_twin_stub": True,
            "coverage": "unsupported",
            "skin": "shopify_like",
            "mutation": display_name,
        },
    }
