"""Analytics instrumentation decorator for MCP tools."""

from __future__ import annotations

import functools
import hashlib
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from src.data.api_client import post_analytics

logger = logging.getLogger(__name__)

# Deliberately NOT rotated. Return rate — whether a caller comes back on a
# later day — is the metric this field exists for, and a rotating salt would
# make it uncomputable by construction. The trade-off is that the digest is a
# persistent pseudonymous id, so keep it to what it is: a hash of transport
# identity, never joined to anything else, with the raw IP never stored.
# Bump the version suffix to deliberately break continuity.
_CLIENT_SALT = "seoul-essentials/v1"


def _client_hash() -> str | None:
    """Stable, non-reversible key for one calling client.

    The server runs stateless_http, so there is no MCP session to key on. We
    hash the transport identity instead — never storing the raw IP, which is
    personal data we have no reason to keep. Returns None outside a request
    context (local calls, tests) rather than inventing an identity.
    """
    try:
        from fastmcp.server.dependencies import get_http_headers

        h = get_http_headers() or {}
    except Exception:
        return None
    ua = h.get("user-agent", "")
    # Cloud Run puts the real client first in X-Forwarded-For.
    ip = (h.get("x-forwarded-for", "") or "").split(",")[0].strip()
    if not ua and not ip:
        return None
    return hashlib.sha256(f"{_CLIENT_SALT}|{ua}|{ip}".encode()).hexdigest()[:16]


def _result_ids(result: Any, cap: int = 20) -> list[str] | None:
    """Ids this call handed back, so a later get_place_detail can be matched to
    the rank it was chosen from. Agents picking rank 4 every time means our
    ordering is wrong even though nothing 'failed'."""
    rows = result if isinstance(result, list) else (
        result.get("results") if isinstance(result, dict) else None
    )
    if not isinstance(rows, list):
        return None
    out = [r["id"] for r in rows[:cap] if isinstance(r, dict) and isinstance(r.get("id"), str)]
    return out or None


def track_usage(func: Callable) -> Callable:
    """Decorator that records tool usage analytics after each call.

    Measures response time, counts results, detects errors,
    and sends the event asynchronously (fire-and-forget).
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        error_msg = None
        result = None

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_msg = str(e)
            raise
        finally:
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)

            # Count results
            result_count = 0
            if isinstance(result, list):
                result_count = len(result)
            elif isinstance(result, dict) and "error" not in result:
                # payload-style responses carry their own count (e.g. subway)
                c = result.get("count")
                result_count = c if isinstance(c, int) else 1

            event = {
                "tool": func.__name__,
                "params": {k: v for k, v in kwargs.items() if v is not None},
                "result_count": result_count,
                "response_time_ms": elapsed_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if error_msg:
                event["error"] = error_msg

            # Engagement instrumentation. Never let it break a tool call —
            # this whole block is inside the finally of a fire-and-forget path.
            try:
                ch = _client_hash()
                if ch:
                    event["client_hash"] = ch
                ids = _result_ids(result)
                if ids:
                    event["result_ids"] = ids
            except Exception:
                logger.debug("engagement fields skipped", exc_info=True)

            # Fire-and-forget in background thread
            threading.Thread(
                target=post_analytics,
                args=(event,),
                daemon=True,
            ).start()

    return wrapper
