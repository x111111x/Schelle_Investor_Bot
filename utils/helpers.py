"""Shared utilities for Project Alpha."""

import functools
import re
import time
from datetime import datetime

import pytz

CHINA_TZ = pytz.timezone("Asia/Shanghai")

# Characters that must be escaped in Telegram MarkdownV2
_MD2_ESCAPE = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


def escape_md2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    return _MD2_ESCAPE.sub(r"\\\1", str(text))


def now_china() -> datetime:
    """Return the current datetime in Asia/Shanghai timezone."""
    return datetime.now(CHINA_TZ)


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff for network calls."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            wait = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        time.sleep(wait)
                        wait *= backoff
            raise last_exc
        return wrapper
    return decorator
