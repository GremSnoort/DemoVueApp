CREATE OR REPLACE FUNCTION api_require_admin(p_user_id uuid)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE v_role user_role;
BEGIN
  SELECT role INTO v_role FROM users WHERE id = p_user_id;
  IF NOT FOUND THEN
    PERFORM api_raise(401, 'unauthorized');
  END IF;

  IF v_role <> 'admin' THEN
    PERFORM api_raise(403, 'forbidden');
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION api_admin_requests_list(p_admin_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM api_require_admin(p_admin_id);

  RETURN jsonb_build_object('items',
    COALESCE(
      (SELECT jsonb_agg(
         jsonb_build_object(
           'id', r.id,
           'user_id', r.user_id,
           'user_login', u.login,
           'type', r.type,
           'payload', r.payload,
           'status', r.status,
           'admin_comment', r.admin_comment,
           'created_at', r.created_at::text,
           'updated_at', r.updated_at::text
         )
         ORDER BY r.created_at DESC
       )
       FROM requests r
       JOIN users u ON u.id = r.user_id),
      '[]'::jsonb
    )
  );
END;
$$;

CREATE OR REPLACE FUNCTION api_admin_request_set_status(
  p_admin_id uuid,
  p_request_id uuid,
  p_status request_status,
  p_admin_comment text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM api_require_admin(p_admin_id);

  UPDATE requests
  SET status = p_status,
      admin_comment = p_admin_comment,
      updated_at = now()
  WHERE id = p_request_id;

  IF NOT FOUND THEN
    PERFORM api_raise(404, 'not found');
  END IF;

  RETURN jsonb_build_object('ok', true);
END;
$$;
