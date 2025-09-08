create type "public"."designation_name_enum" as enum ('Software Engineer', 'Designer', 'Quality Engineer', 'Product Manager', 'DevOps', 'Analyst', 'Team Lead', 'Software Tester', 'Director', 'Manager', 'UI Engineer');

alter table "public"."designations" add column "slug" designation_enum;

CREATE UNIQUE INDEX designations_slug_unique ON public.designations USING btree (slug);


