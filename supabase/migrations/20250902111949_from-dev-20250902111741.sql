create or replace view "public"."test_tracker_card_view" as  SELECT t.tracker_id,
    t.name,
    t.description,
    t.org_id,
    t.project_id,
    t.project_name,
    t.creator_id,
    t.creator_name,
    t.status,
    t.priority,
    t.created_at,
    t.deleted_at,
    COALESCE(b.bug_cnt, 0) AS total_bugs,
    COALESCE(tt.task_cnt, 0) AS total_tasks
   FROM ((test_trackers t
     LEFT JOIN ( SELECT bugs.tracker_id,
            (count(*))::integer AS bug_cnt
           FROM bugs
          GROUP BY bugs.tracker_id) b ON ((b.tracker_id = t.tracker_id)))
     LEFT JOIN ( SELECT test_tracker_tasks.tracker_id,
            (count(*))::integer AS task_cnt
           FROM test_tracker_tasks
          GROUP BY test_tracker_tasks.tracker_id) tt ON ((tt.tracker_id = t.tracker_id)));



