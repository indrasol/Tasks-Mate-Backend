create or replace view "public"."test_tracker_stats_view" as  WITH task_rollup AS (
         SELECT t.tracker_id,
            count(*) AS total_tasks
           FROM test_tracker_tasks t
          GROUP BY t.tracker_id
        ), bug_rollup AS (
         SELECT b.tracker_id,
            count(*) AS total_bugs,
            count(*) FILTER (WHERE (b.status = 'closed'::bug_status_enum)) AS completed_bugs,
            count(*) FILTER (WHERE (b.priority = 'low'::bug_priority_enum)) AS low_priority_bugs,
            count(*) FILTER (WHERE (b.priority = 'medium'::bug_priority_enum)) AS medium_priority_bugs,
            count(*) FILTER (WHERE (b.priority = 'high'::bug_priority_enum)) AS high_priority_bugs
           FROM bugs b
          GROUP BY b.tracker_id
        )
 SELECT p.tracker_id,
    p.org_id,
    p.project_id,
    p.project_name,
    p.name,
    p.description,
    p.creator_id,
    p.creator_name,
    p.status,
    p.priority,
    p.created_at,
    COALESCE(tr.total_tasks, (0)::bigint) AS total_tasks,
    COALESCE(br.total_bugs, (0)::bigint) AS total_bugs,
    COALESCE(br.completed_bugs, (0)::bigint) AS completed_bugs,
    COALESCE(br.low_priority_bugs, (0)::bigint) AS low_priority_bugs,
    COALESCE(br.medium_priority_bugs, (0)::bigint) AS medium_priority_bugs,
    COALESCE(br.high_priority_bugs, (0)::bigint) AS high_priority_bugs,
        CASE
            WHEN (COALESCE(br.total_bugs, (0)::bigint) = 0) THEN 0
            ELSE (round((((br.completed_bugs)::numeric / (br.total_bugs)::numeric) * (100)::numeric)))::integer
        END AS progress_percent
   FROM ((test_trackers p
     LEFT JOIN task_rollup tr ON ((tr.tracker_id = p.tracker_id)))
     LEFT JOIN bug_rollup br ON ((br.tracker_id = p.tracker_id)));



