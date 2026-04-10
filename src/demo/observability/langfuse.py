"""Langfuse observability integration (v4.x API).

Uses the @observe decorator which auto-creates spans and captures
LLM calls, token usage, and latency per agent node.

If LANGFUSE_HOST / LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are not set
or the server is unreachable, the decorator is a no-op and the demo continues.
"""
import functools
import logging
import os
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

_langfuse_enabled = False

try:
    from langfuse import Langfuse, observe as _lf_observe
    _lf_host = os.environ.get("LANGFUSE_HOST", "")
    _lf_pub = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    _lf_sec = os.environ.get("LANGFUSE_SECRET_KEY", "")
    if _lf_host and _lf_pub and _lf_sec:
        _langfuse_client = Langfuse(
            host=_lf_host,
            public_key=_lf_pub,
            secret_key=_lf_sec,
        )
        _langfuse_enabled = True
    else:
        logger.info("Langfuse env vars not set — observability disabled")
except Exception as exc:
    logger.warning("Langfuse init failed: %s", exc)


def trace_agent(name: str | None = None) -> Callable:
    """Decorator that wraps an agent node function with a Langfuse span.

    Usage:
        @trace_agent("regulatory_analyst")
        def regulatory_analyst_node(state: ComplianceState) -> dict:
            ...

    If Langfuse is unavailable, the function runs undecorated.
    """
    def decorator(fn: Callable) -> Callable:
        if not _langfuse_enabled:
            return fn

        span_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                decorated = _lf_observe(name=span_name)(fn)
                return decorated(*args, **kwargs)
            except Exception as exc:
                logger.warning("Langfuse span failed for %s: %s — running untraced", span_name, exc)
                return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_trace_url(run_id: str) -> str:
    """Return the Langfuse trace URL for a given run_id, or empty string."""
    if not _langfuse_enabled:
        return ""
    try:
        host = os.environ.get("LANGFUSE_HOST", "http://localhost:3001")
        return f"{host}/trace/{run_id}"
    except Exception:
        return ""
