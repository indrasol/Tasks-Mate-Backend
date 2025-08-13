# app/services/history_utils.py
from hashlib import sha1
from datetime import datetime
from typing import Any, Dict, List

UPDATE_WHITELIST = [
    "title", "description", "status", "priority",
    "start_date", "due_date", "tags", "project_id"
]

def _norm(v: Any):
    if v is None: return None
    # Normalize dates to ISO date only for stable diffs
    if isinstance(v, datetime): return v.date().isoformat()
    return v

def compute_task_diff(before: Dict, after: Dict) -> List[Dict]:
    changes: List[Dict] = []
    for field in UPDATE_WHITELIST:
        old, new = _norm(before.get(field)), _norm(after.get(field))
        # Normalize array compare (tags)
        if isinstance(old, list): old = sorted(old)
        if isinstance(new, list): new = sorted(new)
        if old != new:
            changes.append({"field": field, "old": old, "new": new})
    return changes

def history_hash(task_id: str, action: str, metadata: Any, created_by: str) -> str:
    payload = f"{task_id}|{action}|{str(metadata)}|{created_by}"
    return sha1(payload.encode()).hexdigest()
