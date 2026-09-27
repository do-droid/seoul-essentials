"""Analytics instrumentation decorator for MCP tools."""

from __future__ import annotations

import contextvars
import functools
import hashlib
import hmac
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from src.data.api_client import post_analytics

logger = logging.getLogger(__name__)

# Deliberately NOT rotated. Return rate — whether a caller comes back on a
# later day — is the metric this field exists for, and a rotating secret would
# make it uncomputable by construction. The trade-off is that the digest is a
# persistent pseudonymous id, so keep it to what it is: a keyed hash of
# transport identity, with the raw IP never stored.
#
# v2 (0.9.0) is an HMAC with the CLIENT_ID_SECRET env secret. v1 used a salt
# published in this repo; once events also carried the raw User-Agent, the IP
# behind a v1 hash could be recovered by trying all IPv4 addresses (~30 CPU
# minutes). The same secret keys gateway_key_hash. Without it, neither is
# written — a warning is logged at startup (see server.main).
_CLIENT_ID_SECRET_ENV = "CLIENT_ID_SECRET"


def _secret() -> bytes | None:
    v = os.environ.get(_CLIENT_ID_SECRET_ENV)
    return v.encode() if v else None


def keyed_hash(label: str, value: str, n: int) -> str | None:
    key = _secret()
    if not key:
        return None
    return hmac.new(key, f"{label}|{value}".encode(), hashlib.sha256).hexdigest()[:n]


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
    return keyed_hash("client/v2", f"{ua}|{ip}", 16)


# Clients on the 2026-07-28 spec repeat their clientInfo in every request's
# _meta (stateless). Set per tool call by the middleware, read here.
CLIENT_INFO: contextvars.ContextVar[dict | None] = contextvars.ContextVar("client_info", default=None)
# Argument repairs the middleware made for this call ("station_name->station").
REPAIRS: contextvars.ContextVar[list | None] = contextvars.ContextVar("repairs", default=None)

_CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"


def client_info_from_meta(meta: Any) -> dict | None:
    if isinstance(meta, dict):
        ci = meta.get(_CLIENT_INFO_META_KEY)
        if isinstance(ci, dict) and ci.get("name"):
            return ci
    return None


def transport_fields() -> dict[str, Any]:
    """Who is on the other end, as far as the transport says — for telling
    callers apart (v9: client_hash alone split one harness into 4 and merged
    unrelated SDK users).

    ua: the User-Agent product string. via: "gateway" when a listing gateway
    (e.g. Smithery) appends ?api_key=… to our URL, else "direct".
    gateway_key_hash: HMAC of that key with the CLIENT_ID_SECRET env secret —
    the key is a third party's credential, so the raw value is never stored,
    and without the secret no hash is written at all (a public salt would make
    it brute-forceable from the repo).
    """
    try:
        from fastmcp.server.dependencies import get_http_request

        req = get_http_request()
    except Exception:
        return {}
    out: dict[str, Any] = {"ua": (req.headers.get("user-agent") or "")[:120]}
    key = req.query_params.get("api_key")
    out["via"] = "gateway" if key else "direct"
    if key:
        kh = keyed_hash("gateway-key", key, 12)
        if kh:
            out["gateway_key_hash"] = kh
    profile = req.query_params.get("profile")
    if profile:
        out["gateway_profile"] = profile[:40]
    ci = CLIENT_INFO.get()
    if ci:
        out["client_name"] = f"{ci.get('name', '')}/{ci.get('version', '')}"[:80]
    return out


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

            # Count results. API rejections (400/404) come back as values, not
            # exceptions — an error dict, or a plain string from the subway and
            # detail tools — so until v0.9.0 every one was recorded as an empty
            # success with error=null and the error field was null on all 8,392
            # events. Record them as errors; result_count stays 0 either way.
            result_count = 0
            if isinstance(result, list):
                result_count = len(result)
            elif isinstance(result, dict):
                if "error" in result:
                    error_msg = error_msg or str(result["error"])[:200]
                else:
                    # payload-style responses carry their own count (e.g. subway)
                    c = result.get("count")
                    result_count = c if isinstance(c, int) else 1
            elif isinstance(result, str):
                error_msg = error_msg or result[:200]

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
                event.update(transport_fields())
                repairs = REPAIRS.get()
                if repairs:
                    event["repairs"] = ",".join(repairs)[:80]
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
