import os
from psycopg_pool import ConnectionPool

DB_DSN = os.getenv("DB_DSN", "")
if not DB_DSN:
    raise RuntimeError("DB_DSN is required")

pool = ConnectionPool(conninfo=DB_DSN, min_size=1, max_size=10, open=True)

