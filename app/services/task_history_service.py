import datetime
import re
from typing import Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.task_history import TaskHistoryInDB
from app.utils.history_utils import history_hash



async def _generate_sequential_history_id() -> str:
    """Generate a random history ID with prefix 'H' and 5 digits, ensuring uniqueness."""
    supabase = get_supabase_client()
    digits = 5
    for _ in range(10):
        candidate = f"H{__import__('random').randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("tasks_history").select("history_id").eq("history_id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify history id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"H{ts:0{digits}d}"

SYSTEM_ALIASES = {
    "system": "System",
    "system-bot": "System Bot",
    "scheduler": "Recurring Task Bot",
    "automation": "Automation",
}

def make_actor_display(raw: str | None) -> str:
    """
    Produce a nice, UI-ready display name from a raw identifier (email/username/id).
    - "rithin.sai@example.com" -> "Rithin Sai"
    - "john_doe" -> "John Doe"
    - "system" -> "System"
    Falls back to "Someone" if nothing usable.
    """
    if not raw:
        return "Someone"

    low = raw.strip().lower()
    if low in SYSTEM_ALIASES:
        return SYSTEM_ALIASES[low]

    # Prefer the part before '@' for emails
    if "@" in raw:
        raw = raw.split("@", 1)[0]

    # Split on common separators
    parts = re.split(r"[.\-_]+", raw.strip())
    parts = [p for p in parts if p]
    if not parts:
        return "Someone"

    # Title-case each part
    pretty = " ".join(p[:1].upper() + p[1:] for p in parts)

    # Gentle length cap to keep timeline tidy
    if len(pretty) > 60:
        pretty = pretty[:57].rstrip() + "..."

    return pretty
async def record_history(*, task_id: str, action: str, created_by: str,
                         title: str | None = None, metadata: list | dict | None = None,
                         actor_display: str | None = None):
    supabase = get_supabase_client()

    # Normalize metadata to a list
    meta_list = metadata if isinstance(metadata, list) else [metadata] if metadata else []

    # Generate sequential history id
    history_id = await _generate_sequential_history_id()

    # Timestamps
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    actor_display = actor_display or make_actor_display(created_by)
    body = {
        "history_id": history_id,
        "task_id": task_id,
        "action": action,
        "title": title,
        "metadata": meta_list,
        "created_by": created_by,
        "actor_display": actor_display,
        "created_at": now,
        "updated_at": now,
    }
    print("History Body", body)
    body["hash_id"] = history_hash(task_id, action, meta_list, created_by)  # idempotency

    # upsert w/ hash guard
    return (
        supabase.from_("tasks_history")
        .upsert(body, on_conflict="hash_id")
        .execute()
    )


async def create_task_history(data: dict):

    data["history_id"] = await _generate_sequential_history_id()

    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    # Support new 'type' field; keep legacy callers that sent event in 'title'
    # If both are present, assume 'title' is the human task title, 'type' is the event type
    if "type" not in data and data.get("title") and data.get("title") in [
        "created", "updated", "deleted", "subtask_added", "subtask_removed",
        "attachment_created", "attachment_updated", "attachment_deleted"
    ]:
        data["type"] = data["title"]
        # Optionally clear title so it can be used for task title; leave as-is if caller set it intentionally

    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task history")

async def get_task_history(task_id: str, task_title: Optional[str] = None):
    supabase = get_supabase_client()
    def op():
        # Return newest first so UI can show latest activity at the top
        query = (
            supabase
            .from_("tasks_history")
            .select("*")
            .eq("task_id", task_id)
        )
        if task_title:
            query = query.eq("title", task_title)
        return query.order("created_at", desc=True).order("history_id", desc=True).execute()
    result = await safe_supabase_operation(op, "Failed to fetch task history")

    items = result.data or []
    # print("Items", items)

    # Defensive normalization: sometimes libraries serialize list-of-objects as a JSON string.
    # Keep the API contract: metadata should always be a list[dict] for the UI.
    normalized = []
    for item in items:
        md = item.get("metadata")
        if isinstance(md, str):
            try:
                import json
                parsed = json.loads(md)
                if isinstance(parsed, list):
                    item["metadata"] = parsed
                elif isinstance(parsed, dict) or parsed is None:
                    item["metadata"] = [parsed] if parsed else []
                else:
                    item["metadata"] = []
            except Exception:
                item["metadata"] = []
        elif md is None:
            item["metadata"] = []
        normalized.append(TaskHistoryInDB(**item))

    return normalized
# async def update_task_history(history_id: str, data: dict):
#     supabase = get_supabase_client()
#     def op():
#         return supabase.from_("tasks_history").update(data).eq("history_id", history_id).execute()
#     return await safe_supabase_operation(op, "Failed to update task history")

# async def delete_task_history(history_id: str):
#     supabase = get_supabase_client()
#     def op():
#         return supabase.from_("tasks_history").delete().eq("history_id", history_id).execute()
#     return await safe_supabase_operation(op, "Failed to delete task history")