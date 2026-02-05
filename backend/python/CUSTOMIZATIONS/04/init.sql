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

CREATE OR REPLACE FUNCTION raise_exception(code text, msg text)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION USING ERRCODE = code, MESSAGE = msg;
END;
$$;

-- clear SQL-function
CREATE OR REPLACE FUNCTION create_admin(
    p_login text,
    p_password text,
    p_name text,
    p_phone text,
    p_email text
)
RETURNS boolean
LANGUAGE sql
AS $$
    SELECT EXISTS (
        INSERT INTO users (login, password, full_name, phone, email, role)
        VALUES ($1, $2, $3, $4, $5, 'admin')
        ON CONFLICT (login) DO NOTHING
        RETURNING 1
    );
$$;

-- SQL raise_exception helper
CREATE OR REPLACE FUNCTION user_register(
  p_login text,
  p_password text,
  p_full_name text,
  p_phone text,
  p_email text
)
RETURNS jsonb
LANGUAGE sql
AS $$
WITH ins AS (
  INSERT INTO users (login, password, full_name, phone, email, role)
  VALUES ($1, $2, $3, $4, $5, 'user')
  ON CONFLICT (login) DO NOTHING
  RETURNING *
)
SELECT
  CASE
    WHEN EXISTS (SELECT 1 FROM ins) THEN
      jsonb_build_object(
        'id', id::text,
        'login', login,
        'full_name', full_name,
        'phone', phone,
        'email', email,
        'role', role
      )
    ELSE
      raise_exception('23505', 'login already exists')
  END
FROM ins;
$$;

-- SQL raise_exception helper
CREATE OR REPLACE FUNCTION user_login(
  p_login text,
  p_password text
)
RETURNS jsonb
LANGUAGE sql
AS $$
WITH u AS (
  SELECT id, login, full_name, role
  FROM users
  WHERE login = $1 AND password = $2
)
SELECT
  COALESCE(
    (SELECT jsonb_build_object(
      'id', id::text,
      'login', login,
      'full_name', full_name,
      'role', role
    ) FROM u),
    raise_exception('28P01', 'invalid login or password')
  );
$$;

CREATE OR REPLACE FUNCTION user_request_create(
  p_user_id uuid,
  p_type text,
  p_payload jsonb DEFAULT '{}'::jsonb
)
RETURNS jsonb
LANGUAGE sql
AS $$
WITH checked AS (
  SELECT
    $1::uuid AS user_id,
    NULLIF(btrim($2::text), '') AS typ,
    COALESCE($3::jsonb, '{}'::jsonb) AS payload
),
ins AS (
  INSERT INTO requests (user_id, type, payload)
  SELECT
    user_id,
    COALESCE(typ, (raise_exception('22023','type required')->>0)::text),
    payload
  FROM checked
  RETURNING *
)
SELECT jsonb_build_object(
  'id', id::text,
  'user_id', user_id::text,
  'type', type,
  'payload', payload,
  'status', status
)
FROM ins;
$$;

CREATE OR REPLACE FUNCTION user_requests_list(p_user_id uuid)
RETURNS jsonb
LANGUAGE sql
AS $$
  SELECT jsonb_build_object(
    'items',
    COALESCE(
      (
        SELECT jsonb_agg(
          to_jsonb(x) - 'password'
          ORDER BY x.created_at DESC
        )
        FROM (
          SELECT
            id::text AS id,
            user_id::text AS user_id,
            type,
            payload,
            status,
            created_at
          FROM requests
          WHERE user_id = p_user_id
        ) x
      ),
      '[]'::jsonb
    )
  );
$$;

CREATE OR REPLACE FUNCTION _user_request_rate_try(
  p_request_id uuid,
  p_user_id uuid,
  p_rating int,
  p_comment text
)
RETURNS jsonb
LANGUAGE sql
AS $$
  INSERT INTO feedback (request_id, user_id, rating, comment)
  VALUES ($1, $2, $3, $4)
  ON CONFLICT (request_id, user_id) DO NOTHING
  RETURNING jsonb_build_object(
    'id', id::text,
    'request_id', request_id::text,
    'user_id', user_id::text,
    'rating', rating,
    'comment', comment
  );
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
BEGIN
  IF p_rating < 0 OR p_rating > 5 THEN
    RAISE EXCEPTION 'rating must be 0..5' USING ERRCODE = '22023';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM requests WHERE id=p_request_id AND user_id=p_user_id) THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE = '42501';
  END IF;

  out := _user_request_rate_try(p_request_id, p_user_id, p_rating, p_comment);

  IF out IS NULL THEN
    RAISE EXCEPTION 'feedback already exists' USING ERRCODE = '23505';
  END IF;

  RETURN out;
END;
$$;

CREATE OR REPLACE FUNCTION admin_requests_list()
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  out jsonb;
BEGIN
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
  INTO out
  FROM requests r
  JOIN users u ON u.id = r.user_id;

  RETURN out;
END;
$$;

CREATE OR REPLACE FUNCTION admin_request_set_status(
  p_request_id uuid,
  p_status request_status
)
RETURNS boolean
LANGUAGE sql
AS $$
  WITH upd AS (
    UPDATE requests
    SET status = $2
    WHERE id = $1
    RETURNING 1
  )
  SELECT
    CASE
      WHEN EXISTS (SELECT 1 FROM upd) THEN true
      ELSE (SELECT raise_exception('P0002', 'request not found'))::boolean
    END;
$$;
