-- View: public.view_permissions

CREATE OR REPLACE VIEW public.view_permissions
  AS
  SELECT
    auth_group.name AS group_name,
    ct.model AS model_name,
    split_part(permission.codename, concat(ct.model, '_'), 2) AS field_name,
    split_part(permission.codename, '_', 1) AS permission_type,
    permission.codename
  FROM public.auth_group auth_group
    JOIN public.auth_group_permissions group_permission ON auth_group.id = group_permission.group_id
    JOIN public.auth_permission permission ON group_permission.permission_id = permission.id
    JOIN public.django_content_type ct ON permission.content_type_id = ct.id
  ORDER BY auth_group.name, ct.model, permission.codename
;
