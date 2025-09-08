alter type "public"."designation_enum" rename to "designation_enum__old_version_to_be_dropped";

create type "public"."designation_enum" as enum ('developer', 'designer', 'qa', 'product_manager', 'devops', 'analyst', 'team_lead', 'tester', 'director', 'manager', 'ui_engineer', 'devops_engineer', 'software_engineer', 'senior_software_engineer', 'staff_engineer', 'principal_engineer', 'frontend_engineer', 'backend_engineer', 'full_stack_engineer', 'mobile_engineer', 'qa_engineer', 'product_designer', 'data_analyst', 'data_scientist', 'engineering_manager', 'architect', 'vp_engineering', 'cto', 'site_reliability_engineer', 'cloud_engineer', 'security_engineer', 'data_engineer', 'machine_learning_engineer', 'mlops_engineer', 'database_administrator', 'systems_administrator', 'support_engineer', 'technical_writer', 'project_manager', 'scrum_master', 'release_manager', 'hr_manager', 'recruiter', 'finance_manager', 'accountant', 'operations_manager', 'office_manager', 'marketing_manager', 'sales_manager', 'sales_executive', 'customer_support_specialist', 'business_development_manager', 'legal_counsel', 'procurement_manager', 'founder', 'ceo', 'coo', 'cfo', 'organization_owner');

alter type "public"."designation_name_enum" rename to "designation_name_enum__old_version_to_be_dropped";

create type "public"."designation_name_enum" as enum ('Software Engineer', 'Designer', 'Quality Engineer', 'Product Manager', 'DevOps', 'Analyst', 'Team Lead', 'Software Tester', 'Director', 'Manager', 'UI Engineer', 'Senior Software Engineer', 'Staff Engineer', 'Principal Engineer', 'Frontend Engineer', 'Backend Engineer', 'Full-stack Engineer', 'Mobile Engineer', 'QA Engineer', 'DevOps Engineer', 'Product Designer', 'Data Analyst', 'Data Scientist', 'Engineering Manager', 'Solutions Architect', 'VP, Engineering', 'Chief Technology Officer', 'Site Reliability Engineer', 'Cloud Engineer', 'Security Engineer', 'Data Engineer', 'Machine Learning Engineer', 'MLOps Engineer', 'Database Administrator', 'Systems Administrator', 'Support Engineer', 'Technical Writer', 'Project Manager', 'Scrum Master', 'Release Manager', 'HR Manager', 'Recruiter', 'Finance Manager', 'Accountant', 'Operations Manager', 'Office Manager', 'Marketing Manager', 'Sales Manager', 'Sales Executive', 'Customer Support Specialist', 'Business Development Manager', 'Legal Counsel', 'Procurement Manager', 'Founder', 'Chief Executive Officer', 'Chief Operating Officer', 'Chief Financial Officer', 'Organization Owner');

alter table "public"."designations" alter column slug type "public"."designation_enum" using slug::text::"public"."designation_enum";

alter table "public"."organization_invites" alter column designation type "public"."designation_enum" using designation::text::"public"."designation_enum";

alter table "public"."organization_members" alter column designation type "public"."designation_enum" using designation::text::"public"."designation_enum";

alter table "public"."project_members" alter column designation type "public"."designation_enum" using designation::text::"public"."designation_enum";

drop type "public"."designation_enum__old_version_to_be_dropped";

drop type "public"."designation_name_enum__old_version_to_be_dropped";

alter table "public"."designations" alter column "name" drop not null;

alter table "public"."designations" alter column "name" set data type designation_name_enum using "name"::text::designation_name_enum;


