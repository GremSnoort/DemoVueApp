CREATE OR REPLACE FUNCTION api_user_register(
  p_login text,
  p_password text,
  p_full_name text,
  p_phone text,
  p_email text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE v_row users%rowtype;
BEGIN
  p_login := btrim(p_login);
  p_full_name := btrim(p_full_name);
  p_phone := btrim(p_phone);
  p_email := btrim(p_email);

  PERFORM api_require(p_login ~ '^[A-Za-z0-9]{6,}$', 400, 'login must be latin letters/digits, min 6');
  PERFORM api_require(length(p_password) > 0, 400, 'password required');
  PERFORM api_require(p_full_name ~ '^[А-Яа-яЁё ]+$', 400, 'full_name must be cyrillic letters and spaces');
  PERFORM api_require(p_phone ~ '^8\(\d{3}\)\d{3}-\d{2}-\d{2}$', 400, 'phone must match 8(XXX)XXX-XX-XX');
  PERFORM api_require(p_email ~ '^[^\s@]+@[^\s@]+\.[^\s@]+$', 400, 'invalid email');

  IF EXISTS (SELECT 1 FROM users WHERE login = p_login) THEN
    PERFORM api_raise(409, 'login already exists');
  END IF;

  INSERT INTO users(login, password_hash, full_name, phone, email, role)
  VALUES (p_login, p_password, p_full_name, p_phone, p_email, 'user')
  RETURNING * INTO v_row;

  RETURN jsonb_build_object(
    'id', v_row.id,
    'login', v_row.login,
    'full_name', v_row.full_name,
    'phone', v_row.phone,
    'email', v_row.email,
    'role', v_row.role
  );
END;
$$;

CREATE OR REPLACE FUNCTION api_user_login(
  p_login text,
  p_password text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE v_row users%rowtype;
BEGIN
  p_login := btrim(p_login);
  PERFORM api_require(p_login <> '', 400, 'login and password required');

  SELECT * INTO v_row FROM users WHERE login = p_login AND password_hash = p_password;
  IF NOT FOUND THEN
    PERFORM api_raise(401, 'invalid login or password');
  END IF;

  RETURN jsonb_build_object(
    'id', v_row.id,
    'login', v_row.login,
    'full_name', v_row.full_name,
    'role', v_row.role
  );
END;
$$;

CREATE OR REPLACE FUNCTION api_seed_admin(p_login text, p_password text)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM users WHERE login = p_login) THEN
    RETURN;
  END IF;

  INSERT INTO users(login, password_hash, full_name, phone, email, role)
  VALUES (p_login, p_password, 'Administrator', '8(000)000-00-00', 'admin@gmail.com', 'admin');
END;
$$;
