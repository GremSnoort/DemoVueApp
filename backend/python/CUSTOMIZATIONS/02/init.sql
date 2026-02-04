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

CREATE OR REPLACE FUNCTION create_admin(p_login text, p_password text, p_name text, p_phone text, p_email text)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM users WHERE login = p_login) THEN
    RETURN false;
  END IF;

  INSERT INTO users (login, password, full_name, phone, email, role)
  VALUES (
    p_login,
    p_password,
    p_name,
    p_phone,
    p_email,
    'admin'
  );

  RETURN true;
END;
$$;

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
    RAISE EXCEPTION 'login already exists'
      USING ERRCODE = '23505'; -- unique_violation
  END IF;

  RETURN jsonb_build_object(
    'id', u.id::text,
    'login', u.login,
    'full_name', u.full_name,
    'phone', u.phone,
    'email', u.email,
    'role', u.role
  );
END;
$$;

CREATE OR REPLACE FUNCTION user_login(
  p_login text,
  p_password text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  out jsonb;
BEGIN
  SELECT jsonb_build_object(
    'id', u.id::text,
    'login', u.login,
    'full_name', u.full_name,
    'role', u.role
  )
  INTO out
  FROM users u
  WHERE u.login = p_login
    AND u.password = p_password;

  IF out IS NULL THEN
    RAISE EXCEPTION 'invalid login or password'
      USING ERRCODE = '28P01';
  END IF;

  RETURN out;
END;
$$;

CREATE OR REPLACE FUNCTION user_request_create(
  p_user_id uuid,
  p_type text,
  p_payload jsonb DEFAULT '{}'::jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  out jsonb;
BEGIN
  IF p_type IS NULL OR btrim(p_type) = '' THEN
    RAISE EXCEPTION 'type required' USING ERRCODE = '22023'; -- invalid_parameter_value
  END IF;

  INSERT INTO requests (user_id, type, payload)
  VALUES (p_user_id, btrim(p_type), COALESCE(p_payload, '{}'::jsonb))
  RETURNING jsonb_build_object(
    'id', id::text,
    'user_id', user_id::text,
    'type', type,
    'payload', payload,
    'status', status
  )
  INTO out;

  RETURN out;
END;
$$;

CREATE OR REPLACE FUNCTION user_requests_list(p_user_id uuid)
RETURNS jsonb
LANGUAGE sql
AS $$
  SELECT jsonb_build_object(
    'items',
    COALESCE(
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
  )
  FROM requests
  WHERE user_id = p_user_id;
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
  v_row record;
BEGIN
  -- rating validation
  IF p_rating < 0 OR p_rating > 5 THEN
    RAISE EXCEPTION 'rating must be 0..5' USING ERRCODE = '22023';
  END IF;

  -- ownership check
  IF NOT EXISTS (
    SELECT 1 FROM requests
    WHERE id = p_request_id AND user_id = p_user_id
  ) THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE = '42501';
  END IF;

  -- insert feedback
  BEGIN
    INSERT INTO feedback (request_id, user_id, rating, comment)
    VALUES (p_request_id, p_user_id, p_rating, p_comment)
    RETURNING id, request_id, user_id, rating, comment
    INTO v_row;
  EXCEPTION
    WHEN unique_violation THEN
      RAISE EXCEPTION 'feedback already exists' USING ERRCODE = '23505';
    WHEN others THEN
      RAISE EXCEPTION 'db error' USING ERRCODE = 'XX000';
  END;

  RETURN jsonb_build_object(
    'id', v_row.id::text,
    'request_id', v_row.request_id::text,
    'user_id', v_row.user_id::text,
    'rating', v_row.rating,
    'comment', v_row.comment
  );
END;
$$;

CREATE OR REPLACE FUNCTION admin_requests_list()
RETURNS jsonb
LANGUAGE sql
AS $$
  SELECT jsonb_build_object(
    'items',
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', r.id::text,
          'user_id', r.user_id::text,
          'user_login', u.login,
          'type', r.type,
          'payload', r.payload,
          'status', r.status::text
        )
        ORDER BY r.id
      ),
      '[]'::jsonb
    )
  )
  FROM requests r
  JOIN users u ON u.id = r.user_id;
$$;

CREATE OR REPLACE FUNCTION admin_request_set_status(
    p_request_id uuid,
    p_status request_status
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE requests
    SET status = p_status
    WHERE id = p_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'request not found'
        USING ERRCODE = 'P0002'; -- no_data_found
    END IF;

    RETURN true;
END;
$$;
