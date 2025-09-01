drop view if exists "public"."organization_dashboard_view";

alter table "public"."users" drop column "test_dummy";

create or replace view "public"."organization_dashboard_view" as  WITH series AS (
         SELECT (generate_series((date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone) - '5 mons'::interval), date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone), '1 mon'::interval))::date AS month_start
        ), kpis AS (
         SELECT o_1.org_id,
            count(DISTINCT t.task_id) AS total_tasks,
            count(DISTINCT p.project_id) FILTER (WHERE (p.status = ANY (ARRAY['in_progress'::project_status_enum, 'planning'::project_status_enum]))) AS active_projects_now,
            count(DISTINCT p.project_id) FILTER (WHERE (p.status = 'completed'::project_status_enum)) AS completed_projects_now,
            count(DISTINCT p.project_id) FILTER (WHERE (p.status = 'blocked'::project_status_enum)) AS blocked_projects_now,
            count(DISTINCT om.user_id) AS team_members,
            count(DISTINCT t.task_id) FILTER (WHERE (date_trunc('month'::text, t.created_at) = date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))) AS tasks_this_month,
            count(DISTINCT t.task_id) FILTER (WHERE (date_trunc('month'::text, t.created_at) = date_trunc('month'::text, (CURRENT_DATE - '1 mon'::interval)))) AS tasks_prev_month,
            count(DISTINCT p.project_id) FILTER (WHERE (date_trunc('month'::text, p.created_at) = date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))) AS new_projects_this_month,
            count(DISTINCT p.project_id) FILTER (WHERE ((p.status = 'completed'::project_status_enum) AND (date_trunc('month'::text, p.updated_at) = date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone)))) AS projects_completed_this_month
           FROM (((organizations o_1
             LEFT JOIN projects p ON ((p.org_id = o_1.org_id)))
             LEFT JOIN tasks t ON (((t.org_id = o_1.org_id) AND (t.is_subtask = false))))
             LEFT JOIN organization_members om ON ((om.org_id = o_1.org_id)))
          GROUP BY o_1.org_id
        ), project_status_distribution AS (
         SELECT p.org_id,
            jsonb_object_agg(p.status, p.cnt) AS distribution
           FROM ( SELECT projects.org_id,
                    COALESCE(projects.status, 'unknown'::project_status_enum) AS status,
                    (count(*))::integer AS cnt
                   FROM projects
                  GROUP BY projects.org_id, COALESCE(projects.status, 'unknown'::project_status_enum)) p
          GROUP BY p.org_id
        ), task_trends AS (
         SELECT t.org_id,
            s.month_start,
            (count(*) FILTER (WHERE ((t.is_subtask = false) AND (t.status = 'completed'::task_status_enum) AND (t.updated_at >= s.month_start) AND (t.updated_at < (s.month_start + '1 mon'::interval)))))::integer AS completed,
            (count(*) FILTER (WHERE ((t.is_subtask = false) AND (t.status = 'in_progress'::task_status_enum) AND (t.updated_at >= s.month_start) AND (t.updated_at < (s.month_start + '1 mon'::interval)))))::integer AS in_progress,
            (count(*) FILTER (WHERE ((t.is_subtask = false) AND (t.status = 'on_hold'::task_status_enum) AND (t.updated_at >= s.month_start) AND (t.updated_at < (s.month_start + '1 mon'::interval)))))::integer AS on_hold,
            (count(*) FILTER (WHERE ((t.is_subtask = false) AND (t.status = 'blocked'::task_status_enum) AND (t.updated_at >= s.month_start) AND (t.updated_at < (s.month_start + '1 mon'::interval)))))::integer AS blocked
           FROM (tasks t
             CROSS JOIN series s)
          GROUP BY t.org_id, s.month_start
        ), task_trends_json AS (
         SELECT task_trends.org_id,
            jsonb_agg(jsonb_build_object('month', to_char((task_trends.month_start)::timestamp with time zone, 'Mon YYYY'::text), 'completed', COALESCE(task_trends.completed, 0), 'in_progress', COALESCE(task_trends.in_progress, 0), 'on_hold', COALESCE(task_trends.on_hold, 0), 'blocked', COALESCE(task_trends.blocked, 0)) ORDER BY task_trends.month_start) AS task_completion_trends
           FROM task_trends
          GROUP BY task_trends.org_id
        ), team_productivity_raw AS (
         SELECT t.org_id,
            COALESCE(u.username) AS assignee_name,
            count(*) AS tasks_total,
            count(*) FILTER (WHERE (t.status = 'completed'::task_status_enum)) AS tasks_completed
           FROM (tasks t
             LEFT JOIN users u ON ((u.username = t.assignee)))
          WHERE (t.is_subtask = false)
          GROUP BY t.org_id, COALESCE(u.username)
        ), team_productivity_json AS (
         SELECT team_productivity_raw.org_id,
            jsonb_agg(jsonb_build_object('assignee_name', team_productivity_raw.assignee_name, 'tasks_completed', team_productivity_raw.tasks_completed, 'tasks_total', team_productivity_raw.tasks_total, 'productivity_percent',
                CASE
                    WHEN (team_productivity_raw.tasks_total = 0) THEN 0
                    ELSE (round(((100.0 * (team_productivity_raw.tasks_completed)::numeric) / (team_productivity_raw.tasks_total)::numeric)))::integer
                END) ORDER BY
                CASE
                    WHEN (team_productivity_raw.tasks_total = 0) THEN 0
                    ELSE (round(((100.0 * (team_productivity_raw.tasks_completed)::numeric) / (team_productivity_raw.tasks_total)::numeric)))::integer
                END DESC, team_productivity_raw.tasks_total DESC) AS team_productivity
           FROM team_productivity_raw
          GROUP BY team_productivity_raw.org_id
        ), project_summary AS (
         SELECT p.org_id,
            p.project_id,
            p.name,
            COALESCE(ps.progress_percent, 0) AS progress_percent,
            COALESCE(ps.tasks_total, (0)::bigint) AS tasks_total,
            COALESCE(ps.team_members, (0)::bigint) AS team_members,
            COALESCE(p.status, 'unknown'::project_status_enum) AS status
           FROM (projects p
             LEFT JOIN project_stats_view ps ON ((ps.project_id = p.project_id)))
        ), project_summary_json AS (
         SELECT project_summary.org_id,
            jsonb_agg(jsonb_build_object('project_id', project_summary.project_id, 'project_name', project_summary.name, 'progress_percent', project_summary.progress_percent, 'tasks_total', project_summary.tasks_total, 'team_members', project_summary.team_members, 'status', project_summary.status) ORDER BY project_summary.name) AS project_performance_summary
           FROM project_summary
          GROUP BY project_summary.org_id
        )
 SELECT o.org_id,
    jsonb_build_object('total_tasks', k.total_tasks, 'active_projects', k.active_projects_now, 'completed_projects', k.completed_projects_now, 'blocked_projects', k.blocked_projects_now, 'team_members', k.team_members, 'tasks_this_month', k.tasks_this_month, 'tasks_prev_month', k.tasks_prev_month, 'tasks_mom_pct',
        CASE
            WHEN (k.tasks_prev_month = 0) THEN NULL::numeric
            ELSE round(((100.0 * ((k.tasks_this_month - k.tasks_prev_month))::numeric) / (NULLIF(k.tasks_prev_month, 0))::numeric), 1)
        END, 'new_projects_this_month', k.new_projects_this_month, 'projects_completed_this_month', k.projects_completed_this_month) AS kpis,
    COALESCE(psd.distribution, '{}'::jsonb) AS project_status_distribution,
    COALESCE(tt.task_completion_trends, '[]'::jsonb) AS task_completion_trends,
    COALESCE(tp.team_productivity, '[]'::jsonb) AS team_productivity,
    COALESCE(pj.project_performance_summary, '[]'::jsonb) AS project_performance_summary
   FROM (((((organizations o
     LEFT JOIN kpis k ON ((k.org_id = o.org_id)))
     LEFT JOIN project_status_distribution psd ON ((psd.org_id = o.org_id)))
     LEFT JOIN task_trends_json tt ON ((tt.org_id = o.org_id)))
     LEFT JOIN team_productivity_json tp ON ((tp.org_id = o.org_id)))
     LEFT JOIN project_summary_json pj ON ((pj.org_id = o.org_id)));



