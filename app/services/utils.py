from datetime import datetime, timedelta

from app.models.enums import InviteStatusEnum

def inject_audit_fields(data: dict, user_id: str = None, action: str = None, extra: dict = None):
    now = datetime.utcnow().isoformat()
    expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
    if action == "create":
        if user_id:
            data["created_by"] = user_id
        data["created_at"] = now
    elif action == "create_proj":
        if user_id:
            data["created_by"] = user_id
        data["created_at"] = now
    elif action == "update":
        if user_id:
            data["updated_by"] = user_id
        data["updated_at"] = now
    elif action == "delete":
        if user_id:
            data["deleted_by"] = user_id
        data["deleted_at"] = now
    elif action == "accept":
        if user_id:
            data["accepted_by"] = user_id
        data["accepted_at"] = now
        data["invite_status"] = InviteStatusEnum.ACCEPTED
    # elif action == "approve":
    #     data["approved_by"] = user_id
    #     data["approved_at"] = now
    elif action == "invite":
        if user_id:
            data["invited_by"] = user_id
        data["invited_at"] = now
        data["expires_at"] = expiry
        data["invite_status"] = InviteStatusEnum.PENDING.value

    elif action == "invite_org":
        if user_id:
            data["invited_by"] = user_id
        data["sent_at"] = now
        data["expires_at"] = expiry
        data["invite_status"] = InviteStatusEnum.PENDING.value

    if extra:
        data.update(extra)
    
    if "org_id" in data and data["org_id"]:
        data["org_id"] = str(data["org_id"])

    if "designation" in data and data["designation"]:
        data["designation"] = str(data["designation"])

    if "role" in data and data["role"]:
        data["role"] = str(data["role"])

    if "user_id" in data and data["user_id"]:
        data["user_id"] = str(data["user_id"])


    return data