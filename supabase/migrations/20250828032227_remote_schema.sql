drop extension if exists "pg_net";

create type "public"."bug_priority_enum" as enum ('low', 'medium', 'high', 'critical');

create type "public"."bug_status_enum" as enum ('open', 'in_progress', 'in_review', 'resolved', 'reopened', 'closed', 'won_t_fix', 'duplicate');

create type "public"."bug_type_enum" as enum ('bug', 'enhancement', 'task', 'documentation');

create type "public"."designation_enum" as enum ('developer', 'designer', 'qa', 'product_manager', 'devops', 'analyst', 'team_lead', 'tester', 'director', 'manager', 'ui_engineer', 'devops_engineer');

create type "public"."history_action_enum" as enum ('created', 'updated', 'deleted', 'subtask_added', 'subtask_removed', 'dependency_added', 'dependency_removed', 'attachment_created', 'attachment_deleted', 'comment_created', 'comment_updated', 'comment_deleted');

create type "public"."invite_status_enum" as enum ('pending', 'accepted', 'cancelled', 'expired');

create type "public"."priority_enum" as enum ('low', 'medium', 'high', 'critical', 'none');

create type "public"."project_status_enum" as enum ('planning', 'in_progress', 'on_hold', 'completed', 'archived', 'not_started', 'blocked', 'paused', 'unknown');

create type "public"."role_enum" as enum ('owner', 'admin', 'member');

create type "public"."task_status_enum" as enum ('not_started', 'in_progress', 'unknown', 'blocked', 'completed', 'archived', 'on_hold');

create sequence "public"."designation_id_seq";


  create table "public"."bug_activity_logs" (
    "id" text not null,
    "bug_id" text not null,
    "user_id" text not null,
    "activity_type" text not null,
    "old_value" jsonb,
    "new_value" jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."bug_activity_logs" enable row level security;


  create table "public"."bug_attachments" (
    "id" text not null,
    "bug_id" text not null,
    "user_id" text not null,
    "file_name" text not null,
    "file_path" text not null,
    "file_type" text,
    "file_size" integer,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."bug_attachments" enable row level security;


  create table "public"."bug_comments" (
    "id" text not null,
    "bug_id" text not null,
    "user_id" text not null,
    "content" text not null,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."bug_comments" enable row level security;


  create table "public"."bug_relations" (
    "source_bug_id" text not null,
    "target_bug_id" text not null,
    "relation_type" text not null,
    "created_at" timestamp with time zone default now(),
    "created_by" text not null
      );


alter table "public"."bug_relations" enable row level security;


  create table "public"."bug_watchers" (
    "bug_id" text not null,
    "user_id" text not null,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."bug_watchers" enable row level security;


  create table "public"."bugs" (
    "id" text not null,
    "tracker_id" text,
    "tracker_name" text,
    "title" text not null,
    "description" text,
    "status" bug_status_enum not null default 'open'::bug_status_enum,
    "priority" bug_priority_enum default 'medium'::bug_priority_enum,
    "type" bug_type_enum default 'bug'::bug_type_enum,
    "assignee" text,
    "reporter" text,
    "project_id" text not null,
    "project_name" text,
    "tags" text[] default '{}'::text[],
    "due_date" timestamp with time zone,
    "estimated_time" interval,
    "actual_time" interval,
    "environment" text,
    "steps_to_reproduce" text,
    "expected_result" text,
    "actual_result" text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "closed_at" timestamp with time zone
      );


alter table "public"."bugs" enable row level security;


  create table "public"."designations" (
    "name" designation_enum not null,
    "metadata" jsonb default '{}'::jsonb,
    "created_by" uuid,
    "updated_by" uuid,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "designation_id" text not null
      );



  create table "public"."organization_invites" (
    "id" text not null,
    "org_id" text not null,
    "email" text not null,
    "designation" designation_enum,
    "role" role_enum,
    "invited_by" text,
    "invite_status" text default 'pending'::text,
    "sent_at" timestamp with time zone default now(),
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "is_cancelled" boolean default false,
    "cancel_date" timestamp with time zone,
    "updated_by" text,
    "org_name" text
      );


alter table "public"."organization_invites" enable row level security;


  create table "public"."organization_members" (
    "user_id" uuid not null,
    "is_active" boolean default true,
    "invited_at" timestamp with time zone,
    "accepted_at" timestamp with time zone,
    "updated_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "delete_reason" text,
    "role" role_enum,
    "designation" designation_enum,
    "org_id" text not null,
    "invited_by" text,
    "deleted_by" text,
    "email" text,
    "username" text,
    "updated_by" text
      );


alter table "public"."organization_members" enable row level security;


  create table "public"."organizations" (
    "name" text not null,
    "description" text,
    "logo" text,
    "email" text,
    "metadata" jsonb default '{}'::jsonb,
    "is_deleted" boolean default false,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "delete_reason" text,
    "designations" designation_enum[],
    "org_id" text not null,
    "created_by" text,
    "updated_by" text,
    "deleted_by" text
      );


alter table "public"."organizations" enable row level security;


  create table "public"."organizations_history" (
    "name" text,
    "description" text,
    "logo" text,
    "email" text,
    "metadata" jsonb,
    "created_at" timestamp with time zone,
    "updated_at" timestamp with time zone,
    "deleted_at" timestamp with time zone default now(),
    "delete_reason" text,
    "designations" designation_enum[],
    "org_id" text,
    "created_by" text,
    "updated_by" text,
    "deleted_by" text,
    "is_deleted" boolean
      );



  create table "public"."project_members" (
    "project_id" text not null,
    "user_id" uuid not null,
    "created_by" text,
    "updated_by" text,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "delete_reason" text,
    "designation" designation_enum,
    "role" role_enum,
    "username" text
      );


alter table "public"."project_members" enable row level security;


  create table "public"."project_resources" (
    "resource_id" text not null,
    "project_id" text not null,
    "project_name" text not null,
    "resource_url" text,
    "resource_type" text,
    "is_active" boolean default true,
    "created_by" text,
    "updated_by" text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "delete_reason" text,
    "resource_name" text,
    "storage_path" text
      );


alter table "public"."project_resources" enable row level security;


  create table "public"."projects" (
    "project_id" text not null,
    "name" text not null,
    "description" text,
    "metadata" jsonb default '{}'::jsonb,
    "status" project_status_enum default 'not_started'::project_status_enum,
    "priority" priority_enum default 'none'::priority_enum,
    "start_date" date,
    "end_date" date,
    "created_by" text,
    "updated_by" text,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "delete_reason" text,
    "org_id" text,
    "project_owner" text,
    "team_members" text[],
    "owner" text,
    "owner_designation" text,
    "team_member_designations" text[]
      );


alter table "public"."projects" enable row level security;


  create table "public"."roles" (
    "name" role_enum not null,
    "permissions" jsonb default '{}'::jsonb,
    "updated_at" timestamp with time zone default now(),
    "role_id" text not null
      );



  create table "public"."scratchpads" (
    "org_id" text not null,
    "user_id" uuid not null,
    "user_name" text not null,
    "content" text not null default ''::text,
    "updated_at" timestamp with time zone not null default now()
      );



  create table "public"."task_attachments" (
    "task_id" text not null,
    "title" text,
    "name" text,
    "url" text,
    "uploaded_by" text,
    "uploaded_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "deleted_by" text,
    "is_inline" boolean default false,
    "attachment_id" text not null,
    "storage_path" text
      );


alter table "public"."task_attachments" enable row level security;


  create table "public"."task_comments" (
    "task_id" text not null,
    "task_title" text,
    "created_by" text,
    "content" text not null,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "comment_id" text not null,
    "comment" text,
    "parent_comment_id" text
      );


alter table "public"."task_comments" enable row level security;


  create table "public"."tasks" (
    "task_id" text not null,
    "project_id" text not null,
    "sub_tasks" text[] default '{}'::text[],
    "dependencies" text[] default '{}'::text[],
    "title" text not null,
    "description" text,
    "status" task_status_enum default 'not_started'::task_status_enum,
    "assignee" text,
    "due_date" date,
    "priority" priority_enum default 'none'::priority_enum,
    "tags" text[] default '{}'::text[],
    "metadata" jsonb[] default '{}'::jsonb[],
    "created_by" text,
    "updated_by" text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "owner" text,
    "start_date" text,
    "end_date" text,
    "org_id" text,
    "is_subtask" boolean default false
      );


alter table "public"."tasks" enable row level security;


  create table "public"."tasks_history" (
    "task_id" text not null,
    "title" text,
    "metadata" jsonb[] default '{}'::jsonb[],
    "hash_id" text,
    "updated_at" timestamp with time zone default now(),
    "history_id" text not null,
    "created_at" timestamp with time zone,
    "created_by" text,
    "type" text,
    "action" history_action_enum,
    "actor_display" text
      );



  create table "public"."test_trackers" (
    "tracker_id" text not null,
    "org_id" text not null,
    "project_id" text not null,
    "name" text not null,
    "description" text,
    "project_name" text,
    "status" task_status_enum not null default 'not_started'::task_status_enum,
    "priority" priority_enum not null default 'low'::priority_enum,
    "creator_id" uuid not null,
    "creator_name" text not null,
    "tags" text[] default '{}'::text[],
    "metadata" jsonb default '{}'::jsonb,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "deleted_at" timestamp with time zone,
    "delete_reason" text,
    "updated_by" text
      );



  create table "public"."users" (
    "id" uuid not null,
    "username" text not null,
    "email" text not null,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


CREATE UNIQUE INDEX bug_activity_logs_pkey ON public.bug_activity_logs USING btree (id);

CREATE UNIQUE INDEX bug_attachments_pkey ON public.bug_attachments USING btree (id);

CREATE UNIQUE INDEX bug_comments_pkey ON public.bug_comments USING btree (id);

CREATE UNIQUE INDEX bug_relations_pkey ON public.bug_relations USING btree (source_bug_id, target_bug_id, relation_type);

CREATE UNIQUE INDEX bug_watchers_pkey ON public.bug_watchers USING btree (bug_id, user_id);

CREATE UNIQUE INDEX bugs_pkey ON public.bugs USING btree (id);

CREATE UNIQUE INDEX designations_pkey ON public.designations USING btree (designation_id);

CREATE INDEX idx_bugs_assignee ON public.bugs USING btree (assignee);

CREATE INDEX idx_bugs_priority ON public.bugs USING btree (priority);

CREATE INDEX idx_bugs_project_id ON public.bugs USING btree (project_id);

CREATE INDEX idx_bugs_reporter ON public.bugs USING btree (reporter);

CREATE INDEX idx_bugs_status ON public.bugs USING btree (status);

CREATE INDEX idx_org_members_user ON public.organization_members USING btree (user_id);

CREATE INDEX idx_task_attach_task ON public.task_attachments USING btree (task_id);

CREATE INDEX idx_task_comments_task ON public.task_comments USING btree (task_id);

CREATE INDEX idx_tasks_history_task ON public.tasks_history USING btree (task_id);

CREATE INDEX idx_test_trackers_creator ON public.test_trackers USING btree (creator_id);

CREATE INDEX idx_test_trackers_org ON public.test_trackers USING btree (org_id);

CREATE INDEX idx_test_trackers_project ON public.test_trackers USING btree (project_id);

CREATE INDEX idx_test_trackers_status ON public.test_trackers USING btree (status);

CREATE UNIQUE INDEX organization_invites_pkey ON public.organization_invites USING btree (id);

CREATE UNIQUE INDEX organization_members_pkey ON public.organization_members USING btree (user_id, org_id);

CREATE UNIQUE INDEX organizations_pkey ON public.organizations USING btree (org_id);

CREATE UNIQUE INDEX project_members_pkey ON public.project_members USING btree (project_id, user_id);

CREATE UNIQUE INDEX project_resources_pkey ON public.project_resources USING btree (resource_id);

CREATE UNIQUE INDEX projects_pkey ON public.projects USING btree (project_id);

CREATE UNIQUE INDEX roles_pkey ON public.roles USING btree (role_id);

CREATE UNIQUE INDEX scratchpads_pkey ON public.scratchpads USING btree (org_id, user_id);

CREATE UNIQUE INDEX task_attachments_attachment_id_key ON public.task_attachments USING btree (attachment_id);

CREATE UNIQUE INDEX task_attachments_pkey ON public.task_attachments USING btree (attachment_id);

CREATE UNIQUE INDEX task_comments_pkey ON public.task_comments USING btree (comment_id);

CREATE UNIQUE INDEX tasks_history_hash_unique ON public.tasks_history USING btree (hash_id);

CREATE UNIQUE INDEX tasks_history_pkey ON public.tasks_history USING btree (history_id);

CREATE UNIQUE INDEX tasks_pkey ON public.tasks USING btree (task_id);

CREATE UNIQUE INDEX test_trackers_pkey ON public.test_trackers USING btree (tracker_id);

CREATE UNIQUE INDEX users_email_key ON public.users USING btree (email);

CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id);

CREATE UNIQUE INDEX users_username_key ON public.users USING btree (username);

alter table "public"."bug_activity_logs" add constraint "bug_activity_logs_pkey" PRIMARY KEY using index "bug_activity_logs_pkey";

alter table "public"."bug_attachments" add constraint "bug_attachments_pkey" PRIMARY KEY using index "bug_attachments_pkey";

alter table "public"."bug_comments" add constraint "bug_comments_pkey" PRIMARY KEY using index "bug_comments_pkey";

alter table "public"."bug_relations" add constraint "bug_relations_pkey" PRIMARY KEY using index "bug_relations_pkey";

alter table "public"."bug_watchers" add constraint "bug_watchers_pkey" PRIMARY KEY using index "bug_watchers_pkey";

alter table "public"."bugs" add constraint "bugs_pkey" PRIMARY KEY using index "bugs_pkey";

alter table "public"."designations" add constraint "designations_pkey" PRIMARY KEY using index "designations_pkey";

alter table "public"."organization_invites" add constraint "organization_invites_pkey" PRIMARY KEY using index "organization_invites_pkey";

alter table "public"."organization_members" add constraint "organization_members_pkey" PRIMARY KEY using index "organization_members_pkey";

alter table "public"."organizations" add constraint "organizations_pkey" PRIMARY KEY using index "organizations_pkey";

alter table "public"."project_members" add constraint "project_members_pkey" PRIMARY KEY using index "project_members_pkey";

alter table "public"."project_resources" add constraint "project_resources_pkey" PRIMARY KEY using index "project_resources_pkey";

alter table "public"."projects" add constraint "projects_pkey" PRIMARY KEY using index "projects_pkey";

alter table "public"."roles" add constraint "roles_pkey" PRIMARY KEY using index "roles_pkey";

alter table "public"."scratchpads" add constraint "scratchpads_pkey" PRIMARY KEY using index "scratchpads_pkey";

alter table "public"."task_attachments" add constraint "task_attachments_pkey" PRIMARY KEY using index "task_attachments_pkey";

alter table "public"."task_comments" add constraint "task_comments_pkey" PRIMARY KEY using index "task_comments_pkey";

alter table "public"."tasks" add constraint "tasks_pkey" PRIMARY KEY using index "tasks_pkey";

alter table "public"."tasks_history" add constraint "tasks_history_pkey" PRIMARY KEY using index "tasks_history_pkey";

alter table "public"."test_trackers" add constraint "test_trackers_pkey" PRIMARY KEY using index "test_trackers_pkey";

alter table "public"."users" add constraint "users_pkey" PRIMARY KEY using index "users_pkey";

alter table "public"."bug_activity_logs" add constraint "bug_activity_logs_bug_id_fkey" FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_activity_logs" validate constraint "bug_activity_logs_bug_id_fkey";

alter table "public"."bug_attachments" add constraint "bug_attachments_bug_id_fkey" FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_attachments" validate constraint "bug_attachments_bug_id_fkey";

alter table "public"."bug_comments" add constraint "bug_comments_bug_id_fkey" FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_comments" validate constraint "bug_comments_bug_id_fkey";

alter table "public"."bug_relations" add constraint "bug_relations_source_bug_id_fkey" FOREIGN KEY (source_bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_relations" validate constraint "bug_relations_source_bug_id_fkey";

alter table "public"."bug_relations" add constraint "bug_relations_target_bug_id_fkey" FOREIGN KEY (target_bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_relations" validate constraint "bug_relations_target_bug_id_fkey";

alter table "public"."bug_watchers" add constraint "bug_watchers_bug_id_fkey" FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."bug_watchers" validate constraint "bug_watchers_bug_id_fkey";

alter table "public"."bugs" add constraint "bugs_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) not valid;

alter table "public"."bugs" validate constraint "bugs_project_id_fkey";

alter table "public"."bugs" add constraint "bugs_tracker_id_fkey" FOREIGN KEY (tracker_id) REFERENCES test_trackers(tracker_id) not valid;

alter table "public"."bugs" validate constraint "bugs_tracker_id_fkey";

alter table "public"."organization_invites" add constraint "organization_invites_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE not valid;

alter table "public"."organization_invites" validate constraint "organization_invites_org_id_fkey";

alter table "public"."organization_members" add constraint "organization_members_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."organization_members" validate constraint "organization_members_org_id_fkey";

alter table "public"."project_members" add constraint "project_members_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE not valid;

alter table "public"."project_members" validate constraint "project_members_project_id_fkey";

alter table "public"."project_resources" add constraint "project_resources_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE not valid;

alter table "public"."project_resources" validate constraint "project_resources_project_id_fkey";

alter table "public"."projects" add constraint "projects_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."projects" validate constraint "projects_org_id_fkey";

alter table "public"."task_attachments" add constraint "task_attachments_attachment_id_key" UNIQUE using index "task_attachments_attachment_id_key";

alter table "public"."task_attachments" add constraint "task_attachments_task_id_fkey" FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."task_attachments" validate constraint "task_attachments_task_id_fkey";

alter table "public"."task_comments" add constraint "task_comments_task_id_fkey" FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."task_comments" validate constraint "task_comments_task_id_fkey";

alter table "public"."tasks" add constraint "tasks_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."tasks" validate constraint "tasks_org_id_fkey";

alter table "public"."tasks" add constraint "tasks_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE not valid;

alter table "public"."tasks" validate constraint "tasks_project_id_fkey";

alter table "public"."tasks_history" add constraint "tasks_history_hash_unique" UNIQUE using index "tasks_history_hash_unique";

alter table "public"."tasks_history" add constraint "tasks_history_task_id_fkey" FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."tasks_history" validate constraint "tasks_history_task_id_fkey";

alter table "public"."test_trackers" add constraint "test_trackers_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE not valid;

alter table "public"."test_trackers" validate constraint "test_trackers_org_id_fkey";

alter table "public"."test_trackers" add constraint "test_trackers_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE not valid;

alter table "public"."test_trackers" validate constraint "test_trackers_project_id_fkey";

alter table "public"."users" add constraint "users_email_key" UNIQUE using index "users_email_key";

alter table "public"."users" add constraint "users_username_key" UNIQUE using index "users_username_key";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.auth_email()
 RETURNS text
 LANGUAGE sql
 STABLE
AS $function$
  select coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    ''
  );
$function$
;

CREATE OR REPLACE FUNCTION public.auth_uid()
 RETURNS uuid
 LANGUAGE sql
 STABLE
AS $function$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;
$function$
;

CREATE OR REPLACE FUNCTION public.auth_username()
 RETURNS text
 LANGUAGE sql
 STABLE
AS $function$
  select coalesce(
    nullif(current_setting('request.jwt.claim.username', true), ''),
    ''
  );
$function$
;

CREATE OR REPLACE FUNCTION public.has_org_role(org text, roles text[])
 RETURNS boolean
 LANGUAGE sql
 STABLE
AS $function$
  select exists (
    select 1 from organization_members
    where org_id = org and user_id = auth_uid()
      and role = any(
        array(
          select enumlabel::role_enum
          from pg_enum
          where enumtypid = 'role_enum'::regtype
            and enumlabel = any(roles)
        )
      ) and is_active = true
  );
$function$
;

CREATE OR REPLACE FUNCTION public.has_proj_role(proj text, roles text[])
 RETURNS boolean
 LANGUAGE sql
 STABLE
AS $function$
  select exists (
    select 1 from project_members
    where project_id = proj and user_id = auth_uid()
      and role = any(
        array(
          select enumlabel::role_enum
          from pg_enum
          where enumtypid = 'role_enum'::regtype
            and enumlabel = any(roles)
        )
      ) and is_active = true
  );
$function$
;

CREATE OR REPLACE FUNCTION public.is_org_member(org text)
 RETURNS boolean
 LANGUAGE sql
 STABLE
AS $function$
  select exists (
    select 1 from organization_members
    where org_id = org and user_id = auth_uid() and is_active = true
  );
$function$
;

CREATE OR REPLACE FUNCTION public.is_project_member(proj text)
 RETURNS boolean
 LANGUAGE sql
 STABLE
AS $function$
  select exists (
    select 1 from project_members
    where project_id = proj and user_id = auth_uid() and is_active = true
  );
$function$
;

CREATE OR REPLACE FUNCTION public.log_bug_activity()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  old_data JSONB;
  new_data JSONB;
  changed_fields JSONB := '{}'::JSONB;
  field TEXT;
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO public.bug_activity_logs (bug_id, user_id, activity_type, new_value)
    VALUES (NEW.id, NEW.reporter, 'bug_created', to_jsonb(NEW));

  ELSIF TG_OP = 'UPDATE' THEN
    old_data := to_jsonb(OLD);
    new_data := to_jsonb(NEW);

    FOR field IN SELECT * FROM jsonb_object_keys(new_data) LOOP
      IF field != 'updated_at' AND (old_data->>field) IS DISTINCT FROM (new_data->>field) THEN
        changed_fields := jsonb_set(changed_fields, ARRAY[field], jsonb_build_object('old', old_data->field, 'new', new_data->field));
      END IF;
    END LOOP;

    IF jsonb_typeof(changed_fields) != 'null' THEN
      INSERT INTO public.bug_activity_logs (bug_id, user_id, activity_type, old_value)
      VALUES (NEW.id, NEW.reporter, 'bug_updated', changed_fields);
    END IF;

  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO public.bug_activity_logs (bug_id, user_id, activity_type, old_value)
    VALUES (OLD.id, OLD.reporter, 'bug_deleted', to_jsonb(OLD));
  END IF;

  RETURN NULL;
END;
$function$
;

create or replace view "public"."organization_stats_view" as  SELECT o.org_id,
    o.name AS org_name,
    o.description AS org_description,
    o.created_by,
    o.created_at,
    (count(DISTINCT p.project_id))::integer AS project_count,
    (count(DISTINCT om.user_id))::integer AS member_count
   FROM ((organizations o
     LEFT JOIN projects p ON ((p.org_id = o.org_id)))
     LEFT JOIN organization_members om ON ((om.org_id = o.org_id)))
  GROUP BY o.org_id, o.name, o.description, o.created_by, o.created_at
  ORDER BY o.name;


create or replace view "public"."project_card_view" as  SELECT p.project_id,
    p.org_id,
    p.name,
    p.description,
    p.start_date,
    p.end_date,
    p.metadata,
    p.status,
    p.priority,
    p.created_by,
    p.project_owner,
    p.updated_by,
    p.is_active,
    p.delete_reason,
    p.team_members,
    p.created_at,
    COALESCE(count(t.*), (0)::bigint) AS tasks_total,
    COALESCE(count(*) FILTER (WHERE (t.status = 'completed'::task_status_enum)), (0)::bigint) AS tasks_completed,
        CASE
            WHEN (COALESCE(count(t.*), (0)::bigint) = 0) THEN (0)::numeric
            ELSE round(((100.0 * (count(*) FILTER (WHERE (t.status = 'completed'::task_status_enum)))::numeric) / (count(t.*))::numeric), 1)
        END AS progress_percent
   FROM (projects p
     LEFT JOIN tasks t ON (((p.project_id = t.project_id) AND (COALESCE(t.is_subtask, false) = false))))
  GROUP BY p.project_id, p.org_id, p.name, p.description, p.start_date, p.end_date, p.metadata, p.status, p.priority, p.created_by, p.project_owner, p.updated_by, p.is_active, p.delete_reason, p.team_members, p.created_at;


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
    (p.end_date - p.start_date) AS duration_days
   FROM ((projects p
     LEFT JOIN task_rollup tr ON ((tr.project_id = p.project_id)))
     LEFT JOIN member_rollup mr ON ((mr.project_id = p.project_id)));


CREATE OR REPLACE FUNCTION public.set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
    -- Only modify when any column really changed
    if row(NEW.*) is distinct from row(OLD.*) then
        NEW.updated_at = now();
    end if;
    return NEW;
end;
$function$
;

create or replace view "public"."task_card_view" as  SELECT t.task_id,
    t.org_id,
    t.project_id,
    t.sub_tasks,
    t.dependencies,
    t.title,
    t.description,
    t.start_date,
    t.due_date,
    t.metadata,
    t.status,
    t.priority,
    t.tags,
    t.created_by,
    t.assignee,
    t.is_subtask,
    t.updated_by,
    t.created_at,
    t.updated_at,
    COALESCE(count(tc.comment_id), (0)::bigint) AS comments
   FROM (tasks t
     LEFT JOIN task_comments tc ON ((t.task_id = tc.task_id)))
  GROUP BY t.task_id, t.org_id, t.project_id, t.sub_tasks, t.dependencies, t.title, t.description, t.start_date, t.due_date, t.metadata, t.status, t.priority, t.tags, t.created_by, t.assignee, t.is_subtask, t.updated_by, t.created_at, t.updated_at;


CREATE OR REPLACE FUNCTION public.update_modified_column()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$function$
;

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


grant delete on table "public"."bug_activity_logs" to "anon";

grant insert on table "public"."bug_activity_logs" to "anon";

grant references on table "public"."bug_activity_logs" to "anon";

grant select on table "public"."bug_activity_logs" to "anon";

grant trigger on table "public"."bug_activity_logs" to "anon";

grant truncate on table "public"."bug_activity_logs" to "anon";

grant update on table "public"."bug_activity_logs" to "anon";

grant delete on table "public"."bug_activity_logs" to "authenticated";

grant insert on table "public"."bug_activity_logs" to "authenticated";

grant references on table "public"."bug_activity_logs" to "authenticated";

grant select on table "public"."bug_activity_logs" to "authenticated";

grant trigger on table "public"."bug_activity_logs" to "authenticated";

grant truncate on table "public"."bug_activity_logs" to "authenticated";

grant update on table "public"."bug_activity_logs" to "authenticated";

grant delete on table "public"."bug_activity_logs" to "service_role";

grant insert on table "public"."bug_activity_logs" to "service_role";

grant references on table "public"."bug_activity_logs" to "service_role";

grant select on table "public"."bug_activity_logs" to "service_role";

grant trigger on table "public"."bug_activity_logs" to "service_role";

grant truncate on table "public"."bug_activity_logs" to "service_role";

grant update on table "public"."bug_activity_logs" to "service_role";

grant delete on table "public"."bug_attachments" to "anon";

grant insert on table "public"."bug_attachments" to "anon";

grant references on table "public"."bug_attachments" to "anon";

grant select on table "public"."bug_attachments" to "anon";

grant trigger on table "public"."bug_attachments" to "anon";

grant truncate on table "public"."bug_attachments" to "anon";

grant update on table "public"."bug_attachments" to "anon";

grant delete on table "public"."bug_attachments" to "authenticated";

grant insert on table "public"."bug_attachments" to "authenticated";

grant references on table "public"."bug_attachments" to "authenticated";

grant select on table "public"."bug_attachments" to "authenticated";

grant trigger on table "public"."bug_attachments" to "authenticated";

grant truncate on table "public"."bug_attachments" to "authenticated";

grant update on table "public"."bug_attachments" to "authenticated";

grant delete on table "public"."bug_attachments" to "service_role";

grant insert on table "public"."bug_attachments" to "service_role";

grant references on table "public"."bug_attachments" to "service_role";

grant select on table "public"."bug_attachments" to "service_role";

grant trigger on table "public"."bug_attachments" to "service_role";

grant truncate on table "public"."bug_attachments" to "service_role";

grant update on table "public"."bug_attachments" to "service_role";

grant delete on table "public"."bug_comments" to "anon";

grant insert on table "public"."bug_comments" to "anon";

grant references on table "public"."bug_comments" to "anon";

grant select on table "public"."bug_comments" to "anon";

grant trigger on table "public"."bug_comments" to "anon";

grant truncate on table "public"."bug_comments" to "anon";

grant update on table "public"."bug_comments" to "anon";

grant delete on table "public"."bug_comments" to "authenticated";

grant insert on table "public"."bug_comments" to "authenticated";

grant references on table "public"."bug_comments" to "authenticated";

grant select on table "public"."bug_comments" to "authenticated";

grant trigger on table "public"."bug_comments" to "authenticated";

grant truncate on table "public"."bug_comments" to "authenticated";

grant update on table "public"."bug_comments" to "authenticated";

grant delete on table "public"."bug_comments" to "service_role";

grant insert on table "public"."bug_comments" to "service_role";

grant references on table "public"."bug_comments" to "service_role";

grant select on table "public"."bug_comments" to "service_role";

grant trigger on table "public"."bug_comments" to "service_role";

grant truncate on table "public"."bug_comments" to "service_role";

grant update on table "public"."bug_comments" to "service_role";

grant delete on table "public"."bug_relations" to "anon";

grant insert on table "public"."bug_relations" to "anon";

grant references on table "public"."bug_relations" to "anon";

grant select on table "public"."bug_relations" to "anon";

grant trigger on table "public"."bug_relations" to "anon";

grant truncate on table "public"."bug_relations" to "anon";

grant update on table "public"."bug_relations" to "anon";

grant delete on table "public"."bug_relations" to "authenticated";

grant insert on table "public"."bug_relations" to "authenticated";

grant references on table "public"."bug_relations" to "authenticated";

grant select on table "public"."bug_relations" to "authenticated";

grant trigger on table "public"."bug_relations" to "authenticated";

grant truncate on table "public"."bug_relations" to "authenticated";

grant update on table "public"."bug_relations" to "authenticated";

grant delete on table "public"."bug_relations" to "service_role";

grant insert on table "public"."bug_relations" to "service_role";

grant references on table "public"."bug_relations" to "service_role";

grant select on table "public"."bug_relations" to "service_role";

grant trigger on table "public"."bug_relations" to "service_role";

grant truncate on table "public"."bug_relations" to "service_role";

grant update on table "public"."bug_relations" to "service_role";

grant delete on table "public"."bug_watchers" to "anon";

grant insert on table "public"."bug_watchers" to "anon";

grant references on table "public"."bug_watchers" to "anon";

grant select on table "public"."bug_watchers" to "anon";

grant trigger on table "public"."bug_watchers" to "anon";

grant truncate on table "public"."bug_watchers" to "anon";

grant update on table "public"."bug_watchers" to "anon";

grant delete on table "public"."bug_watchers" to "authenticated";

grant insert on table "public"."bug_watchers" to "authenticated";

grant references on table "public"."bug_watchers" to "authenticated";

grant select on table "public"."bug_watchers" to "authenticated";

grant trigger on table "public"."bug_watchers" to "authenticated";

grant truncate on table "public"."bug_watchers" to "authenticated";

grant update on table "public"."bug_watchers" to "authenticated";

grant delete on table "public"."bug_watchers" to "service_role";

grant insert on table "public"."bug_watchers" to "service_role";

grant references on table "public"."bug_watchers" to "service_role";

grant select on table "public"."bug_watchers" to "service_role";

grant trigger on table "public"."bug_watchers" to "service_role";

grant truncate on table "public"."bug_watchers" to "service_role";

grant update on table "public"."bug_watchers" to "service_role";

grant delete on table "public"."bugs" to "anon";

grant insert on table "public"."bugs" to "anon";

grant references on table "public"."bugs" to "anon";

grant select on table "public"."bugs" to "anon";

grant trigger on table "public"."bugs" to "anon";

grant truncate on table "public"."bugs" to "anon";

grant update on table "public"."bugs" to "anon";

grant delete on table "public"."bugs" to "authenticated";

grant insert on table "public"."bugs" to "authenticated";

grant references on table "public"."bugs" to "authenticated";

grant select on table "public"."bugs" to "authenticated";

grant trigger on table "public"."bugs" to "authenticated";

grant truncate on table "public"."bugs" to "authenticated";

grant update on table "public"."bugs" to "authenticated";

grant delete on table "public"."bugs" to "service_role";

grant insert on table "public"."bugs" to "service_role";

grant references on table "public"."bugs" to "service_role";

grant select on table "public"."bugs" to "service_role";

grant trigger on table "public"."bugs" to "service_role";

grant truncate on table "public"."bugs" to "service_role";

grant update on table "public"."bugs" to "service_role";

grant delete on table "public"."designations" to "anon";

grant insert on table "public"."designations" to "anon";

grant references on table "public"."designations" to "anon";

grant select on table "public"."designations" to "anon";

grant trigger on table "public"."designations" to "anon";

grant truncate on table "public"."designations" to "anon";

grant update on table "public"."designations" to "anon";

grant delete on table "public"."designations" to "authenticated";

grant insert on table "public"."designations" to "authenticated";

grant references on table "public"."designations" to "authenticated";

grant select on table "public"."designations" to "authenticated";

grant trigger on table "public"."designations" to "authenticated";

grant truncate on table "public"."designations" to "authenticated";

grant update on table "public"."designations" to "authenticated";

grant delete on table "public"."designations" to "service_role";

grant insert on table "public"."designations" to "service_role";

grant references on table "public"."designations" to "service_role";

grant select on table "public"."designations" to "service_role";

grant trigger on table "public"."designations" to "service_role";

grant truncate on table "public"."designations" to "service_role";

grant update on table "public"."designations" to "service_role";

grant delete on table "public"."organization_invites" to "anon";

grant insert on table "public"."organization_invites" to "anon";

grant references on table "public"."organization_invites" to "anon";

grant select on table "public"."organization_invites" to "anon";

grant trigger on table "public"."organization_invites" to "anon";

grant truncate on table "public"."organization_invites" to "anon";

grant update on table "public"."organization_invites" to "anon";

grant delete on table "public"."organization_invites" to "authenticated";

grant insert on table "public"."organization_invites" to "authenticated";

grant references on table "public"."organization_invites" to "authenticated";

grant select on table "public"."organization_invites" to "authenticated";

grant trigger on table "public"."organization_invites" to "authenticated";

grant truncate on table "public"."organization_invites" to "authenticated";

grant update on table "public"."organization_invites" to "authenticated";

grant delete on table "public"."organization_invites" to "service_role";

grant insert on table "public"."organization_invites" to "service_role";

grant references on table "public"."organization_invites" to "service_role";

grant select on table "public"."organization_invites" to "service_role";

grant trigger on table "public"."organization_invites" to "service_role";

grant truncate on table "public"."organization_invites" to "service_role";

grant update on table "public"."organization_invites" to "service_role";

grant delete on table "public"."organization_members" to "anon";

grant insert on table "public"."organization_members" to "anon";

grant references on table "public"."organization_members" to "anon";

grant select on table "public"."organization_members" to "anon";

grant trigger on table "public"."organization_members" to "anon";

grant truncate on table "public"."organization_members" to "anon";

grant update on table "public"."organization_members" to "anon";

grant delete on table "public"."organization_members" to "authenticated";

grant insert on table "public"."organization_members" to "authenticated";

grant references on table "public"."organization_members" to "authenticated";

grant select on table "public"."organization_members" to "authenticated";

grant trigger on table "public"."organization_members" to "authenticated";

grant truncate on table "public"."organization_members" to "authenticated";

grant update on table "public"."organization_members" to "authenticated";

grant delete on table "public"."organization_members" to "service_role";

grant insert on table "public"."organization_members" to "service_role";

grant references on table "public"."organization_members" to "service_role";

grant select on table "public"."organization_members" to "service_role";

grant trigger on table "public"."organization_members" to "service_role";

grant truncate on table "public"."organization_members" to "service_role";

grant update on table "public"."organization_members" to "service_role";

grant delete on table "public"."organizations" to "anon";

grant insert on table "public"."organizations" to "anon";

grant references on table "public"."organizations" to "anon";

grant select on table "public"."organizations" to "anon";

grant trigger on table "public"."organizations" to "anon";

grant truncate on table "public"."organizations" to "anon";

grant update on table "public"."organizations" to "anon";

grant delete on table "public"."organizations" to "authenticated";

grant insert on table "public"."organizations" to "authenticated";

grant references on table "public"."organizations" to "authenticated";

grant select on table "public"."organizations" to "authenticated";

grant trigger on table "public"."organizations" to "authenticated";

grant truncate on table "public"."organizations" to "authenticated";

grant update on table "public"."organizations" to "authenticated";

grant delete on table "public"."organizations" to "service_role";

grant insert on table "public"."organizations" to "service_role";

grant references on table "public"."organizations" to "service_role";

grant select on table "public"."organizations" to "service_role";

grant trigger on table "public"."organizations" to "service_role";

grant truncate on table "public"."organizations" to "service_role";

grant update on table "public"."organizations" to "service_role";

grant delete on table "public"."organizations_history" to "anon";

grant insert on table "public"."organizations_history" to "anon";

grant references on table "public"."organizations_history" to "anon";

grant select on table "public"."organizations_history" to "anon";

grant trigger on table "public"."organizations_history" to "anon";

grant truncate on table "public"."organizations_history" to "anon";

grant update on table "public"."organizations_history" to "anon";

grant delete on table "public"."organizations_history" to "authenticated";

grant insert on table "public"."organizations_history" to "authenticated";

grant references on table "public"."organizations_history" to "authenticated";

grant select on table "public"."organizations_history" to "authenticated";

grant trigger on table "public"."organizations_history" to "authenticated";

grant truncate on table "public"."organizations_history" to "authenticated";

grant update on table "public"."organizations_history" to "authenticated";

grant delete on table "public"."organizations_history" to "service_role";

grant insert on table "public"."organizations_history" to "service_role";

grant references on table "public"."organizations_history" to "service_role";

grant select on table "public"."organizations_history" to "service_role";

grant trigger on table "public"."organizations_history" to "service_role";

grant truncate on table "public"."organizations_history" to "service_role";

grant update on table "public"."organizations_history" to "service_role";

grant delete on table "public"."project_members" to "anon";

grant insert on table "public"."project_members" to "anon";

grant references on table "public"."project_members" to "anon";

grant select on table "public"."project_members" to "anon";

grant trigger on table "public"."project_members" to "anon";

grant truncate on table "public"."project_members" to "anon";

grant update on table "public"."project_members" to "anon";

grant delete on table "public"."project_members" to "authenticated";

grant insert on table "public"."project_members" to "authenticated";

grant references on table "public"."project_members" to "authenticated";

grant select on table "public"."project_members" to "authenticated";

grant trigger on table "public"."project_members" to "authenticated";

grant truncate on table "public"."project_members" to "authenticated";

grant update on table "public"."project_members" to "authenticated";

grant delete on table "public"."project_members" to "service_role";

grant insert on table "public"."project_members" to "service_role";

grant references on table "public"."project_members" to "service_role";

grant select on table "public"."project_members" to "service_role";

grant trigger on table "public"."project_members" to "service_role";

grant truncate on table "public"."project_members" to "service_role";

grant update on table "public"."project_members" to "service_role";

grant delete on table "public"."project_resources" to "anon";

grant insert on table "public"."project_resources" to "anon";

grant references on table "public"."project_resources" to "anon";

grant select on table "public"."project_resources" to "anon";

grant trigger on table "public"."project_resources" to "anon";

grant truncate on table "public"."project_resources" to "anon";

grant update on table "public"."project_resources" to "anon";

grant delete on table "public"."project_resources" to "authenticated";

grant insert on table "public"."project_resources" to "authenticated";

grant references on table "public"."project_resources" to "authenticated";

grant select on table "public"."project_resources" to "authenticated";

grant trigger on table "public"."project_resources" to "authenticated";

grant truncate on table "public"."project_resources" to "authenticated";

grant update on table "public"."project_resources" to "authenticated";

grant delete on table "public"."project_resources" to "service_role";

grant insert on table "public"."project_resources" to "service_role";

grant references on table "public"."project_resources" to "service_role";

grant select on table "public"."project_resources" to "service_role";

grant trigger on table "public"."project_resources" to "service_role";

grant truncate on table "public"."project_resources" to "service_role";

grant update on table "public"."project_resources" to "service_role";

grant delete on table "public"."projects" to "anon";

grant insert on table "public"."projects" to "anon";

grant references on table "public"."projects" to "anon";

grant select on table "public"."projects" to "anon";

grant trigger on table "public"."projects" to "anon";

grant truncate on table "public"."projects" to "anon";

grant update on table "public"."projects" to "anon";

grant delete on table "public"."projects" to "authenticated";

grant insert on table "public"."projects" to "authenticated";

grant references on table "public"."projects" to "authenticated";

grant select on table "public"."projects" to "authenticated";

grant trigger on table "public"."projects" to "authenticated";

grant truncate on table "public"."projects" to "authenticated";

grant update on table "public"."projects" to "authenticated";

grant delete on table "public"."projects" to "service_role";

grant insert on table "public"."projects" to "service_role";

grant references on table "public"."projects" to "service_role";

grant select on table "public"."projects" to "service_role";

grant trigger on table "public"."projects" to "service_role";

grant truncate on table "public"."projects" to "service_role";

grant update on table "public"."projects" to "service_role";

grant delete on table "public"."roles" to "anon";

grant insert on table "public"."roles" to "anon";

grant references on table "public"."roles" to "anon";

grant select on table "public"."roles" to "anon";

grant trigger on table "public"."roles" to "anon";

grant truncate on table "public"."roles" to "anon";

grant update on table "public"."roles" to "anon";

grant delete on table "public"."roles" to "authenticated";

grant insert on table "public"."roles" to "authenticated";

grant references on table "public"."roles" to "authenticated";

grant select on table "public"."roles" to "authenticated";

grant trigger on table "public"."roles" to "authenticated";

grant truncate on table "public"."roles" to "authenticated";

grant update on table "public"."roles" to "authenticated";

grant delete on table "public"."roles" to "service_role";

grant insert on table "public"."roles" to "service_role";

grant references on table "public"."roles" to "service_role";

grant select on table "public"."roles" to "service_role";

grant trigger on table "public"."roles" to "service_role";

grant truncate on table "public"."roles" to "service_role";

grant update on table "public"."roles" to "service_role";

grant delete on table "public"."scratchpads" to "anon";

grant insert on table "public"."scratchpads" to "anon";

grant references on table "public"."scratchpads" to "anon";

grant select on table "public"."scratchpads" to "anon";

grant trigger on table "public"."scratchpads" to "anon";

grant truncate on table "public"."scratchpads" to "anon";

grant update on table "public"."scratchpads" to "anon";

grant delete on table "public"."scratchpads" to "authenticated";

grant insert on table "public"."scratchpads" to "authenticated";

grant references on table "public"."scratchpads" to "authenticated";

grant select on table "public"."scratchpads" to "authenticated";

grant trigger on table "public"."scratchpads" to "authenticated";

grant truncate on table "public"."scratchpads" to "authenticated";

grant update on table "public"."scratchpads" to "authenticated";

grant delete on table "public"."scratchpads" to "service_role";

grant insert on table "public"."scratchpads" to "service_role";

grant references on table "public"."scratchpads" to "service_role";

grant select on table "public"."scratchpads" to "service_role";

grant trigger on table "public"."scratchpads" to "service_role";

grant truncate on table "public"."scratchpads" to "service_role";

grant update on table "public"."scratchpads" to "service_role";

grant delete on table "public"."task_attachments" to "anon";

grant insert on table "public"."task_attachments" to "anon";

grant references on table "public"."task_attachments" to "anon";

grant select on table "public"."task_attachments" to "anon";

grant trigger on table "public"."task_attachments" to "anon";

grant truncate on table "public"."task_attachments" to "anon";

grant update on table "public"."task_attachments" to "anon";

grant delete on table "public"."task_attachments" to "authenticated";

grant insert on table "public"."task_attachments" to "authenticated";

grant references on table "public"."task_attachments" to "authenticated";

grant select on table "public"."task_attachments" to "authenticated";

grant trigger on table "public"."task_attachments" to "authenticated";

grant truncate on table "public"."task_attachments" to "authenticated";

grant update on table "public"."task_attachments" to "authenticated";

grant delete on table "public"."task_attachments" to "service_role";

grant insert on table "public"."task_attachments" to "service_role";

grant references on table "public"."task_attachments" to "service_role";

grant select on table "public"."task_attachments" to "service_role";

grant trigger on table "public"."task_attachments" to "service_role";

grant truncate on table "public"."task_attachments" to "service_role";

grant update on table "public"."task_attachments" to "service_role";

grant delete on table "public"."task_comments" to "anon";

grant insert on table "public"."task_comments" to "anon";

grant references on table "public"."task_comments" to "anon";

grant select on table "public"."task_comments" to "anon";

grant trigger on table "public"."task_comments" to "anon";

grant truncate on table "public"."task_comments" to "anon";

grant update on table "public"."task_comments" to "anon";

grant delete on table "public"."task_comments" to "authenticated";

grant insert on table "public"."task_comments" to "authenticated";

grant references on table "public"."task_comments" to "authenticated";

grant select on table "public"."task_comments" to "authenticated";

grant trigger on table "public"."task_comments" to "authenticated";

grant truncate on table "public"."task_comments" to "authenticated";

grant update on table "public"."task_comments" to "authenticated";

grant delete on table "public"."task_comments" to "service_role";

grant insert on table "public"."task_comments" to "service_role";

grant references on table "public"."task_comments" to "service_role";

grant select on table "public"."task_comments" to "service_role";

grant trigger on table "public"."task_comments" to "service_role";

grant truncate on table "public"."task_comments" to "service_role";

grant update on table "public"."task_comments" to "service_role";

grant delete on table "public"."tasks" to "anon";

grant insert on table "public"."tasks" to "anon";

grant references on table "public"."tasks" to "anon";

grant select on table "public"."tasks" to "anon";

grant trigger on table "public"."tasks" to "anon";

grant truncate on table "public"."tasks" to "anon";

grant update on table "public"."tasks" to "anon";

grant delete on table "public"."tasks" to "authenticated";

grant insert on table "public"."tasks" to "authenticated";

grant references on table "public"."tasks" to "authenticated";

grant select on table "public"."tasks" to "authenticated";

grant trigger on table "public"."tasks" to "authenticated";

grant truncate on table "public"."tasks" to "authenticated";

grant update on table "public"."tasks" to "authenticated";

grant delete on table "public"."tasks" to "service_role";

grant insert on table "public"."tasks" to "service_role";

grant references on table "public"."tasks" to "service_role";

grant select on table "public"."tasks" to "service_role";

grant trigger on table "public"."tasks" to "service_role";

grant truncate on table "public"."tasks" to "service_role";

grant update on table "public"."tasks" to "service_role";

grant delete on table "public"."tasks_history" to "anon";

grant insert on table "public"."tasks_history" to "anon";

grant references on table "public"."tasks_history" to "anon";

grant select on table "public"."tasks_history" to "anon";

grant trigger on table "public"."tasks_history" to "anon";

grant truncate on table "public"."tasks_history" to "anon";

grant update on table "public"."tasks_history" to "anon";

grant delete on table "public"."tasks_history" to "authenticated";

grant insert on table "public"."tasks_history" to "authenticated";

grant references on table "public"."tasks_history" to "authenticated";

grant select on table "public"."tasks_history" to "authenticated";

grant trigger on table "public"."tasks_history" to "authenticated";

grant truncate on table "public"."tasks_history" to "authenticated";

grant update on table "public"."tasks_history" to "authenticated";

grant delete on table "public"."tasks_history" to "service_role";

grant insert on table "public"."tasks_history" to "service_role";

grant references on table "public"."tasks_history" to "service_role";

grant select on table "public"."tasks_history" to "service_role";

grant trigger on table "public"."tasks_history" to "service_role";

grant truncate on table "public"."tasks_history" to "service_role";

grant update on table "public"."tasks_history" to "service_role";

grant delete on table "public"."test_trackers" to "anon";

grant insert on table "public"."test_trackers" to "anon";

grant references on table "public"."test_trackers" to "anon";

grant select on table "public"."test_trackers" to "anon";

grant trigger on table "public"."test_trackers" to "anon";

grant truncate on table "public"."test_trackers" to "anon";

grant update on table "public"."test_trackers" to "anon";

grant delete on table "public"."test_trackers" to "authenticated";

grant insert on table "public"."test_trackers" to "authenticated";

grant references on table "public"."test_trackers" to "authenticated";

grant select on table "public"."test_trackers" to "authenticated";

grant trigger on table "public"."test_trackers" to "authenticated";

grant truncate on table "public"."test_trackers" to "authenticated";

grant update on table "public"."test_trackers" to "authenticated";

grant delete on table "public"."test_trackers" to "service_role";

grant insert on table "public"."test_trackers" to "service_role";

grant references on table "public"."test_trackers" to "service_role";

grant select on table "public"."test_trackers" to "service_role";

grant trigger on table "public"."test_trackers" to "service_role";

grant truncate on table "public"."test_trackers" to "service_role";

grant update on table "public"."test_trackers" to "service_role";

grant delete on table "public"."users" to "anon";

grant insert on table "public"."users" to "anon";

grant references on table "public"."users" to "anon";

grant select on table "public"."users" to "anon";

grant trigger on table "public"."users" to "anon";

grant truncate on table "public"."users" to "anon";

grant update on table "public"."users" to "anon";

grant delete on table "public"."users" to "authenticated";

grant insert on table "public"."users" to "authenticated";

grant references on table "public"."users" to "authenticated";

grant select on table "public"."users" to "authenticated";

grant trigger on table "public"."users" to "authenticated";

grant truncate on table "public"."users" to "authenticated";

grant update on table "public"."users" to "authenticated";

grant delete on table "public"."users" to "service_role";

grant insert on table "public"."users" to "service_role";

grant references on table "public"."users" to "service_role";

grant select on table "public"."users" to "service_role";

grant trigger on table "public"."users" to "service_role";

grant truncate on table "public"."users" to "service_role";

grant update on table "public"."users" to "service_role";


  create policy "bug_attachment_rw"
  on "public"."bug_attachments"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM bugs b
  WHERE ((b.id = bug_attachments.bug_id) AND is_project_member(b.project_id)))));



  create policy "Allow insert of bug_comments"
  on "public"."bug_comments"
  as permissive
  for insert
  to authenticated
with check (true);



  create policy "bug_comment_rw"
  on "public"."bug_comments"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM bugs b
  WHERE ((b.id = bug_comments.bug_id) AND is_project_member(b.project_id)))));



  create policy "Allow authenticated insert"
  on "public"."bugs"
  as permissive
  for insert
  to authenticated
with check (true);



  create policy "bug_select"
  on "public"."bugs"
  as permissive
  for select
  to public
using (is_project_member(project_id));



  create policy "bug_update"
  on "public"."bugs"
  as permissive
  for update
  to public
using ((is_project_member(project_id) AND ((reporter = (auth_uid())::text) OR (assignee = (auth_uid())::text) OR (reporter = auth_username()) OR (assignee = auth_username()) OR has_proj_role(project_id, ARRAY['admin'::text, 'owner'::text]))));



  create policy "oi_admin"
  on "public"."organization_invites"
  as permissive
  for all
  to public
using ((is_org_member(org_id) AND has_org_role(org_id, ARRAY['admin'::text, 'owner'::text])));



  create policy "oi_self"
  on "public"."organization_invites"
  as permissive
  for select
  to public
using ((email = auth_email()));



  create policy "om_admin_select"
  on "public"."organization_members"
  as permissive
  for select
  to public
using (has_org_role(org_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "om_manage"
  on "public"."organization_members"
  as permissive
  for all
  to public
using (has_org_role(org_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "om_self_select"
  on "public"."organization_members"
  as permissive
  for select
  to public
using ((user_id = auth_uid()));



  create policy "org_delete"
  on "public"."organizations"
  as permissive
  for delete
  to public
using (has_org_role(org_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "org_select"
  on "public"."organizations"
  as permissive
  for select
  to public
using (is_org_member(org_id));



  create policy "org_update"
  on "public"."organizations"
  as permissive
  for update
  to public
using (has_org_role(org_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "Allow all inserts"
  on "public"."organizations_history"
  as permissive
  for insert
  to public
with check (true);



  create policy "pm_admin"
  on "public"."project_members"
  as permissive
  for all
  to public
using (has_proj_role(project_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "pm_self"
  on "public"."project_members"
  as permissive
  for select
  to public
using ((user_id = auth_uid()));



  create policy "pr_manage"
  on "public"."project_resources"
  as permissive
  for all
  to public
using ((is_project_member(project_id) AND has_proj_role(project_id, ARRAY['admin'::text, 'owner'::text])));



  create policy "pr_select"
  on "public"."project_resources"
  as permissive
  for select
  to public
using (is_project_member(project_id));



  create policy "proj_manage"
  on "public"."projects"
  as permissive
  for all
  to public
using (has_proj_role(project_id, ARRAY['admin'::text, 'owner'::text]));



  create policy "proj_select"
  on "public"."projects"
  as permissive
  for select
  to public
using (is_org_member(org_id));



  create policy "task_attachment_rw"
  on "public"."task_attachments"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM tasks t
  WHERE ((t.task_id = t.task_id) AND is_project_member(t.project_id)))));



  create policy "task_comment_rw"
  on "public"."task_comments"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM tasks t
  WHERE ((t.task_id = t.task_id) AND is_project_member(t.project_id)))));



  create policy "task_select"
  on "public"."tasks"
  as permissive
  for select
  to public
using (is_project_member(project_id));



  create policy "task_update"
  on "public"."tasks"
  as permissive
  for update
  to public
using ((is_project_member(project_id) AND ((created_by = (auth_uid())::text) OR (assignee = (auth_uid())::text) OR (created_by = auth_username()) OR (assignee = auth_username()) OR has_proj_role(project_id, ARRAY['admin'::text, 'owner'::text]))));


CREATE TRIGGER update_bug_comments_modtime BEFORE UPDATE ON public.bug_comments FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_bugs_modtime BEFORE UPDATE ON public.bugs FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER set_updated_at_designations BEFORE UPDATE ON public.designations FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_organization_members BEFORE UPDATE ON public.organization_members FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_organizations BEFORE UPDATE ON public.organizations FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_project_members BEFORE UPDATE ON public.project_members FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_project_resources BEFORE UPDATE ON public.project_resources FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_projects BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_roles BEFORE UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_task_comments BEFORE UPDATE ON public.task_comments FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_tasks BEFORE UPDATE ON public.tasks FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_tasks_history BEFORE UPDATE ON public.tasks_history FOR EACH ROW EXECUTE FUNCTION set_updated_at();


