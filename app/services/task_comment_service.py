import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation


async def _generate_sequential_comment_id() -> str:
    """Generate a random comment ID with prefix 'C' and 5 digits, ensuring uniqueness."""
    supabase = get_supabase_client()
    digits = 5
    for _ in range(10):
        candidate = f"C{__import__('random').randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("task_comments").select("comment_id").eq("comment_id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify comment id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"C{ts:0{digits}d}"

async def create_task_comment(data: dict):
    """Create a new comment or reply."""
    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    # Generate comment_id if missing
    if not data.get("comment_id"):
        data["comment_id"] = await _generate_sequential_comment_id()

    # Some databases may still expect the legacy 'comment' column
    if data.get("content") and not data.get("comment"):
        data["comment"] = data["content"]
        
    # If this is a reply, verify the parent exists
    parent_id = data.get("parent_comment_id")
    if parent_id:
        parent = await get_task_comment(parent_id)
        if not parent.data:
            raise ValueError("Parent comment not found")
            
        # Ensure we're not creating a circular reference
        if parent.data.get("parent_comment_id"):
            raise ValueError("Cannot reply to a reply")

    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").insert(data).execute()
        
    result = await safe_supabase_operation(op, "Failed to create task comment")
    
    # If this is a reply, update the parent's updated_at
    if parent_id and result.data:
        await update_task_comment(parent_id, {"updated_at": data["created_at"]})
    
    return result

async def get_task_comment(comment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").select("*").eq("comment_id", comment_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task comment")

async def update_task_comment(comment_id: str, data: dict):
    # Stamp updated_at automatically if not provided
    if "updated_at" not in data:
        data["updated_at"] = datetime.datetime.utcnow().isoformat()
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").update(data).eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to update task comment")

async def delete_task_comment(comment_id: str, _audit: dict | None = None):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").delete().eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task comment")

async def get_comments_for_task(task_id, search=None, limit=100, offset=0, sort_by="created_at", sort_order="asc"):
    """Fetch comments for a task, including replies in a nested structure."""
    supabase = get_supabase_client()
    
    # First, fetch all comments for the task
    query = supabase.from_("task_comments").select("*")\
        .eq("task_id", task_id)
        
    if search:
        query = query.ilike("content", f"%{search}%")
    
    # Sort by creation date by default
    query = query.order(sort_by, desc=(sort_order == "desc"))
    
    # Get all comments (we'll handle pagination after building the tree)
    result = await safe_supabase_operation(
        lambda: query.execute(),
        "Failed to fetch task comments"
    )
    
    if not result or not result.data:
        return []
    
    # Build comment tree
    comments_map = {}
    root_comments = []
    
    # First pass: map all comments by ID
    for comment in result.data:
        comment['replies'] = []
        comments_map[comment['comment_id']] = comment
    
    # Second pass: build the tree
    for comment in result.data:
        parent_id = comment.get('parent_comment_id')
        if parent_id and parent_id in comments_map:
            # This is a reply, add it to its parent's replies
            comments_map[parent_id]['replies'].append(comment)
        elif not parent_id:
            # This is a root-level comment
            root_comments.append(comment)
    
    # Sort replies by creation date
    for comment in comments_map.values():
        comment['replies'].sort(key=lambda x: x.get('created_at', ''))
    
    # Apply pagination to root comments only
    paginated_comments = root_comments[offset:offset + limit]
    
    return paginated_comments