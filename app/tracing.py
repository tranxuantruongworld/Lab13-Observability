from __future__ import annotations

import os
from typing import Any

try:
    from langfuse.decorators import observe, langfuse_context
except Exception:  # pragma: no cover
    print("Langfuse not configured, using dummy tracing functions. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable tracing.")
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
