CREATE OR REPLACE FUNCTION api_user_requests_create(
  p_user_id uuid,
  p_type text,
  p_payload jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE v_row requests%rowtype;
BEGIN
  p_type := btrim(p_type);
  PERFORM api_require(p_type <> '', 400, 'type required');

  IF p_payload IS NULL THEN
    p_payload := '{}'::jsonb;
  END IF;

  INSERT INTO requests(user_id, type, payload)
  VALUES (p_user_id, p_type, p_payload)
  RETURNING * INTO v_row;

  RETURN jsonb_build_object(
    'id', v_row.id,
    'user_id', v_row.user_id,
    'type', v_row.type,
    'payload', v_row.payload,
    'status', v_row.status,
    'admin_comment', v_row.admin_comment,
    'created_at', v_row.created_at::text,
    'updated_at', v_row.updated_at::text
  );
END;
$$;

CREATE OR REPLACE FUNCTION api_user_requests_list(p_user_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN jsonb_build_object('items',
    COALESCE(
      (SELECT jsonb_agg(
         jsonb_build_object(
           'id', r.id,
           'user_id', r.user_id,
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
       WHERE r.user_id = p_user_id),
      '[]'::jsonb
    )
  );
END;
$$;

CREATE OR REPLACE FUNCTION api_user_request_rate(
  p_user_id uuid,
  p_request_id uuid,
  p_rating int,
  p_comment text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE v_row feedback%rowtype;
BEGIN
  PERFORM api_require(p_rating BETWEEN 1 AND 5, 400, 'rating must be 1..5');

  IF NOT EXISTS (SELECT 1 FROM requests WHERE id = p_request_id AND user_id = p_user_id) THEN
    PERFORM api_raise(403, 'forbidden');
  END IF;

  INSERT INTO feedback(request_id, user_id, rating, comment)
  VALUES (p_request_id, p_user_id, p_rating, p_comment)
  RETURNING * INTO v_row;

  RETURN jsonb_build_object(
    'id', v_row.id,
    'request_id', v_row.request_id,
    'user_id', v_row.user_id,
    'rating', v_row.rating,
    'comment', v_row.comment,
    'created_at', v_row.created_at::text
  );
EXCEPTION
  WHEN unique_violation THEN
    PERFORM api_raise(400, 'db error (maybe feedback already exists)');
END;
$$;
