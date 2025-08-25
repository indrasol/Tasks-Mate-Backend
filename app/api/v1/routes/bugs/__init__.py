# This file makes the bugs directory a Python package

from .bug_router import router as bug_router
from .comment_router import router as comment_router
from .attachment_router import router as attachment_router
from .history_router import router as history_router
from .watcher_router import router as watcher_router

__all__ = [
    "bug_router",
    "comment_router",
    "attachment_router",
    "history_router",
    "watcher_router"
]
