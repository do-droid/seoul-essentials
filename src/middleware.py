"""Argument repair and rejection tracking for tool calls.

Why: about 1 in 11 tool calls from agents was rejected by schema validation
before reaching the tool (30 days to 2026-09-26: 96 of ~1,100 non-operator
attempts). Those calls never reached @track_usage, so they were invisible in
analytics — and most were slips with one obvious meaning (station_name for
station, full for full_day, an integer line). Agents that do not re-read
tools/list keep making them.

Only renames with a single possible meaning belong here. A guess that can be
wrong (e.g. free-text `query` → type/district) would turn a visible rejection
into a silently different answer, so it stays a rejection — now a recorded one.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any

from fastmcp.exceptions import ValidationError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from src.data.api_client import post_analytics

logger = logging.getLogger(__name__)

# tool -> {wrong name: canonical name}. Applied only when the canonical name is
# absent, so an explicit correct argument always wins.
_RENAMES: dict[str, dict[str, str]] = {
    "get_subway_timetable": {"station_name": "station", "full": "full_day"},
    # radius → radius_m only when the value is plausibly meters (see below).
    "find_nearby": {"latitude": "lat", "longitude": "lng", "lon": "lng"},
    "get_place_detail": {"place_id": "id"},
}

_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}


def repair_arguments(tool: str, args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return (arguments, list of repairs made)."""
    fixed = dict(args)
    repairs: list[str] = []
    for wrong, right in _RENAMES.get(tool, {}).items():
        if wrong in fixed and right not in fixed:
            fixed[right] = fixed.pop(wrong)
            repairs.append(f"{wrong}->{right}")
    if tool == "find_nearby" and "radius" in fixed and "radius_m" not in fixed:
        # "radius" is often kilometres (radius=1). Rename only meter-sized
        # numbers; anything else stays a rejection whose hint says meters.
        r = fixed["radius"]
        if isinstance(r, (int, float)) and not isinstance(r, bool) and r >= 100:
            fixed["radius_m"] = int(r)
            fixed.pop("radius")
            repairs.append("radius->radius_m")
    if tool == "get_subway_timetable":
        if isinstance(fixed.get("line"), int) and not isinstance(fixed["line"], bool):
            fixed["line"] = str(fixed["line"])
            repairs.append("line:int->str")
        v = fixed.get("full_day")
        if isinstance(v, str) and v.strip().lower() in _TRUE | _FALSE:
            fixed["full_day"] = v.strip().lower() in _TRUE
            repairs.append("full_day:str->bool")
    return fixed, repairs


_MAX_KEYS = 20


def _record_rejection(tool: str, args: dict[str, Any], exc: Exception) -> None:
    """One analytics event per rejected call, shaped like a normal event with
    result_count 0 and error='invalid_arguments: …' so zero-result and error
    metrics finally see these calls."""
    from src.tools.analytics import _client_hash, transport_fields  # same request context

    # args are the keys the client actually SENT (before repair) — the slips
    # are a fingerprint of the calling framework. Bounded, and never free text
    # from submit_feedback (the caller skips that tool).
    keys = sorted(str(k)[:64] for k in args)[:_MAX_KEYS]
    event: dict[str, Any] = {
        "tool": tool,
        "params": {str(k)[:64]: (v if isinstance(v, (int, float, bool)) or v is None
                                 else str(v)[:200])
                   for k, v in list(args.items())[:_MAX_KEYS]},
        "result_count": 0,
        "response_time_ms": 0,
        "error": f"invalid_arguments: keys={keys} — {str(exc)[:160]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        ch = _client_hash()
        if ch:
            event["client_hash"] = ch
        event.update(transport_fields())
    except Exception:
        pass
    threading.Thread(target=post_analytics, args=(event,), daemon=True).start()


def rejection_hint(tool: str, args: dict[str, Any], valid: list[str]) -> str:
    """One sentence that lets the agent fix the call on its next turn."""
    unknown = sorted(set(args) - set(valid))
    parts = []
    if unknown:
        parts.append(f"Unknown argument(s) {unknown}.")
    if tool == "find_nearby" and "radius" in args:
        parts.append("Use radius_m, in meters (100-5000).")
    if tool == "find_places" and {"query", "q", "keyword", "name", "search"} & set(unknown):
        parts.append("find_places has no name or keyword search: choose a `type` "
                     "(e.g. toilet, pharmacy, tourist_info) and optionally a `district`.")
    if valid:
        parts.append(f"Valid arguments for {tool}: {', '.join(valid)}.")
    return " ".join(parts)


def _header_fingerprint() -> dict[str, Any]:
    """Headers that say which platform relayed the call — never their secrets.
    cf-worker names the Cloudflare zone of a Worker-based gateway; for other
    x-*/smithery-* headers only the names are kept."""
    try:
        from fastmcp.server.dependencies import get_http_request

        h = get_http_request().headers
    except Exception:
        return {}
    out: dict[str, Any] = {}
    # The HTTP Via header goes to via_header: "via" is our gateway/direct label.
    for name, field in (("cf-worker", "cf_worker"), ("mcp-protocol-version",
                        "mcp_protocol_version"), ("via", "via_header")):
        if h.get(name):
            out[field] = h.get(name)[:80]
    extra = sorted(k for k in h.keys()
                   if k.startswith(("x-", "smithery")) and k not in ("x-forwarded-for",
                   "x-forwarded-proto", "x-cloud-trace-context", "x-forwarded-host"))
    if extra:
        out["header_names"] = extra[:20]
    return out


class ClientInfoLogMiddleware(Middleware):
    """Log what each client says it is at initialize — the MCP handshake's
    self-identification (clientInfo name/version). Stateless HTTP means tool
    calls do not carry it, so it is logged here and joined later by
    client_hash / gateway_key_hash and time. Cloud Logging only; nothing is
    written to Firestore."""

    async def on_initialize(self, context: MiddlewareContext, call_next):
        try:
            from src.tools.analytics import _client_hash, transport_fields

            params = context.message.params
            ci = params.client_info
            record = {
                "client_name": (ci.name or "")[:80],
                "client_title": (getattr(ci, "title", None) or "")[:80],
                "client_version": (ci.version or "")[:40],
                "client_website": (getattr(ci, "website_url", None) or "")[:120],
                "protocol_version": params.protocol_version,
                "capabilities": sorted(params.capabilities.model_dump(exclude_none=True)),
                "client_hash": _client_hash(),
                **transport_fields(),
                **_header_fingerprint(),
            }
            logger.info("mcp_initialize %s", json.dumps(record, ensure_ascii=False))
        except Exception:
            logger.debug("initialize not logged", exc_info=True)
        return await call_next(context)


class ArgumentRepairMiddleware(Middleware):
    def __init__(self, valid_args: dict[str, list[str]] | None = None) -> None:
        self.valid_args = valid_args or {}

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        from src.tools.analytics import CLIENT_INFO, REPAIRS, client_info_from_meta

        msg = context.message
        # FastMCP rebuilds context.message with its own _meta, so read the
        # client's request _meta from the request context instead.
        meta = None
        try:
            rc = context.fastmcp_context.request_context if context.fastmcp_context else None
            meta = rc.meta if rc is not None else None
        except Exception:
            pass
        CLIENT_INFO.set(client_info_from_meta(meta))
        args = dict(msg.arguments or {})
        fixed, repairs = repair_arguments(msg.name, args)
        REPAIRS.set(repairs or None)
        if repairs:
            logger.info("repaired tool arguments %s: %s", msg.name, repairs)
            context = context.copy(message=msg.model_copy(update={"arguments": fixed}))
        try:
            return await call_next(context)
        except ValidationError as exc:
            if msg.name != "submit_feedback":   # untracked tool; its args are free text
                try:
                    _record_rejection(msg.name, args, exc)
                except Exception:
                    logger.debug("rejection not recorded", exc_info=True)
            hint = rejection_hint(msg.name, fixed, self.valid_args.get(msg.name, []))
            if not hint:
                raise
            # Hint first: the pydantic dump after it is long and agents skim.
            raise ValidationError(f"{hint}\n{exc}", log_level=logging.WARNING) from exc.__cause__
