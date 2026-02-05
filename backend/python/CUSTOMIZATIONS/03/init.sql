CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('user', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE request_status AS ENUM ('new', 'in_progress', 'approved', 'rejected', 'done');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  login         TEXT NOT NULL UNIQUE,
  password      TEXT NOT NULL,
  full_name     TEXT NOT NULL,
  phone         TEXT NOT NULL,
  email         TEXT NOT NULL,
  role          user_role NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS requests (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type          TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
  status        request_status NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS feedback (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id  UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rating      INT NOT NULL CHECK (rating BETWEEN 0 AND 5),
  comment     TEXT,
  UNIQUE(request_id, user_id)
);

-- UPSERT
CREATE OR REPLACE FUNCTION create_admin(
    p_login text,
    p_password text,
    p_name text,
    p_phone text,
    p_email text
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO users (login, password, full_name, phone, email, role)
  VALUES (p_login, p_password, p_name, p_phone, p_email, 'admin')
  ON CONFLICT (login) DO NOTHING;

  RETURN FOUND;
END;
$$;

-- Fat DB
CREATE OR REPLACE FUNCTION user_register(
  p_login text,
  p_password text,
  p_full_name text,
  p_phone text,
  p_email text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  u users%ROWTYPE;
BEGIN
  INSERT INTO users (login, password, full_name, phone, email, role)
  VALUES (p_login, p_password, p_full_name, p_phone, p_email, 'user')
  ON CONFLICT (login) DO NOTHING
  RETURNING * INTO u;

  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'ok', false,
      'error', 'login_exists'
    );
  END IF;

  RETURN jsonb_build_object(
    'ok', true,
    'user', jsonb_build_object(
      'id', u.id::text,
      'login', u.login,
      'full_name', u.full_name,
      'phone', u.phone,
      'email', u.email,
      'role', u.role
    )
  );
END;
$$;

-- Fat DB
CREATE OR REPLACE FUNCTION user_login(
  p_login text,
  p_password text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  u users%ROWTYPE;
BEGIN
  SELECT * INTO u FROM users
  WHERE login = p_login AND password = p_password;

  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'ok', false,
      'error', 'invalid_credentials'
    );
  END IF;

  RETURN jsonb_build_object(
    'ok', true,
    'user', jsonb_build_object(
      'id', u.id::text,
      'login', u.login,
      'full_name', u.full_name,
      'role', u.role
    )
  );
END;
$$;

CREATE OR REPLACE FUNCTION user_request_create(
  p_user_id uuid,
  p_type text,
  p_payload jsonb DEFAULT '{}'::jsonb
)
RETURNS jsonb
LANGUAGE sql
AS $$
WITH inp AS (
  SELECT
    $1::uuid AS user_id,
    NULLIF(btrim($2::text), '') AS typ,
    COALESCE($3::jsonb, '{}'::jsonb) AS payload
),
ins AS (
  INSERT INTO requests (user_id, type, payload)
  SELECT user_id, typ, payload
  FROM inp
  WHERE typ IS NOT NULL
  RETURNING *
)
SELECT
  CASE
    WHEN (SELECT typ FROM inp) IS NULL THEN
      jsonb_build_object('ok', false, 'error', 'type required', 'code', 22023)
    ELSE
      jsonb_build_object(
        'ok', true,
        'item', (SELECT jsonb_build_object(
          'id', id::text,
          'user_id', user_id::text,
          'type', type,
          'payload', payload,
          'status', status
        ) FROM ins)
      )
  END;
$$;

CREATE OR REPLACE FUNCTION user_requests_list(p_user_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  items jsonb;
BEGIN
  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'id', id::text,
        'user_id', user_id::text,
        'type', type,
        'payload', payload,
        'status', status
      )
    ),
    '[]'::jsonb
  )
  INTO items
  FROM requests
  WHERE user_id = p_user_id;

  RETURN jsonb_build_object('items', items);
END;
$$;

CREATE OR REPLACE FUNCTION user_request_rate(
  p_request_id uuid,
  p_user_id uuid,
  p_rating int,
  p_comment text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  out jsonb;
  was_update bool;
BEGIN
  IF p_rating < 0 OR p_rating > 5 THEN
    RAISE EXCEPTION 'rating must be 0..5' USING ERRCODE = '22023';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM requests WHERE id=p_request_id AND user_id=p_user_id) THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE = '42501';
  END IF;

  WITH up AS (
    INSERT INTO feedback (request_id, user_id, rating, comment)
    VALUES (p_request_id, p_user_id, p_rating, p_comment)
    ON CONFLICT (request_id, user_id) DO UPDATE
      SET rating = EXCLUDED.rating,
          comment = EXCLUDED.comment
    RETURNING (xmax <> 0) AS updated,
              jsonb_build_object(
                'id', id::text,
                'request_id', request_id::text,
                'user_id', user_id::text,
                'rating', rating,
                'comment', comment
              ) AS j
  )
  SELECT updated, j INTO was_update, out FROM up;

  IF was_update THEN
    RAISE EXCEPTION 'feedback already exists' USING ERRCODE = '23505';
  END IF;

  RETURN out;
END;
$$;

CREATE OR REPLACE FUNCTION admin_requests_list()
RETURNS jsonb
LANGUAGE sql
AS $$
  SELECT jsonb_build_object(
    'items',
    COALESCE(
      jsonb_agg(to_jsonb(x) ORDER BY x.id),
      '[]'::jsonb
    )
  )
  FROM (
    SELECT
      r.id::text       AS id,
      r.user_id::text  AS user_id,
      u.login          AS user_login,
      r.type           AS type,
      r.payload        AS payload,
      r.status::text   AS status
    FROM requests r
    JOIN users u ON u.id = r.user_id
  ) x;
$$;

CREATE OR REPLACE FUNCTION admin_request_set_status(
  p_request_id uuid,
  p_status request_status
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
  v_cnt int;
BEGIN
  UPDATE requests
  SET status = p_status
  WHERE id = p_request_id;

  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt = 0 THEN
    RAISE EXCEPTION 'request not found'
      USING ERRCODE = 'P0002';
  END IF;

  RETURN true;
END;
$$;
