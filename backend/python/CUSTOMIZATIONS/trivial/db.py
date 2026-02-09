from pathlib import Path
from typing import Callable

import psycopg
from psycopg_pool import ConnectionPool


# DB_URL = "<PROTO>://<LOGIN>:<PASSWORD>@<HOST_IPV4>:5432/<DBNAME>?sslmode=disable" # Template
DB_URL = "postgres://app:app@localhost:5432/app?sslmode=disable" # Linux
# DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" # Windows


pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10, open=True)


def execute_on_conn(callback: Callable[[psycopg.Cursor], None]) -> None:
    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                callback(cur)


def apply_schema(schema_dir: str = "./") -> None:
    p = Path(schema_dir)
    if not p.exists() or not p.is_dir():
        raise RuntimeError(f"dir not found: {schema_dir}")

    for file in sorted(p.glob("*.sql")):
        sql = file.read_text(encoding="utf-8")
        execute_on_conn(lambda cur, sql=sql: cur.execute(sql))
