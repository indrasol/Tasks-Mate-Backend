create or replace view "public"."project_stats_view" as  WITH task_rollup AS (
         SELECT t.project_id,
            count(*) AS total_tasks,
            count(*) FILTER (WHERE (t.status = 'completed'::task_status_enum)) AS completed_tasks
           FROM tasks t
          GROUP BY t.project_id
        ), member_rollup AS (
         SELECT pm.project_id,
            count(DISTINCT pm.user_id) AS team_members
           FROM project_members pm
          GROUP BY pm.project_id
        ), bug_rollup AS (
         SELECT b.project_id,
            count(*) AS total_bugs
           FROM bugs b
          GROUP BY b.project_id
        )
 SELECT p.project_id,
    COALESCE(tr.completed_tasks, (0)::bigint) AS tasks_completed,
    COALESCE(tr.total_tasks, (0)::bigint) AS tasks_total,
        CASE
            WHEN (COALESCE(tr.total_tasks, (0)::bigint) = 0) THEN 0
            ELSE (round((((tr.completed_tasks)::numeric / (tr.total_tasks)::numeric) * (100)::numeric)))::integer
        END AS progress_percent,
    COALESCE(mr.team_members, (0)::bigint) AS team_members,
    GREATEST(0, (p.end_date - CURRENT_DATE)) AS days_left,
    (p.end_date - p.start_date) AS duration_days,
    COALESCE(br.total_bugs, (0)::bigint) AS bugs_total
   FROM (((projects p
     LEFT JOIN task_rollup tr ON ((tr.project_id = p.project_id)))
     LEFT JOIN bug_rollup br ON ((br.project_id = p.project_id)))
     LEFT JOIN member_rollup mr ON ((mr.project_id = p.project_id)));



