alter table "public"."organizations" add column "deleted_at" timestamp with time zone;

create or replace view "public"."organization_stats_view" as  SELECT o.org_id,
    o.name AS org_name,
    o.description AS org_description,
    o.created_by,
    o.created_at,
    COALESCE(p.project_count, 0) AS project_count,
    COALESCE(m.member_count, 0) AS member_count,
    COALESCE(o.is_deleted, false) AS is_deleted
   FROM ((organizations o
     LEFT JOIN LATERAL ( SELECT (count(*))::integer AS project_count
           FROM projects p_1
          WHERE (p_1.org_id = o.org_id)) p ON (true))
     LEFT JOIN LATERAL ( SELECT (count(DISTINCT om.user_id))::integer AS member_count
           FROM organization_members om
          WHERE (om.org_id = o.org_id)) m ON (true));



