from typing import Any, Dict, List, Optional
from datetime import datetime, date
import logging
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

logger = logging.getLogger(__name__)


class GoalService:
    @staticmethod
    async def list_goals(
        org_id: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        due_start: Optional[date] = None,
        due_end: Optional[date] = None,
    ) -> Dict[str, Any]:
        supabase = get_supabase_client()

        # Use RPC or build SQL via postgrest filter limitations; here we assume RPC view exists
        # Fallback: basic list with limited filters
        try:
            # Build base query
            def query_list():
                query = supabase.from_("goals").select("*")\
                    .eq("org_id", org_id)\
                    .order("updated_at", desc=True)

                if status and status != 'all':
                    query = query.eq("status", status)
                if due_start:
                    query = query.gte("due_date", due_start.isoformat())
                if due_end:
                    query = query.lte("due_date", due_end.isoformat())

                # Pagination
                from_idx = (page - 1) * page_size
                to_idx = from_idx + page_size - 1
                query = query.range(from_idx, to_idx)

                return query.execute()

            result = await safe_supabase_operation(query_list, "Failed to list goals")

            items = result.data or []

            # Filter by q (client-side if not supported) and by assignment user if needed
            if q:
                q_lower = q.lower()
                items = [g for g in items if (g.get('title','') or '').lower().find(q_lower) >= 0 or (g.get('description','') or '').lower().find(q_lower) >= 0]

            # Join latest progress and assignees via additional queries (simplified)
            goal_ids = [g.get('id') for g in items if g.get('id')]
            latest_by_goal: Dict[str, int] = {}
            assignees_by_goal: Dict[str, List[Dict[str, str]]] = {}

            if goal_ids:
                def get_latest():
                    return supabase.from_("goal_updates").select("goal_id, progress, created_at").in_("goal_id", goal_ids).order("created_at", desc=True).execute()

                latest = await safe_supabase_operation(get_latest, "Failed to get latest updates")
                for row in (latest.data or []):
                    gid = row.get('goal_id')
                    if gid not in latest_by_goal:
                        latest_by_goal[gid] = int(row.get('progress') or 0)

                def get_assignees():
                    return supabase.from_("goal_assignees").select("goal_id, user_id").in_("goal_id", goal_ids).execute()

                assignments = await safe_supabase_operation(get_assignees, "Failed to get assignees")
                for row in (assignments.data or []):
                    gid = row.get('goal_id')
                    if user_id and str(row.get('user_id')) != str(user_id):
                        # Apply user filter
                        continue
                    assignees_by_goal.setdefault(gid, []).append({
                        'userId': str(row.get('user_id')),
                    })

            # If user filter is set, drop items without assignments for that user
            if user_id:
                items = [g for g in items if assignees_by_goal.get(g.get('id'))]

            # Map fields to frontend shape
            mapped = []
            for g in items:
                mapped.append({
                    'id': g.get('id'),
                    'orgId': g.get('org_id'),
                    'title': g.get('title'),
                    'description': g.get('description'),
                    'status': g.get('status'),
                    'startDate': g.get('start_date'),
                    'dueDate': g.get('due_date'),
                    'visibility': g.get('visibility') or 'org',
                    'progress': latest_by_goal.get(g.get('id'), 0),
                    'assignees': assignees_by_goal.get(g.get('id'), []),
                    'category': g.get('category') or [],
                    'subCategory': g.get('sub_category') or [],
                    'sectionId': g.get('section_id'),
                    'createdBy': g.get('created_by'),
                    'createdAt': g.get('created_at'),
                    'updatedAt': g.get('updated_at'),
                })

            # Total count (approximate without complex filters)
            total = len(mapped)

            return {
                'items': mapped,
                'total': total,
                'page': page,
                'pageSize': page_size,
            }

        except Exception as e:
            logger.error(f"Error listing goals: {str(e)}")
            raise

    @staticmethod
    async def create_goal(org_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        supabase = get_supabase_client()
        now = datetime.utcnow().isoformat()
        try:
            def to_iso(value):
                try:
                    return value.isoformat() if hasattr(value, 'isoformat') else value
                except Exception:
                    return value

            def insert_goal():
                return supabase.from_("goals").insert({
                    'org_id': org_id,
                    'title': payload.get('title'),
                    'description': payload.get('description'),
                    'status': payload.get('status', 'active'),
                    'start_date': to_iso(payload.get('startDate')),
                    'due_date': to_iso(payload.get('dueDate')),
                    'visibility': payload.get('visibility', 'org'),
                    'category': payload.get('category') or [],
                    'sub_category': payload.get('subCategory') or [],
                    'section_id': payload.get('sectionId'),
                    'created_by': user_id,
                    'created_at': now,
                    'updated_at': now,
                }).execute()

            goal_res = await safe_supabase_operation(insert_goal, "Failed to create goal")

            if not goal_res.data:
                raise Exception("Failed to create goal")

            # Supabase may return a dict (with .single()) or a list if API behavior changes
            goal_data = goal_res.data
            if isinstance(goal_data, list):
                if len(goal_data) == 0:
                    raise Exception("Failed to create goal: empty response")
                goal = goal_data[0]
            else:
                goal = goal_data

            # Assign assignees if provided (no roles)
            assignees = payload.get('assignees') or []
            rows = []
            for a in assignees:
                rows.append({'goal_id': goal['id'], 'user_id': a.get('userId')})

            if rows:
                def insert_assign():
                    return supabase.from_("goal_assignees").insert(rows).execute()
                await safe_supabase_operation(insert_assign, "Failed to insert assignments")

            return goal
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}")
            raise

    @staticmethod
    async def update_goal(org_id: str, goal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        supabase = get_supabase_client()
        try:
            update_data: Dict[str, Any] = {}
            for src, dst in [
                ('title', 'title'), ('description', 'description'), ('status', 'status'),
                ('startDate', 'start_date'), ('dueDate', 'due_date'), ('visibility', 'visibility')
            ]:
                if src in payload and payload.get(src) is not None:
                    update_data[dst] = payload.get(src)

            if update_data:
                update_data['updated_at'] = datetime.utcnow().isoformat()

                def do_update():
                    return supabase.from_("goals").update(update_data).eq('id', goal_id).eq('org_id', org_id).execute()

                res = await safe_supabase_operation(do_update, "Failed to update goal")
                updated = res.data
            else:
                # No field updates requested
                def get_current():
                    return supabase.from_("goals").select('*').eq('id', goal_id).eq('org_id', org_id).single().execute()
                res = await safe_supabase_operation(get_current, "Failed to fetch goal")
                updated = res.data

            # Update assignments if provided
            if 'assignees' in payload and isinstance(payload.get('assignees'), list):
                def del_assign():
                    return supabase.from_("goal_assignees").delete().eq('goal_id', goal_id).execute()
                await safe_supabase_operation(del_assign, "Failed to clear assignments")

                new_rows = [{'goal_id': goal_id, 'user_id': a.get('userId')} for a in payload.get('assignees')]
                if new_rows:
                    def ins_assign():
                        return supabase.from_("goal_assignees").insert(new_rows).execute()
                    await safe_supabase_operation(ins_assign, "Failed to set assignments")

            return updated
        except Exception as e:
            logger.error(f"Error updating goal: {str(e)}")
            raise

    @staticmethod
    async def list_sections(org_id: str) -> List[Dict[str, Any]]:
        supabase = get_supabase_client()
        def do_list():
            return supabase.from_("goal_sections").select("*").eq("org_id", org_id).order("order", desc=False).execute()
        res = await safe_supabase_operation(do_list, "Failed to list sections")
        return res.data or []

    @staticmethod
    async def create_section(org_id: str, title: str, order: int = 0) -> Dict[str, Any]:
        supabase = get_supabase_client()
        def do_insert():
            return supabase.from_("goal_sections").insert({
                'org_id': org_id, 'title': title, 'order': order
            }).execute()
        res = await safe_supabase_operation(do_insert, "Failed to create section")
        return res.data

    @staticmethod
    async def update_section(org_id: str, section_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        supabase = get_supabase_client()
        update_data: Dict[str, Any] = {}
        if 'title' in data and data.get('title') is not None:
            update_data['title'] = data['title']
        if 'order' in data and data.get('order') is not None:
            update_data['order'] = data['order']
        def do_update():
            return supabase.from_("goal_sections").update(update_data).eq('id', section_id).eq('org_id', org_id).execute()
        res = await safe_supabase_operation(do_update, "Failed to update section")
        return res.data

    @staticmethod
    async def delete_section(org_id: str, section_id: str) -> None:
        supabase = get_supabase_client()
        def do_delete():
            return supabase.from_("goal_sections").delete().eq('id', section_id).eq('org_id', org_id).execute()
        await safe_supabase_operation(do_delete, "Failed to delete section")

    @staticmethod
    async def delete_goal(org_id: str, goal_id: str) -> None:
        supabase = get_supabase_client()
        try:
            def do_delete():
                return supabase.from_("goals").delete().eq('id', goal_id).eq('org_id', org_id).execute()
            await safe_supabase_operation(do_delete, "Failed to delete goal")
        except Exception as e:
            logger.error(f"Error deleting goal: {str(e)}")
            raise

    @staticmethod
    async def add_update(org_id: str, goal_id: str, user_id: str, progress: int, note: Optional[str]) -> Dict[str, Any]:
        supabase = get_supabase_client()
        try:
            def do_insert():
                return supabase.from_("goal_updates").insert({
                    'goal_id': goal_id,
                    'user_id': user_id,
                    'progress': progress,
                    'note': note,
                }).execute()
            res = await safe_supabase_operation(do_insert, "Failed to add update")
            return res.data
        except Exception as e:
            logger.error(f"Error adding goal update: {str(e)}")
            raise

    @staticmethod
    async def list_updates(org_id: str, goal_id: str) -> List[Dict[str, Any]]:
        supabase = get_supabase_client()
        try:
            def do_list():
                return supabase.from_("goal_updates").select("*").eq('goal_id', goal_id).order('created_at', desc=True).execute()
            res = await safe_supabase_operation(do_list, "Failed to list updates")
            return res.data or []
        except Exception as e:
            logger.error(f"Error listing goal updates: {str(e)}")
            raise



