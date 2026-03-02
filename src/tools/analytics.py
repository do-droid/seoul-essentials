"""Analytics instrumentation decorator for MCP tools."""

from __future__ import annotations

import functools
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from src.data.api_client import post_analytics

logger = logging.getLogger(__name__)


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
                result_count = 1

            event = {
                "tool": func.__name__,
                "params": {k: v for k, v in kwargs.items() if v is not None},
                "result_count": result_count,
                "response_time_ms": elapsed_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if error_msg:
                event["error"] = error_msg

            # Fire-and-forget in background thread
            threading.Thread(
                target=post_analytics,
                args=(event,),
                daemon=True,
            ).start()

    return wrapper
