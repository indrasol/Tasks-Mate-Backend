create table "public"."test_tracker_tasks" (
    "tracker_id" text not null,
    "task_id" text not null,
    "created_at" timestamp with time zone default now()
);


CREATE INDEX idx_test_tracker_tasks_task ON public.test_tracker_tasks USING btree (task_id);

CREATE INDEX idx_test_tracker_tasks_tracker ON public.test_tracker_tasks USING btree (tracker_id);

CREATE UNIQUE INDEX test_tracker_tasks_pkey ON public.test_tracker_tasks USING btree (tracker_id, task_id);

alter table "public"."test_tracker_tasks" add constraint "test_tracker_tasks_pkey" PRIMARY KEY using index "test_tracker_tasks_pkey";

alter table "public"."test_tracker_tasks" add constraint "test_tracker_tasks_task_id_fkey" FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE not valid;

alter table "public"."test_tracker_tasks" validate constraint "test_tracker_tasks_task_id_fkey";

alter table "public"."test_tracker_tasks" add constraint "test_tracker_tasks_tracker_id_fkey" FOREIGN KEY (tracker_id) REFERENCES test_trackers(tracker_id) ON DELETE CASCADE not valid;

alter table "public"."test_tracker_tasks" validate constraint "test_tracker_tasks_tracker_id_fkey";

grant delete on table "public"."test_tracker_tasks" to "anon";

grant insert on table "public"."test_tracker_tasks" to "anon";

grant references on table "public"."test_tracker_tasks" to "anon";

grant select on table "public"."test_tracker_tasks" to "anon";

grant trigger on table "public"."test_tracker_tasks" to "anon";

grant truncate on table "public"."test_tracker_tasks" to "anon";

grant update on table "public"."test_tracker_tasks" to "anon";

grant delete on table "public"."test_tracker_tasks" to "authenticated";

grant insert on table "public"."test_tracker_tasks" to "authenticated";

grant references on table "public"."test_tracker_tasks" to "authenticated";

grant select on table "public"."test_tracker_tasks" to "authenticated";

grant trigger on table "public"."test_tracker_tasks" to "authenticated";

grant truncate on table "public"."test_tracker_tasks" to "authenticated";

grant update on table "public"."test_tracker_tasks" to "authenticated";

grant delete on table "public"."test_tracker_tasks" to "service_role";

grant insert on table "public"."test_tracker_tasks" to "service_role";

grant references on table "public"."test_tracker_tasks" to "service_role";

grant select on table "public"."test_tracker_tasks" to "service_role";

grant trigger on table "public"."test_tracker_tasks" to "service_role";

grant truncate on table "public"."test_tracker_tasks" to "service_role";

grant update on table "public"."test_tracker_tasks" to "service_role";


