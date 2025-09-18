from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

from app.services.project_service import get_all_org_projects
from app.services.organization_member_service import get_members_for_org

# Helper to normalize empty lists → None (means 'All')
def _norm_list(v: Optional[List[str]]) -> Optional[List[str]]:
	if v is None: 
		return None
	if isinstance(v, list):
		clean = [str(x) for x in v if x not in (None, "")]
		return clean or None
	return None

def _in_or_all(query, column: str, values: Optional[List[str]]):
	if values:
		return query.in_(column, values)
	return query

def _between_or_all(query, column: str, start: Optional[datetime], end: Optional[datetime]):
	if start and end:
		return query.gte(column, start.isoformat()).lte(column, end.isoformat())
	if start and not end:
		return query.gte(column, start.isoformat())
	if end and not start:
		return query.lte(column, end.isoformat())
	return query

async def _get_project_members_map(project_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
	supabase = get_supabase_client()
	members_map: Dict[str, List[Dict[str, Any]]] = {}
	if not project_ids:
		return members_map
	def op():
		return supabase.from_("project_members").select("*").in_("project_id", project_ids).execute()
	res = await safe_supabase_operation(op, "Failed to fetch project members")
	rows = res.data or []
	for r in rows:
		pid = r.get("project_id")
		if pid not in members_map:
			members_map[pid] = []
		members_map[pid].append(r)
	return members_map

def _member_id_candidates(member_row: Dict[str, Any]) -> Set[str]:
	# Try matching by user_id primarily; also accept email/username if present to match bug.assignee
	ids: Set[str] = set()
	uid = member_row.get("user_id")
	email = member_row.get("email")
	username = member_row.get("username")
	if uid: ids.add(str(uid))
	if email: ids.add(str(email))
	if username: ids.add(str(username))
	return ids

def _project_task_item(t: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"id": t.get("task_id") or t.get("id"),
		"title": t.get("title"),
		"status": t.get("status"),
		"priority": t.get("priority"),
		"project_id": t.get("project_id"),
	}

def _project_bug_item(b: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"id": b.get("bug_id") or b.get("id"),
		"title": b.get("title"),
		"status": b.get("status"),
		"priority": b.get("priority"),
		"project_id": b.get("project_id"),
	}

async def get_org_reports(filters: Dict[str, Any]) -> Dict[str, Any]:
	org_id: str = filters.get("org_id")
	if not org_id:
		return {"projects": []}

	project_ids: Optional[List[str]] = _norm_list(filters.get("project_ids"))
	member_ids: Optional[List[str]] = _norm_list(filters.get("member_ids"))
	date_from: Optional[datetime] = filters.get("date_from")
	date_to: Optional[datetime] = filters.get("date_to")
	task_statuses: Optional[List[str]] = _norm_list(filters.get("task_statuses"))
	task_priorities: Optional[List[str]] = _norm_list(filters.get("task_priorities"))
	bug_statuses: Optional[List[str]] = _norm_list(filters.get("bug_statuses"))
	bug_priorities: Optional[List[str]] = _norm_list(filters.get("bug_priorities"))

	# 1) Projects in the org
	projects_cards = await get_all_org_projects(org_id)
	all_project_ids = [p.project_id for p in projects_cards]
	target_project_ids = project_ids or all_project_ids

	# 2) Members: we pull org-level members; later limit to those present in each project via project_members
	org_members = await get_members_for_org(org_id, limit=100000)
	# Map: user_id -> org_member row
	org_member_by_id: Dict[str, Dict[str, Any]] = {str(m.get("user_id")): m for m in org_members if m.get("user_id")}

	# 3) Per-project members
	pm_map = await _get_project_members_map(target_project_ids)

	supabase = get_supabase_client()

	# 4) Fetch tasks and bugs scoped to target projects, with filters
	# Tasks live in task_card_view; use 'project_id', 'assignee', 'status', 'priority', 'created_at'
	def tasks_op():
		q = supabase.from_("task_card_view").select("*").in_("project_id", target_project_ids)
		q = _in_or_all(q, "status", task_statuses)
		q = _in_or_all(q, "priority", task_priorities)
		q = _between_or_all(q, "created_at", date_from, date_to)
		return q.execute()

	# Bugs live in 'bugs'; use 'project_id','assignee','status','priority','created_at'
	def bugs_op():
		q = supabase.from_("bugs").select("*").in_("project_id", target_project_ids)
		q = _in_or_all(q, "status", bug_statuses)
		q = _in_or_all(q, "priority", bug_priorities)
		q = _between_or_all(q, "created_at", date_from, date_to)
		return q.execute()

	tasks_res, bugs_res = await safe_supabase_operation(tasks_op, "Failed to fetch tasks"), await safe_supabase_operation(bugs_op, "Failed to fetch bugs")
	all_tasks: List[Dict[str, Any]] = tasks_res.data or []
	all_bugs: List[Dict[str, Any]] = bugs_res.data or []

	# 5) Build result
	result_projects: List[Dict[str, Any]] = []
	for p in projects_cards:
		if p.project_id not in target_project_ids:
			continue

		project_member_rows = pm_map.get(p.project_id, [])
		# If member_ids filter is applied, restrict to those user_ids
		if member_ids:
			project_member_rows = [m for m in project_member_rows if str(m.get("user_id")) in member_ids]

		# Build member details using org member info if available
		members_out: List[Dict[str, Any]] = []
		for pm in project_member_rows:
			user_id = str(pm.get("user_id"))
			org_member = org_member_by_id.get(user_id) or {}
			member_display = {
				"user_id": user_id,
				"email": org_member.get("email"),
				"role": pm.get("role"),
				"designation": org_member.get("designation"),
			}
			cands = _member_id_candidates({**org_member, **pm})

			# Filter tasks for member within this project
			mtasks = [t for t in all_tasks if t.get("project_id") == p.project_id and (str(t.get("assignee")) in cands if t.get("assignee") is not None else False)]
			# Filter bugs similarly (assignee may be username/email or user_id)
			mbugs = [b for b in all_bugs if b.get("project_id") == p.project_id and (str(b.get("assignee")) in cands if b.get("assignee") is not None else False)]

			# Categorization helpers
			def group_count(rows: List[Dict[str, Any]], key: str, allowed: Optional[List[str]]):
				counts: Dict[str, int] = {}
				allowed_set = set(allowed) if allowed else set()
				for r in rows:
					val = str(r.get(key) or "").strip().lower()
					if not val:
						val = "others"
					elif allowed and val not in allowed_set:
						val = "others"
					counts[val] = counts.get(val, 0) + 1
				# Ensure 'others' present if we had any rows not matching
				if rows and allowed:
					total = sum(counts.values())
					matched = sum(v for k, v in counts.items() if k != "others")
					if total > matched:
						counts["others"] = counts.get("others", 0)
				return counts

			member_out = {
				**member_display,
				"tasks_by_status": group_count(mtasks, "status", task_statuses),
				"tasks_by_priority": group_count(mtasks, "priority", task_priorities),
				"bugs_by_status": group_count(mbugs, "status", bug_statuses),
				"bugs_by_priority": group_count(mbugs, "priority", bug_priorities),
				"tasks_total": len(mtasks),
				"bugs_total": len(mbugs),
				"tasks_items": [_project_task_item(t) for t in mtasks[:50]],
				"bugs_items": [_project_bug_item(b) for b in mbugs[:50]],
			}
			members_out.append(member_out)

		result_projects.append({
			"project_id": p.project_id,
			"project_name": p.name,
			"members": members_out,
		})

	return {
		"org_id": org_id,
		"filters": {
			"project_ids": target_project_ids,
			"member_ids": member_ids or [],
			"date_from": date_from.isoformat() if date_from else None,
			"date_to": date_to.isoformat() if date_to else None,
			"task_statuses": task_statuses or [],
			"task_priorities": task_priorities or [],
			"bug_statuses": bug_statuses or [],
			"bug_priorities": bug_priorities or [],
		},
		"projects": result_projects,
	}

# --- Timesheets aggregation (derived from tasks) ---
async def get_org_timesheets(filters: Dict[str, Any]) -> Dict[str, Any]:
	org_id: str = filters.get("org_id")
	if not org_id:
		return {"users": []}

	project_ids: Optional[List[str]] = _norm_list(filters.get("project_ids"))
	member_ids: Optional[List[str]] = _norm_list(filters.get("member_ids"))
	date_from: Optional[datetime] = filters.get("date_from")
	date_to: Optional[datetime] = filters.get("date_to")
	# Optional filter to narrow statuses in timesheets view
	task_statuses: Optional[List[str]] = _norm_list(filters.get("task_statuses"))

	# 1) Resolve projects in org
	projects_cards = await get_all_org_projects(org_id)
	all_project_ids = [p.project_id for p in projects_cards]
	target_project_ids = project_ids or all_project_ids

	# 2) Org members metadata
	org_members = await get_members_for_org(org_id, limit=100000)
	org_member_by_id: Dict[str, Dict[str, Any]] = {str(m.get("user_id")): m for m in org_members if m.get("user_id")}

	# 3) Pull tasks from task_card_view for the projects/date range; group by assignee
	supabase = get_supabase_client()

	def tasks_op():
		q = supabase.from_("task_card_view").select("*").in_("project_id", target_project_ids)
		q = _between_or_all(q, "created_at", date_from, date_to)
		if member_ids:
			q = q.in_("assignee", member_ids)
		if task_statuses:
			q = q.in_("status", task_statuses)
		return q.execute()

	res = await safe_supabase_operation(tasks_op, "Failed to fetch tasks for timesheets")
	rows: List[Dict[str, Any]] = res.data or []

	# 4) Group tasks by user and status buckets
	by_user: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
	for r in rows:
		assignee_raw = r.get("assignee")
		if assignee_raw is None:
			continue
		uid = str(assignee_raw)
		if uid not in by_user:
			by_user[uid] = {"in_progress": [], "completed": [], "blockers": []}
		item = {
			"id": r.get("task_id") or r.get("id"),
			"title": r.get("title"),
			"project": r.get("project_name"),
			"project_id": r.get("project_id"),
			"hours_logged": None,
			"status": r.get("status"),
			"priority": r.get("priority"),
		}
		status = str(r.get("status") or "").lower()
		if status in ("in_progress", "on_hold"):
			by_user[uid]["in_progress"].append(item)
		elif status in ("completed",):
			by_user[uid]["completed"].append(item)
		elif status in ("blocked",):
			by_user[uid]["blockers"].append(item)
		else:
			by_user[uid]["in_progress"].append(item)

	# 5) Build users output
	users_out: List[Dict[str, Any]] = []
	for uid, buckets in by_user.items():
		meta = org_member_by_id.get(uid, {})
		name = meta.get("username") or meta.get("email") or uid
		email = meta.get("email")
		role = meta.get("role")
		designation = meta.get("designation")
		users_out.append({
			"user_id": uid,
			"name": name,
			"email": email,
			"avatar_initials": (name or uid)[:2].upper(),
			"role": role,
			"designation": designation,
			"total_hours_today": None,
			"total_hours_week": None,
			"in_progress": buckets.get("in_progress", [])[:10],
			"completed": buckets.get("completed", [])[:10],
			"blockers": buckets.get("blockers", [])[:10],
		})

	return {
		"org_id": org_id,
		"filters": {
			"project_ids": target_project_ids,
			"member_ids": member_ids or [],
			"date_from": date_from.isoformat() if date_from else None,
			"date_to": date_to.isoformat() if date_to else None,
			"task_statuses": task_statuses or [],
		},
		"users": users_out,
	}