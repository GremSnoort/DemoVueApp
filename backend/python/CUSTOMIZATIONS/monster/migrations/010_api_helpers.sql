CREATE OR REPLACE FUNCTION api_raise(p_http int, p_msg text)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION '%', json_build_object('error', p_msg)
    USING ERRCODE = 'P0001',  -- custom error
          HINT = p_http::text;
END;
$$;

CREATE OR REPLACE FUNCTION api_require(p_ok boolean, p_http int, p_msg text)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT p_ok THEN
    PERFORM api_raise(p_http, p_msg);
  END IF;
END;
$$;
