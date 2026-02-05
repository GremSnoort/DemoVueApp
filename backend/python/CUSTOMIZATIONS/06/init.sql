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

-- CTE (SQL)
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
    WITH ins AS (
        INSERT INTO users (login, password, full_name, phone, email, role)
        VALUES ($1, $2, $3, $4, $5, 'admin')
        ON CONFLICT DO NOTHING
        RETURNING 1
    )
    SELECT EXISTS (SELECT 1 FROM ins);
$$;

-- NULL
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
    INSERT INTO users (login, password, full_name, phone, email, role)
    VALUES ($1, $2, $3, $4, $5, 'user')
    ON CONFLICT (login) DO NOTHING
    RETURNING jsonb_build_object(
        'id', id::text,
        'login', login,
        'full_name', full_name,
        'phone', phone,
        'email', email,
        'role', role
    );
$$;

-- NULL
CREATE OR REPLACE FUNCTION user_login(
  p_login text,
  p_password text
)
RETURNS jsonb
LANGUAGE sql
AS $$
    SELECT jsonb_build_object(
        'id', u.id::text,
        'login', u.login,
        'full_name', u.full_name,
        'role', u.role
    )
    FROM users u
    WHERE u.login = $1
    AND u.password = $2;
$$;

CREATE OR REPLACE FUNCTION user_request_create(
  p_user_id uuid,
  p_type text,
  p_payload jsonb DEFAULT '{}'::jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  IF p_type IS NULL OR btrim(p_type) = '' THEN
    RAISE EXCEPTION 'type required'
      USING ERRCODE = '22023';
  END IF;

  RETURN (
    INSERT INTO requests (user_id, type, payload)
    VALUES (p_user_id, btrim(p_type), COALESCE(p_payload, '{}'::jsonb))
    RETURNING jsonb_build_object(
      'id', id::text,
      'user_id', user_id::text,
      'type', type,
      'payload', payload,
      'status', status
    )
  );
END;
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
          jsonb_build_object(
            'id', r.id::text,
            'user_id', r.user_id::text,
            'type', r.type,
            'payload', r.payload,
            'status', r.status
          )
          ORDER BY r.created_at DESC
        )
        FROM requests r
        WHERE r.user_id = p_user_id
      ),
      '[]'::jsonb
    )
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

  INSERT INTO feedback (request_id, user_id, rating, comment)
  VALUES (p_request_id, p_user_id, p_rating, p_comment)
  ON CONFLICT (request_id, user_id) DO NOTHING
  RETURNING jsonb_build_object(
    'id', id::text,
    'request_id', request_id::text,
    'user_id', user_id::text,
    'rating', rating,
    'comment', comment
  )
  INTO out;

  IF NOT FOUND THEN
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
    COALESCE(jsonb_agg(j), '[]'::jsonb)
  )
  FROM (
    SELECT jsonb_build_object(
      'id', r.id::text,
      'user_id', r.user_id::text,
      'user_login', u.login,
      'type', r.type,
      'payload', r.payload,
      'status', r.status::text
    ) AS j
    FROM requests r
    JOIN users u ON u.id = r.user_id
    ORDER BY r.id
  ) s;
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
      ELSE
        (SELECT
           (RAISE EXCEPTION 'request not found' USING ERRCODE = 'P0002')::boolean
        )
    END;
$$;
