import json
import psycopg
from pathlib import Path
from typing import Callable
from fastapi import HTTPException
from psycopg_pool import ConnectionPool


# DB_URL = "<PROTO>://<LOGIN>:<PASSWORD>@<HOST_IPV4>:5432/<DBNAME>?sslmode=disable" # Template
DB_URL = "postgres://ubuntu:postgres@localhost:5432/postgres?sslmode=disable" # Linux
# DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" # Windows


pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10, open=True)


def _get_attr(obj, *names, default=None):
    for n in names:
        if obj is None:
            return default
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
    return default

def db_call_json(fn_sql: str, params: tuple):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {fn_sql}", params)
                row = cur.fetchone()
            try:
                conn.commit()
            except Exception:
                pass
        return None if row is None else row[0]

    except Exception as e:
        sqlstate = _get_attr(e, "sqlstate", "pgcode", default=None)
        diag = _get_attr(e, "diag", default=None)

        msg_primary = _get_attr(diag, "message_primary", default=None)
        msg_detail  = _get_attr(diag, "message_detail", default=None)
        msg_hint    = _get_attr(diag, "message_hint", default=None)

        raw_msg = msg_primary or str(e)

        if sqlstate == "P0001":
            http = 400
            if isinstance(msg_hint, str) and msg_hint.isdigit():
                http = int(msg_hint)

            try:
                detail = json.loads(raw_msg) if raw_msg else {"error": "db error"}
                if not isinstance(detail, dict):
                    detail = {"error": str(detail)}
            except Exception:
                detail = {"error": raw_msg or "db error"}

            raise HTTPException(status_code=http, detail=detail)

        # 23505 unique_violation
        if sqlstate == "23505":
            raise HTTPException(status_code=409, detail={"error": "conflict"})

        # 23503 foreign_key_violation
        if sqlstate == "23503":
            raise HTTPException(status_code=400, detail={"error": "invalid reference"})

        # 22023 invalid_parameter_value
        if sqlstate == "22023":
            raise HTTPException(status_code=400, detail={"error": "invalid parameter"})

        # --- fallback ---
        raise HTTPException(status_code=400, detail={"error": raw_msg})


def db_run(callback: Callable[[psycopg.Cursor], None]) -> None:
    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                callback(cur)


def apply_sql(schema_dir: str = "./migrations") -> None:
    p = Path(schema_dir)
    if not p.exists() or not p.is_dir():
        raise RuntimeError(f"dir not found: {schema_dir}")

    for file in sorted(p.glob("*.sql")):
        sql = file.read_text(encoding="utf-8")
        db_run(lambda cur, sql=sql: cur.execute(sql))
