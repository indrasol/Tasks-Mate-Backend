alter table "public"."users" add column "test_dummy" text;

create policy "org_insert"
on "public"."organizations"
as permissive
for insert
to anon, authenticated, service_role
with check (true);


