from datetime import datetime

def inject_audit_fields(data: dict, user_id: str, action: str, extra: dict = None):
    now = datetime.utcnow().isoformat()
    if action == "create":
        data["created_by"] = user_id
        data["created_at"] = now
    elif action == "update":
        data["updated_by"] = user_id
        data["updated_at"] = now
    elif action == "delete":
        data["deleted_by"] = user_id
        data["deleted_at"] = now
    elif action == "accept":
        data["accepted_by"] = user_id
        data["accepted_at"] = now
    elif action == "approve":
        data["approved_by"] = user_id
        data["approved_at"] = now
    if extra:
        data.update(extra)
    return data