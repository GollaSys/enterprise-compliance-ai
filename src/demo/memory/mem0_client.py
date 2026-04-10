"""mem0 long-term memory wrapper.

All calls are fire-and-forget with silent exception handling.
The demo never crashes from memory failures — it just logs and continues.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Mem0Client:
    """Thin wrapper around mem0 Memory with graceful degradation."""

    def __init__(self, data_path: str = "./data/mem0") -> None:
        try:
            from mem0 import Memory
            config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "compliance_demo",
                        "path": data_path,
                    },
                }
            }
            self._memory = Memory.from_config(config)
        except Exception as exc:
            logger.warning("mem0 init failed — long-term memory unavailable: %s", exc)
            self._memory = None

    def search(self, query: str, user_id: str = "demo") -> list[dict[str, Any]]:
        """Search prior findings. Returns [] on any failure."""
        if self._memory is None:
            return []
        try:
            results = self._memory.search(query, user_id=user_id)
            # mem0 returns dict with "results" key in some versions
            if isinstance(results, dict):
                return results.get("results", [])
            return results if isinstance(results, list) else []
        except Exception as exc:
            logger.warning("mem0 search failed: %s", exc)
            return []

    def add(self, text: str, user_id: str = "demo", metadata: dict | None = None) -> bool:
        """Store a finding. Returns False on any failure."""
        if self._memory is None:
            return False
        try:
            self._memory.add(text, user_id=user_id, metadata=metadata or {})
            return True
        except Exception as exc:
            logger.warning("mem0 add failed: %s", exc)
            return False
