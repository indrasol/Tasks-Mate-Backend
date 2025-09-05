alter table "public"."bugs" drop constraint "bugs_project_id_fkey";

alter table "public"."bugs" drop constraint "bugs_tracker_id_fkey";

alter table "public"."test_tracker_tasks" drop constraint "test_tracker_tasks_pkey";

drop index if exists "public"."test_tracker_tasks_pkey";

alter table "public"."test_tracker_tasks" add column "bug_id" text not null;

CREATE UNIQUE INDEX test_tracker_tasks_pkey ON public.test_tracker_tasks USING btree (tracker_id, task_id, bug_id);

alter table "public"."test_tracker_tasks" add constraint "test_tracker_tasks_pkey" PRIMARY KEY using index "test_tracker_tasks_pkey";

alter table "public"."test_tracker_tasks" add constraint "test_tracker_tasks_bug_id_fkey" FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE not valid;

alter table "public"."test_tracker_tasks" validate constraint "test_tracker_tasks_bug_id_fkey";

alter table "public"."bugs" add constraint "bugs_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE not valid;

alter table "public"."bugs" validate constraint "bugs_project_id_fkey";

alter table "public"."bugs" add constraint "bugs_tracker_id_fkey" FOREIGN KEY (tracker_id) REFERENCES test_trackers(tracker_id) ON DELETE CASCADE not valid;

alter table "public"."bugs" validate constraint "bugs_tracker_id_fkey";


