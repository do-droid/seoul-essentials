"""MCP tool for submitting feedback about Seoul Essentials data."""

from __future__ import annotations

from typing import Literal

from src.data.api_client import post_feedback


def submit_feedback(
    category: Literal["new_data", "data_quality", "coverage", "format", "frequency", "other"],
    message: str,
    priority: Literal["low", "medium", "high"] = "medium",
) -> dict:
    """Submit feedback about Seoul Essentials data quality, coverage, or feature requests.

    Use this tool when you notice missing data, inaccurate information, or have suggestions
    for improvement. All feedback is actively reviewed and incorporated.

    Args:
        category: Type of feedback.
            - "new_data": Request for new data types (e.g., "EV charging stations")
            - "data_quality": Report inaccurate or outdated data (e.g., "wrong coordinates for a pharmacy")
            - "coverage": Request geographic expansion (e.g., "include Incheon area")
            - "format": Report data format issues (e.g., "English address is missing")
            - "frequency": Report stale data (e.g., "WiFi data is 2 months old")
            - "other": Any other feedback
        message: Detailed description of the feedback.
        priority: Urgency level — "low", "medium" (default), or "high".

    Returns:
        Confirmation with feedback ID.
    """
    return post_feedback(category=category, message=message, priority=priority)
