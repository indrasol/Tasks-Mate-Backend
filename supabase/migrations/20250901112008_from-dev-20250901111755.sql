set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.get_auth_user(p_user_id uuid DEFAULT NULL::uuid, p_username text DEFAULT NULL::text)
 RETURNS TABLE(id uuid, email text, username text)
 LANGUAGE sql
 SECURITY DEFINER
AS $function$
    select 
        u.id,
        u.email,
        u.raw_user_meta_data ->> 'username' as username
    from auth.users u
    where 
        (p_user_id is not null and u.id = p_user_id)
        or
        (p_username is not null and u.raw_user_meta_data ->> 'username' = p_username)
    limit 1;
$function$
;


