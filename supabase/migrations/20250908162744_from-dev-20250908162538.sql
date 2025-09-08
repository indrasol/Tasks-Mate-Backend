alter table "public"."scratchpads" add constraint "scratchpads_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."scratchpads" validate constraint "scratchpads_org_id_fkey";


